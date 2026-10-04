from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization


# Generate a new private key for Camera-001
private_key = ed25519.Ed25519PrivateKey.generate()

# Derive the corresponding public key
public_key = private_key.public_key()


# Save the private key
with open("camera_001_private_key.pem", "wb") as f:
    f.write(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
    )


# Save the public key
with open("camera_001_public_key.pem", "wb") as f:
    f.write(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    )


print("Camera-001 key pair generated successfully.")
print("Private key: camera_001_private_key.pem")
print("Public key : camera_001_public_key.pem")
