const path = require('path');
const fs = require('fs');
const crypto = require('crypto');

const EVIDENCE_FILE =
    path.resolve(__dirname, '../security/evidence.txt';

const PUBLIC_KEY_FILE =
    path.resolve(__dirname, '../security/camera_001_public_key.pem';

const SECURITY_DATA_FILE =
    path.resolve(__dirname, '../security/security_data.json';


function calculateSha256(filePath) {
    const fileData = fs.readFileSync(filePath);

    return crypto
        .createHash('sha256')
        .update(fileData)
        .digest();
}


function verifyEd25519Signature(hashBuffer, signatureHex, publicKeyPath) {
    const publicKey = fs.readFileSync(publicKeyPath);

    const signature = Buffer.from(signatureHex, 'hex');

    return crypto.verify(
        null,
        hashBuffer,
        publicKey,
        signature
    );
}


function main() {

    const securityData = JSON.parse(
        fs.readFileSync(SECURITY_DATA_FILE, 'utf8')
    );

    const currentHash = calculateSha256(EVIDENCE_FILE);

    const storedHash = Buffer.from(
        securityData.frameHash,
        'hex'
    );

    const hashMatches =
        currentHash.equals(storedHash);

    let signatureValid = false;

    if (hashMatches) {
        signatureValid = verifyEd25519Signature(
            currentHash,
            securityData.signature,
            PUBLIC_KEY_FILE
        );
    }

    console.log('=== EVIDENCE VERIFICATION ===');
    console.log('');

    console.log('Evidence file:', EVIDENCE_FILE);
    console.log('');

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
        hashMatches ? 'VALID' : 'INVALID'
    );

    console.log(
        'Signature    :',
        signatureValid ? 'VALID' : 'INVALID'
    );

    console.log('');

    if (hashMatches && signatureValid) {
        console.log('RESULT: EVIDENCE VERIFIED ✓');
    } else {
        console.log('RESULT: EVIDENCE VERIFICATION FAILED ✗');
        console.log('WARNING: Evidence may have been modified.');
    }
}


main();
