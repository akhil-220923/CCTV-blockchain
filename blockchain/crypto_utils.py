import os
import hashlib
import json
from typing import Tuple, Union, List
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


def calculate_file_sha256(file_path: str) -> str:
    """Calculate the SHA-256 hexadecimal hash of any file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


def calculate_data_sha256(data: Union[bytes, str]) -> str:
    """Calculate the SHA-256 hexadecimal hash of bytes or string."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def generate_key_pair(private_key_path: str, public_key_path: str) -> Tuple[str, str]:
    """Generate and save an Ed25519 key pair."""
    os.makedirs(os.path.dirname(os.path.abspath(private_key_path)), exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(public_key_path)), exist_ok=True)

    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    priv_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    with open(private_key_path, "wb") as f:
        f.write(priv_bytes)

    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(public_key_path, "wb") as f:
        f.write(pub_bytes)

    return private_key_path, public_key_path


def load_private_key_from_file(private_key_path: str) -> ed25519.Ed25519PrivateKey:
    """Load an Ed25519 private key from PEM file."""
    with open(private_key_path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def load_public_key_from_file(public_key_path: str) -> ed25519.Ed25519PublicKey:
    """Load an Ed25519 public key from PEM file."""
    with open(public_key_path, "rb") as f:
        return serialization.load_pem_public_key(f.read())


def load_public_key_from_pem(pem_str: str) -> ed25519.Ed25519PublicKey:
    """Load an Ed25519 public key from PEM string."""
    return serialization.load_pem_public_key(pem_str.encode("utf-8"))


def sign_data(private_key: ed25519.Ed25519PrivateKey, data: Union[bytes, str]) -> str:
    """Sign data using Ed25519 private key and return hex-encoded signature."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    signature = private_key.sign(data)
    return signature.hex()


def verify_signature(public_key: ed25519.Ed25519PublicKey, data: Union[bytes, str], signature_hex: str) -> bool:
    """Verify Ed25519 signature over data."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    try:
        sig_bytes = bytes.fromhex(signature_hex)
        public_key.verify(sig_bytes, data)
        return True
    except Exception:
        return False


def compute_merkle_root(tx_hashes: List[str]) -> str:
    """Compute Merkle Root for a list of transaction hashes."""
    if not tx_hashes:
        return calculate_data_sha256("EMPTY_TREE")
    
    current_level = tx_hashes[:]
    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i + 1] if i + 1 < len(current_level) else left
            combined = calculate_data_sha256(left + right)
            next_level.append(combined)
        current_level = next_level
    return current_level[0]
