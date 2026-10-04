import hashlib

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


PRIVATE_KEY_FILE = "camera_001_private_key.pem"
PUBLIC_KEY_FILE = "camera_001_public_key.pem"


def calculate_sha256(file_path):
    """
    Calculate the SHA-256 hash of an evidence file.
    """

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        while chunk := file.read(4096):
            sha256.update(chunk)

    return sha256.digest()


def load_private_key():
    """
    Load Camera-001's private key.
    """

    with open(PRIVATE_KEY_FILE, "rb") as file:
        return serialization.load_pem_private_key(
            file.read(),
            password=None
        )


def load_public_key():
    """
    Load Camera-001's public key.
    """

    with open(PUBLIC_KEY_FILE, "rb") as file:
        return serialization.load_pem_public_key(
            file.read()
        )


def sign_evidence(file_path):
    """
    Hash the evidence and sign the hash using
    Camera-001's private key.
    """

    evidence_hash = calculate_sha256(file_path)

    private_key = load_private_key()

    signature = private_key.sign(evidence_hash)

    return evidence_hash, signature


def verify_evidence(file_path, signature):
    """
    Verify that the current evidence matches
    the supplied signature.
    """

    evidence_hash = calculate_sha256(file_path)

    public_key = load_public_key()

    try:
        public_key.verify(signature, evidence_hash)
        return True, evidence_hash

    except Exception:
        return False, evidence_hash
