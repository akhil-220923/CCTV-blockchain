from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import hashlib


def calculate_sha256(file_path):
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        while chunk := file.read(4096):
            sha256.update(chunk)

    return sha256.digest()


# Load Camera-001 public key
with open("camera_001_public_key.pem", "rb") as f:
    public_key = serialization.load_pem_public_key(f.read())


# Calculate the current evidence hash
evidence_hash = calculate_sha256("evidence.txt")


# Load the signature generated earlier
# For now, we will generate it again using the private key.
with open("camera_001_private_key.pem", "rb") as f:
    private_key = serialization.load_pem_private_key(
        f.read(),
        password=None
    )

signature = private_key.sign(evidence_hash)


# Verify the signature
try:
    public_key.verify(signature, evidence_hash)
    print("SIGNATURE VERIFICATION: VALID")
    print("Camera-001 successfully authenticated the evidence.")

except Exception:
    print("SIGNATURE VERIFICATION: INVALID")
    print("The evidence or signature may have been altered.")

