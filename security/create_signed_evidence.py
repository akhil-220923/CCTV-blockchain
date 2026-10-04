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


# Hash the original evidence
evidence_hash = calculate_sha256("evidence.txt")

# Sign the original hash
signature = private_key.sign(evidence_hash)

# Save the signature
with open("evidence.signature", "wb") as f:
    f.write(signature)

print("Original evidence signed successfully.")
print("Signature saved as: evidence.signature")
print("Original SHA-256:", evidence_hash.hex())
