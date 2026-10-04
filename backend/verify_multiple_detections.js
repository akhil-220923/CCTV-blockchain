const fs = require("fs");
const crypto = require("crypto");
const grpc = require("@grpc/grpc-js");
const { connect, signers, hash } = require("@hyperledger/fabric-gateway");
const path = require("path");

const CHANNEL_NAME = "mychannel";
const CHAINCODE_NAME = "cctv";

const FABRIC_ROOT =
    (process.env.TEST_NETWORK || path.resolve(__dirname, '../../fabric-samples/test-network'));

const CERT_PATH =
    `${FABRIC_ROOT}/organizations/peerOrganizations/org1.example.com/users/User1@org1.example.com/msp/signcerts/cert.pem`;

const KEY_DIR =
    `${FABRIC_ROOT}/organizations/peerOrganizations/org1.example.com/users/User1@org1.example.com/msp/keystore`;

const TLS_CERT_PATH =
    `${FABRIC_ROOT}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt`;

const PEER_ENDPOINT = "localhost:7051";
const PEER_HOST_ALIAS = "peer0.org1.example.com";

const EVIDENCE_DIR =
    path.resolve(__dirname, "../security/test_frames/detected";

const CAMERA_PUBLIC_KEY =
    path.resolve(__dirname, "../security/camera_001_public_key.pem";


/* =========================================================
   FILE UTILITIES
   ========================================================= */

function readFile(filePath) {
    return fs.readFileSync(filePath);
}


function sha256File(filePath) {

    const data = readFile(filePath);

    return crypto
        .createHash("sha256")
        .update(data)
        .digest("hex");
}


/* =========================================================
   FIND FABRIC PRIVATE KEY
   ========================================================= */

function findPrivateKey() {

    const files = fs.readdirSync(KEY_DIR);

    const keyFile = files.find(file =>
        file.endsWith("_sk")
    );

    if (!keyFile) {
        throw new Error("Fabric private key not found.");
    }

    return path.join(KEY_DIR, keyFile);
}


/* =========================================================
   VERIFY ED25519 SIGNATURE
   ========================================================= */

function verifyEd25519(filePath, signatureHex) {

    const data = readFile(filePath);

    /*
     * The camera originally signed the SHA-256
     * digest of the evidence.
     */
    const digest = crypto
        .createHash("sha256")
        .update(data)
        .digest();

    const publicKey = fs.readFileSync(
        CAMERA_PUBLIC_KEY
    );

    const signature =
        Buffer.from(signatureHex, "hex");

    return crypto.verify(
        null,
        digest,
        {
            key: publicKey,
            format: "pem",
            type: "spki"
        },
        signature
    );
}


/* =========================================================
   PARSE FABRIC RESPONSE
   ========================================================= */
function parseFabricResponse(result) {

    /*
     * Fabric Gateway may return the chaincode
     * response as a Buffer or as a Uint8Array.
     */

    let raw;

    if (Buffer.isBuffer(result)) {

        raw = result.toString("utf8");

    } else if (result instanceof Uint8Array) {

        raw = Buffer.from(result).toString("utf8");

    } else if (Array.isArray(result)) {

        raw = Buffer.from(result).toString("utf8");

    } else {

        raw = String(result);
    }

    raw = raw.trim();

    console.log("  Fabric response decoded successfully.");

    try {

        return JSON.parse(raw);

    } catch (error) {

        throw new Error(
            `Decoded Fabric response is not valid JSON: ${raw}`
        );
    }
}


/* =========================================================
   MAIN
   ========================================================= */

async function main() {

    console.log("=== MULTI-FRAME EVIDENCE VERIFICATION ===");
    console.log();

    /*
     * Load Fabric identity.
     */

    const credentials =
        readFile(CERT_PATH);

    const privateKeyPath =
        findPrivateKey();

    const privateKeyPem =
        readFile(privateKeyPath);

    const identity = {
        mspId: "Org1MSP",
        credentials
    };

    const signer =
        signers.newPrivateKeySigner(
            crypto.createPrivateKey(privateKeyPem)
        );

    /*
     * TLS connection.
     */

    const tlsRootCert =
        readFile(TLS_CERT_PATH);

    const grpcClient =
        new grpc.Client(
            PEER_ENDPOINT,
            grpc.credentials.createSsl(
                tlsRootCert
            ),
            {
                "grpc.ssl_target_name_override":
                    PEER_HOST_ALIAS
            }
        );

    /*
     * Connect to Fabric Gateway.
     */

    const gateway =
        connect({
            client: grpcClient,
            identity,
            signer,
            hash: hash.sha256
        });

    const network =
        gateway.getNetwork(CHANNEL_NAME);

    const contract =
        network.getContract(CHAINCODE_NAME);


    let validCount = 0;
    let invalidCount = 0;


    /* =====================================================
       VERIFY DET-008 TO DET-014
       ===================================================== */

    for (let i = 0; i < 7; i++) {

        const detectionID =
            `DET-${String(i + 8).padStart(3, "0")}`;

        const evidenceFile =
            path.join(
                EVIDENCE_DIR,
                `detected_${String(i).padStart(3, "0")}.jpg`
            );


        console.log(`Checking ${detectionID}...`);

        try {

            /*
             * Check that evidence file exists.
             */

            if (!fs.existsSync(evidenceFile)) {

                throw new Error(
                    `Evidence file not found: ${evidenceFile}`
                );
            }


            /* =============================================
               STEP 1 — READ DETECTION FROM BLOCKCHAIN
               ============================================= */

            const result =
                await contract.evaluateTransaction(
                    "ReadDetection",
                    detectionID
                );


            /*
             * Convert Fabric response into JSON object.
             */

            const detection =
                parseFabricResponse(result);


            console.log(
                `  Object   : ${detection.objectType}`
            );

            console.log(
                `  Confidence: ${detection.confidence}`
            );


            /* =============================================
               STEP 2 — CALCULATE CURRENT FILE HASH
               ============================================= */

            const currentHash =
                sha256File(evidenceFile);


            console.log(
                `  Stored hash : ${detection.frameHash}`
            );

            console.log(
                `  Current hash: ${currentHash}`
            );


            /* =============================================
               STEP 3 — COMPARE HASH
               ============================================= */

            const hashMatch =
                currentHash.toLowerCase() ===
                detection.frameHash.toLowerCase();


            /* =============================================
               STEP 4 — VERIFY DIGITAL SIGNATURE
               ============================================= */

            const signatureValid =
                verifyEd25519(
                    evidenceFile,
                    detection.signature
                );


            console.log(
                `  Hash     : ${
                    hashMatch
                        ? "VALID ✓"
                        : "INVALID ✗"
                }`
            );

            console.log(
                `  Signature: ${
                    signatureValid
                        ? "VALID ✓"
                        : "INVALID ✗"
                }`
            );


            /* =============================================
               FINAL RESULT
               ============================================= */

            if (
                hashMatch &&
                signatureValid
            ) {

                console.log(
                    "  RESULT   : VERIFIED ✓"
                );

                validCount++;

            } else {

                console.log(
                    "  RESULT   : VERIFICATION FAILED ✗"
                );

                invalidCount++;
            }

        } catch (error) {

            console.log(
                "  ERROR:",
                error.message
            );

            invalidCount++;
        }

        console.log();
    }


    /* =====================================================
       SUMMARY
       ===================================================== */

    console.log(
        "======================================"
    );

    console.log(
        "VERIFICATION SUMMARY"
    );

    console.log(
        "======================================"
    );

    console.log(
        `Valid events   : ${validCount}`
    );

    console.log(
        `Invalid events : ${invalidCount}`
    );


    if (invalidCount === 0) {

        console.log();
        console.log(
            "ALL EVIDENCE VERIFIED ✓"
        );

    } else {

        console.log();
        console.log(
            "WARNING: SOME EVIDENCE FAILED VERIFICATION ✗"
        );
    }


    /*
     * Close connections.
     */

    gateway.close();
    grpcClient.close();
}


/* =========================================================
   START
   ========================================================= */

main().catch(error => {

    console.error(error);

    process.exit(1);
});
