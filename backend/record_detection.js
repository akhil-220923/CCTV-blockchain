const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const grpc = require('@grpc/grpc-js');
const { connect, signers } = require('@hyperledger/fabric-gateway');

const TEST_NETWORK = (process.env.TEST_NETWORK || path.resolve(__dirname, '../../fabric-samples/test-network'));
const SECURITY_DATA_PATH = path.resolve(__dirname, '../security/frame_security_data.json';

const CERT_PATH =
    `${TEST_NETWORK}/organizations/peerOrganizations/org1.example.com/users/User1@org1.example.com/msp/signcerts/cert.pem`;

const KEY_PATH =
    `${TEST_NETWORK}/organizations/peerOrganizations/org1.example.com/users/User1@org1.example.com/msp/keystore/859a808f22bceab6811340de7a81c714fa73f8acccdd01e7b104134ff368c59c_sk`;

const TLS_CERT_PATH =
    `${TEST_NETWORK}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt`;

const PEER_ENDPOINT = 'localhost:7051';
const PEER_HOST_ALIAS = 'peer0.org1.example.com';

function newGrpcConnection() {
    const tlsRootCert = fs.readFileSync(TLS_CERT_PATH);

    const tlsCredentials = grpc.credentials.createSsl(tlsRootCert);

    return new grpc.Client(
        PEER_ENDPOINT,
        tlsCredentials,
        {
            'grpc.ssl_target_name_override': PEER_HOST_ALIAS,
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
    const privateKeyPem = fs.readFileSync(KEY_PATH);
    const privateKey = crypto.createPrivateKey(privateKeyPem);

    return signers.newPrivateKeySigner(privateKey);
}

function loadSecurityData() {
    const data = fs.readFileSync(SECURITY_DATA_PATH, 'utf8');

    return JSON.parse(data);
}

async function main() {
    const securityData = loadSecurityData();

    console.log('=== SECURITY DATA ===');
    console.log('Evidence file:', securityData.evidenceFile);
    console.log('Frame hash   :', securityData.frameHash);
    console.log('Signature    :', securityData.signature);

    const client = newGrpcConnection();

    const gateway = connect({
        client,
        identity: newIdentity(),
        signer: newSigner(),

        evaluateOptions: () => ({
            deadline: Date.now() + 5000,
        }),

        endorseOptions: () => ({
            deadline: Date.now() + 15000,
        }),

        submitOptions: () => ({
            deadline: Date.now() + 15000,
        }),

        commitStatusOptions: () => ({
            deadline: Date.now() + 15000,
        }),
    });

    try {
        const network = gateway.getNetwork('mychannel');
        const contract = network.getContract('cctv');

        console.log('');
        console.log('Submitting DET-005 to Fabric...');

        await contract.submitTransaction(
            'RecordDetection',
            'DET-007',
            'CAM-001',
            '2026-09-20T17:00:00',
            'person',
            '0.94',
            securityData.frameHash,
            securityData.signature,
            'TEST_MODEL_HASH'
        );

        console.log('Transaction committed successfully.');

        console.log('');
        console.log('Reading DET-007 from Fabric...');

        const detection = await contract.evaluateTransaction(
            'ReadDetection',
            'DET-007'
        );

        console.log('Detection read from Fabric:');
        console.log(new TextDecoder().decode(detection));

    } finally {
        gateway.close();
        client.close();
    }
}

main().catch((error) => {
    console.error('Detection transaction failed:');
    console.error(error);
    process.exit(1);
});
