const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const {
    connect,
    signers,
    hash
} = require('@hyperledger/fabric-gateway');

const grpc = require('@grpc/grpc-js');


// ============================================================
// FABRIC CONNECTION SETTINGS
// ============================================================

const channelName = 'mychannel';
const chaincodeName = 'cctv';

const mspId = 'Org1MSP';

const cryptoPath =
    path.join(process.env.TEST_NETWORK || path.resolve(__dirname, '../../fabric-samples/test-network'), 'organizations/peerOrganizations/org1.example.com');

const certPath =
    path.join(
        cryptoPath,
        'users/User1@org1.example.com/msp/signcerts/cert.pem'
    );

const keyDirectoryPath =
    path.join(
        cryptoPath,
        'users/User1@org1.example.com/msp/keystore'
    );

const tlsCertPath =
    path.join(
        cryptoPath,
        'peers/peer0.org1.example.com/tls/ca.crt'
    );

const peerEndpoint =
    'localhost:7051';

const peerHostAlias =
    'peer0.org1.example.com';


// ============================================================
// HELPER: LOAD PRIVATE KEY
// ============================================================

function loadPrivateKey() {

    const files =
        fs.readdirSync(keyDirectoryPath);

    const keyFile =
        files.find(file => file.endsWith('_sk'));

    if (!keyFile) {
        throw new Error(
            'No private key found in Fabric keystore.'
        );
    }

    return fs.readFileSync(
        path.join(keyDirectoryPath, keyFile)
    );
}


// ============================================================
// FABRIC IDENTITY
// ============================================================

function newGrpcConnection() {

    const tlsRootCert =
        fs.readFileSync(tlsCertPath);

    const tlsCredentials =
        grpc.credentials.createSsl(tlsRootCert);

    return new grpc.Client(
        peerEndpoint,
        tlsCredentials,
        {
            'grpc.ssl_target_name_override':
                peerHostAlias
        }
    );
}


function newIdentity() {

    const credentials =
        fs.readFileSync(certPath);

    return {
        mspId,
        credentials
    };
}


function newSigner() {

    const privateKeyPem =
        loadPrivateKey();

    const privateKey =
        crypto.createPrivateKey(
            privateKeyPem
        );

    return signers.newPrivateKeySigner(
        privateKey
    );
}


// ============================================================
// MAIN
// ============================================================

async function main() {

    console.log('');
    console.log(
        '=============================================='
    );
    console.log(
        ' TIMESTAMPED CCTV DETECTION RECORDING'
    );
    console.log(
        ' Fabric Chaincode v6.0'
    );
    console.log(
        '=============================================='
    );
    console.log('');


    // --------------------------------------------------------
    // LOAD TIMESTAMPED SECURITY DATA
    // --------------------------------------------------------

    const dataPath =
        path.join(
            __dirname,
            '../security/timestamped_security_data.json'
        );

    if (!fs.existsSync(dataPath)) {

        throw new Error(
            `Security data file not found:\n${dataPath}`
        );
    }

    const events =
        JSON.parse(
            fs.readFileSync(
                dataPath,
                'utf8'
            )
        );


    console.log(
        `Loaded ${events.length} timestamped events.`
    );

    console.log('');


    // --------------------------------------------------------
    // CONNECT TO FABRIC
    // --------------------------------------------------------

    const client =
        newGrpcConnection();

    const gateway =
        connect({
            client,
            identity: newIdentity(),
            signer: newSigner(),

            hash: hash.sha256,

            evaluateOptions: () => ({
                deadline:
                    Date.now() + 5000
            }),

            endorseOptions: () => ({
                deadline:
                    Date.now() + 15000
            }),

            submitOptions: () => ({
                deadline:
                    Date.now() + 15000
            }),

            commitStatusOptions: () => ({
                deadline:
                    Date.now() + 15000
            })
        });


    try {

        const network =
            gateway.getNetwork(channelName);

        const contract =
            network.getContract(
                chaincodeName
            );


        // ----------------------------------------------------
        // SUBMIT EACH TIMESTAMPED DETECTION
        // ----------------------------------------------------

        for (
            let index = 0;
            index < events.length;
            index++
        ) {

            const event =
                events[index];


            // DET-015 ... DET-021
            //
            // DET-008 ... DET-014 already exist
            // from the previous multi-frame test.

            const detectionID =
                `DET-${String(index + 15).padStart(3, '0')}`;


            // Blockchain transaction timestamp
            const timestamp =
                new Date().toISOString();


            console.log(
                '----------------------------------------------'
            );

            console.log(
                `Submitting ${detectionID}...`
            );

            console.log(
                `Frame Number: ${event.frameNumber}`
            );

            console.log(
                `Video Timestamp: ${event.videoTimestamp}`
            );

            console.log(
                `Timestamp Seconds: ${event.timestampSeconds}`
            );

            console.log(
                `Evidence: ${event.evidenceFile}`
            );


            try {

                // ------------------------------------------------
                // v6.0 RecordDetection
                //
                // IMPORTANT:
                // The argument order must exactly match
                // smartcontract.go
                // ------------------------------------------------

                await contract.submitTransaction(

                    'RecordDetection',

                    detectionID,

                    event.cameraID,

                    timestamp,

                    // New v6.0 fields
                    String(event.frameNumber),

                    event.videoTimestamp,

                    String(event.timestampSeconds),

                    // Existing fields
                    event.objectType,

                    String(event.confidence),

                    event.frameHash,

                    event.signature,

                    event.modelHash
                );


                console.log(
                    `${detectionID}: COMMITTED ✓`
                );


                // ------------------------------------------------
                // READ THE RECORD BACK FROM FABRIC
                // ------------------------------------------------

                const result =
                    await contract.evaluateTransaction(
                        'ReadDetection',
                        detectionID
                    );


                const detection =
                    JSON.parse(
                        Buffer.from(result).toString(
                            'utf8'
                        )
                    );


                console.log(
                    'Stored in Fabric:'
                );

                console.log(
                    `  Detection ID: ${detection.detectionID}`
                );

                console.log(
                    `  Camera ID: ${detection.cameraID}`
                );

                console.log(
                    `  Frame Number: ${detection.frameNumber}`
                );

                console.log(
                    `  Video Timestamp: ${detection.videoTimestamp}`
                );

                console.log(
                    `  Timestamp Seconds: ${detection.timestampSeconds}`
                );

                console.log(
                    `  Object: ${detection.objectType}`
                );

                console.log(
                    `  Confidence: ${detection.confidence}`
                );

                console.log(
                    `  Frame Hash: ${detection.frameHash}`
                );

                console.log(
                    `  Model Hash: ${detection.modelHash}`
                );

                console.log('');


            } catch (error) {

                console.error(
                    `${detectionID}: FAILED`
                );

                console.error(
                    error.message
                );

                console.log('');
            }
        }


        console.log(
            '=============================================='
        );

        console.log(
            ' Finished timestamped detection recording.'
        );

        console.log(
            '=============================================='
        );

    } finally {

        gateway.close();
        client.close();

    }
}


// ============================================================
// ERROR HANDLING
// ============================================================

main().catch(error => {

    console.error('');
    console.error(
        'FATAL ERROR:'
    );

    console.error(
        error
    );

    process.exitCode = 1;

});
