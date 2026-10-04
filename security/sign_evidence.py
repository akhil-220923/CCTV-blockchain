from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import hashlib


def calculate_sha256(file_path):
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        while chunk := file.read(4096):
            sha256.update(chunk)

    return sha256.digest()


# Load Camera-001 private key
with open("camera_001_private_key.pem", "rb") as f:
    private_key = serialization.load_pem_private_key(
        f.read(),
        password=None
    )


# Calculate evidence hash
evidence_hash = calculate_sha256("evidence.txt")


# Sign the hash using Camera-001's private key
signature = private_key.sign(evidence_hash)


print("Camera-001 evidence signing successful.")
print("Evidence SHA-256:", evidence_hash.hex())
print("Digital signature:", signature.hex())

