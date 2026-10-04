from security_module import sign_evidence


EVIDENCE_FILE = "evidence.txt"


def main():
    evidence_hash, signature = sign_evidence(EVIDENCE_FILE)

    frame_hash = evidence_hash.hex()
    signature_hex = signature.hex()

    print("=== DETECTION SECURITY DATA ===")
    print(f"Evidence file : {EVIDENCE_FILE}")
    print(f"Frame hash    : {frame_hash}")
    print(f"Signature     : {signature_hex}")
    print()
    print("These values are ready to be stored with")
    print("the detection event on Hyperledger Fabric.")


if __name__ == "__main__":
    main()
