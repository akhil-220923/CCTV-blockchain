import hashlib


def calculate_sha256(file_path):
    """Calculate the SHA-256 hash of a file."""

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        while chunk := file.read(4096):
            sha256.update(chunk)

    return sha256.hexdigest()


if __name__ == "__main__":
    file_path = "evidence.txt"

    file_hash = calculate_sha256(file_path)

    print("Evidence file:", file_path)
    print("SHA-256 hash :", file_hash)
