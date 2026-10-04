const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const grpc = require('@grpc/grpc-js');
const { connect, signers } = require('@hyperledger/fabric-gateway');

const TEST_NETWORK = (process.env.TEST_NETWORK || path.resolve(__dirname, '../../fabric-samples/test-network'));

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
    const credentials = fs.readFileSync(CERT_PATH);

    return {
        mspId: 'Org1MSP',
        credentials,
    };
}

function newSigner() {
    const privateKeyPem = fs.readFileSync(KEY_PATH);

    const privateKey = crypto.createPrivateKey(privateKeyPem);

    return signers.newPrivateKeySigner(privateKey);
}

async function main() {
    const client = newGrpcConnection();

    const gateway = connect({
        client,
        identity: newIdentity(),
        signer: newSigner(),
        evaluateOptions: () => {
            return {
                deadline: Date.now() + 5000,
            };
        },
    });

    try {
        const network = gateway.getNetwork('mychannel');
        const contract = network.getContract('cctv');

        const result = await contract.evaluateTransaction(
            'ReadCamera',
            'CAM-001'
        );

        console.log('=== FABRIC CONNECTION TEST ===');
        console.log('Successfully connected to Fabric.');
        console.log('ReadCamera result:');
        console.log(new TextDecoder().decode(result));
    } finally {
        gateway.close();
        client.close();
    }
}

main().catch((error) => {
    console.error('Fabric connection failed:');
    console.error(error);
    process.exit(1);
});
