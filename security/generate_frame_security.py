import json
from security_module import sign_evidence

EVIDENCE_FILE = "test_frames/test_frame_001_detected.jpg"
OUTPUT_FILE = "frame_security_data.json"


def main():
    evidence_hash, signature = sign_evidence(EVIDENCE_FILE)

    security_data = {
        "evidenceFile": EVIDENCE_FILE,
        "frameHash": evidence_hash.hex(),
        "signature": signature.hex()
    }

    with open(OUTPUT_FILE, "w") as file:
        json.dump(security_data, file, indent=4)

    print("=== FRAME SECURITY DATA ===")
    print(f"Evidence : {EVIDENCE_FILE}")
    print(f"Hash     : {security_data['frameHash']}")
    print(f"Signature: {security_data['signature']}")
    print(f"Output   : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
