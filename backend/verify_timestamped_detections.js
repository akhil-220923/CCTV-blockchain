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


// =========================================================
// TIMESTAMPED EVIDENCE DIRECTORY
// =========================================================

const EVIDENCE_DIR =
    path.resolve(__dirname, "../security/test_frames/timestamped_detected";


// =========================================================
// CAMERA PUBLIC KEY
// =========================================================

const CAMERA_PUBLIC_KEY =
    path.resolve(__dirname, "../security/camera_001_public_key.pem";


// =========================================================
// FILE UTILITIES
// =========================================================

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


// =========================================================
// FIND FABRIC PRIVATE KEY
// =========================================================

function findPrivateKey() {

    const files =
        fs.readdirSync(KEY_DIR);

    const keyFile =
        files.find(file =>
            file.endsWith("_sk")
        );

    if (!keyFile) {

        throw new Error(
            "Fabric private key not found."
        );
    }

    return path.join(
        KEY_DIR,
        keyFile
    );
}


// =========================================================
// VERIFY ED25519 SIGNATURE
// =========================================================

function verifyEd25519(
    filePath,
    signatureHex
) {

    const data =
        readFile(filePath);

    /*
     * The camera signs the SHA-256
     * digest of the evidence.
     */

    const digest =
        crypto
            .createHash("sha256")
            .update(data)
            .digest();


    const publicKey =
        fs.readFileSync(
            CAMERA_PUBLIC_KEY
        );


    const signature =
        Buffer.from(
            signatureHex,
            "hex"
        );


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


// =========================================================
// PARSE FABRIC RESPONSE
// =========================================================

function parseFabricResponse(result) {

    let raw;


    if (Buffer.isBuffer(result)) {

        raw =
            result.toString("utf8");

    } else if (
        result instanceof Uint8Array
    ) {

        raw =
            Buffer
                .from(result)
                .toString("utf8");

    } else if (
        Array.isArray(result)
    ) {

        raw =
            Buffer
                .from(result)
                .toString("utf8");

    } else {

        raw =
            String(result);
    }


    raw =
        raw.trim();


    try {

        return JSON.parse(raw);

    } catch (error) {

        throw new Error(
            `Fabric response is not valid JSON: ${raw}`
        );
    }
}


// =========================================================
// MAIN
// =========================================================

async function main() {

    console.log(
        "================================================"
    );

    console.log(
        " TIMESTAMPED EVIDENCE VERIFICATION"
    );

    console.log(
        " Fabric DET-015 to DET-021"
    );

    console.log(
        "================================================"
    );

    console.log();


    // -----------------------------------------------------
    // FABRIC IDENTITY
    // -----------------------------------------------------

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
            crypto.createPrivateKey(
                privateKeyPem
            )
        );


    // -----------------------------------------------------
    // TLS
    // -----------------------------------------------------

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


    // -----------------------------------------------------
    // CONNECT TO FABRIC
    // -----------------------------------------------------

    const gateway =
        connect({

            client: grpcClient,

            identity,

            signer,

            hash: hash.sha256
        });


    try {

        const network =
            gateway.getNetwork(
                CHANNEL_NAME
            );


        const contract =
            network.getContract(
                CHAINCODE_NAME
            );


        let validCount = 0;

        let invalidCount = 0;


        // =================================================
        // VERIFY DET-015 TO DET-021
        // =================================================

        for (
            let i = 0;
            i < 7;
            i++
        ) {

            const detectionID =
                `DET-${String(i + 15).padStart(3, "0")}`;


            const frameNumber =
                i * 49;


            const evidenceFile =
                path.join(

                    EVIDENCE_DIR,

                    `detected_${String(i).padStart(3, "0")}.jpg`
                );


            console.log(
                "-----------------------------------------------"
            );


            console.log(
                `Checking ${detectionID}`
            );


            console.log(
                `Evidence: ${evidenceFile}`
            );


            // ------------------------------------------------
            // CHECK FILE EXISTS
            // ------------------------------------------------

            if (!fs.existsSync(evidenceFile)) {

                console.log(
                    "Evidence file: NOT FOUND ❌"
                );

                invalidCount++;

                continue;
            }


            // ------------------------------------------------
            // READ DETECTION FROM FABRIC
            // ------------------------------------------------

            let detection;


            try {

                const result =
                    await contract.evaluateTransaction(
                        "ReadDetection",
                        detectionID
                    );


                detection =
                    parseFabricResponse(
                        result
                    );

            } catch (error) {

                console.log(
                    `Fabric record: FAILED ❌`
                );

                console.log(
                    error.message
                );

                invalidCount++;

                continue;
            }


            console.log(
                `Fabric record: FOUND ✓`
            );


            // ------------------------------------------------
            // HASH VERIFICATION
            // ------------------------------------------------

            const localHash =
                sha256File(
                    evidenceFile
                );


            const blockchainHash =
                detection.frameHash;


            const hashValid =
                localHash === blockchainHash;


            console.log(
                `Hash match: ${
                    hashValid
                        ? "VALID ✓"
                        : "INVALID ✗"
                }`
            );


            // ------------------------------------------------
            // SIGNATURE VERIFICATION
            // ------------------------------------------------

            const signatureValid =
                verifyEd25519(

                    evidenceFile,

                    detection.signature
                );


            console.log(
                `Signature: ${
                    signatureValid
                        ? "VALID ✓"
                        : "INVALID ✗"
                }`
            );


            // ------------------------------------------------
            // FRAME NUMBER
            // ------------------------------------------------

            const frameValid =
                Number(
                    detection.frameNumber
                ) === frameNumber;


            console.log(
                `Frame Number: ${
                    detection.frameNumber
                } ${
                    frameValid
                        ? "✓"
                        : "✗"
                }`
            );


            // ------------------------------------------------
            // VIDEO TIMESTAMP
            // ------------------------------------------------

            console.log(
                `Video Timestamp: ${
                    detection.videoTimestamp
                }`
            );


            // ------------------------------------------------
            // TIMESTAMP SECONDS
            // ------------------------------------------------

            console.log(
                `Timestamp Seconds: ${
                    detection.timestampSeconds
                }`
            );


            // ------------------------------------------------
            // OBJECT
            // ------------------------------------------------

            console.log(
                `Object: ${
                    detection.objectType
                }`
            );


            // ------------------------------------------------
            // CONFIDENCE
            // ------------------------------------------------

            console.log(
                `Confidence: ${
                    detection.confidence
                }`
            );


            // ------------------------------------------------
            // FINAL RESULT
            // ------------------------------------------------

            if (
                hashValid &&
                signatureValid &&
                frameValid
            ) {

                console.log(
                    `RESULT: EVIDENCE VERIFIED ✓`
                );

                validCount++;

            } else {

                console.log(
                    `RESULT: EVIDENCE INVALID ✗`
                );

                invalidCount++;
            }


            console.log();
        }


        // =================================================
        // FINAL SUMMARY
        // =================================================

        console.log(
            "================================================"
        );

        console.log(
            " VERIFICATION SUMMARY"
        );

        console.log(
            "================================================"
        );

        console.log(
            `Valid detections: ${validCount}`
        );

        console.log(
            `Invalid detections: ${invalidCount}`
        );


        if (
            invalidCount === 0 &&
            validCount === 7
        ) {

            console.log();

            console.log(
                "RESULT: ALL TIMESTAMPED EVIDENCE VERIFIED ✓"
            );

        } else {

            console.log();

            console.log(
                "RESULT: SOME EVIDENCE FAILED VERIFICATION ✗"
            );
        }

    } finally {

        gateway.close();

        grpcClient.close();
    }
}


// =========================================================
// ERROR HANDLING
// =========================================================

main().catch(error => {

    console.error();

    console.error(
        "FATAL ERROR:"
    );

    console.error(
        error
    );

    process.exitCode = 1;
});
