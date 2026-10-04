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


# Calculate hash of the CURRENT evidence
current_hash = calculate_sha256("evidence.txt")


# Load the ORIGINAL signature
with open("evidence.signature", "rb") as f:
    original_signature = f.read()


print("Current evidence SHA-256:")
print(current_hash.hex())

print("\nVerifying original signature against current evidence...")

try:
    public_key.verify(original_signature, current_hash)

    print("SIGNATURE VERIFICATION: VALID")
    print("Evidence is authentic and unchanged.")

except Exception:
    print("SIGNATURE VERIFICATION: INVALID")
    print("WARNING: Evidence has been modified or the signature is invalid.")

