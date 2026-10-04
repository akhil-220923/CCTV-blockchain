const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const grpc = require('@grpc/grpc-js');
const { connect, signers } = require('@hyperledger/fabric-gateway');

const TEST_NETWORK =
    (process.env.TEST_NETWORK || path.resolve(__dirname, '../../fabric-samples/test-network'));

const EVIDENCE_FILE =
    path.resolve(__dirname, '../security/test_frames/test_frame_001_detected.jpg';

const PUBLIC_KEY_FILE =
    path.resolve(__dirname, '../security/camera_001_public_key.pem';

const CERT_PATH =
    `${TEST_NETWORK}/organizations/peerOrganizations/org1.example.com/users/User1@org1.example.com/msp/signcerts/cert.pem`;

const KEYSTORE_PATH =
    `${TEST_NETWORK}/organizations/peerOrganizations/org1.example.com/users/User1@org1.example.com/msp/keystore`;

const TLS_CERT_PATH =
    `${TEST_NETWORK}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt`;

const PEER_ENDPOINT = 'localhost:7051';
const PEER_HOST_ALIAS = 'peer0.org1.example.com';

const DETECTION_ID = 'DET-007';

function newGrpcConnection() {
    const tlsRootCert = fs.readFileSync(TLS_CERT_PATH);

    const tlsCredentials =
        grpc.credentials.createSsl(tlsRootCert);

    return new grpc.Client(
        PEER_ENDPOINT,
        tlsCredentials,
        {
            'grpc.ssl_target_name_override':
                PEER_HOST_ALIAS,
        }
    );
}

function newIdentity() {
    return {
        mspId: 'Org1MSP',
        credentials: fs.readFileSync(CERT_PATH),
    };
}

function newSigner() {
    const keyFiles = fs.readdirSync(KEYSTORE_PATH);

    const keyFile = keyFiles.find(
        file => file.endsWith('_sk')
    );

    if (!keyFile) {
        throw new Error(
            'No Fabric private key found in keystore.'
        );
    }

    const keyPath =
        `${KEYSTORE_PATH}/${keyFile}`;

    console.log(
        'Using Fabric identity key:',
        keyFile
    );

    const privateKeyPem =
        fs.readFileSync(keyPath);

    const privateKey =
        crypto.createPrivateKey(privateKeyPem);

    return signers.newPrivateKeySigner(privateKey);
}

function calculateSha256(filePath) {
    const fileData =
        fs.readFileSync(filePath);

    return crypto
        .createHash('sha256')
        .update(fileData)
        .digest();
}

function verifyEd25519Signature(
    hashBuffer,
    signatureHex
) {
    const publicKey =
        fs.readFileSync(PUBLIC_KEY_FILE);

    const signature =
        Buffer.from(signatureHex, 'hex');

    return crypto.verify(
        null,
        hashBuffer,
        publicKey,
        signature
    );
}

async function main() {

    console.log('=== DETECTION VERIFICATION ===');
    console.log('');

    if (!fs.existsSync(EVIDENCE_FILE)) {
        throw new Error(
            `Evidence file not found: ${EVIDENCE_FILE}`
        );
    }

    if (!fs.existsSync(PUBLIC_KEY_FILE)) {
        throw new Error(
            `Camera public key not found: ${PUBLIC_KEY_FILE}`
        );
    }

    const client =
        newGrpcConnection();

    const gateway = connect({
        client,
        identity: newIdentity(),
        signer: newSigner(),
        evaluateOptions: () => ({
            deadline: Date.now() + 5000,
        }),
    });

    try {

        const network =
            gateway.getNetwork('mychannel');

        const contract =
            network.getContract('cctv');

        console.log(
            `Reading ${DETECTION_ID} from Fabric...`
        );

        const result =
            await contract.evaluateTransaction(
                'ReadDetection',
                DETECTION_ID
            );

        const detection =
            JSON.parse(
                new TextDecoder().decode(result)
            );

        console.log('');
        console.log(
            'Detection ID :',
            detection.detectionID
        );

        console.log(
            'Camera ID    :',
            detection.cameraID
        );

        console.log(
            'Object       :',
            detection.objectType
        );

        console.log(
            'Confidence   :',
            detection.confidence
        );

        console.log('');

        // Calculate hash of the current evidence image
        const currentHash =
            calculateSha256(EVIDENCE_FILE);

        // Hash stored on Fabric
        const storedHash =
            Buffer.from(
                detection.frameHash,
                'hex'
            );

        const hashMatches =
            currentHash.equals(storedHash);

        // Verify Ed25519 signature
        let signatureValid = false;

        if (hashMatches) {
            signatureValid =
                verifyEd25519Signature(
                    currentHash,
                    detection.signature
                );
        }

        console.log(
            'Stored hash  :',
            storedHash.toString('hex')
        );

        console.log(
            'Current hash :',
            currentHash.toString('hex')
        );

        console.log('');

        console.log(
            'Hash match   :',
            hashMatches
                ? 'VALID'
                : 'INVALID'
        );

        console.log(
            'Signature    :',
            signatureValid
                ? 'VALID'
                : 'INVALID'
        );

        console.log('');

        if (hashMatches && signatureValid) {

            console.log(
                'RESULT: EVIDENCE VERIFIED ✓'
            );

            console.log(
                'The current evidence matches the hash stored on Fabric.'
            );

            console.log(
                'The stored signature is valid.'
            );

        } else {

            console.log(
                'RESULT: EVIDENCE VERIFICATION FAILED ✗'
            );

            console.log(
                'WARNING: Evidence may have been modified.'
            );
        }

    } finally {

        gateway.close();
        client.close();
    }
}

main().catch((error) => {

    console.error('');
    console.error(
        'Verification failed:'
    );

    console.error(error);

    process.exit(1);
});
