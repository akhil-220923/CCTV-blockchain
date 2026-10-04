import json
import os

from security_module import sign_evidence

INPUT_DIR = "test_frames/detected"
OUTPUT_FILE = "multiple_frame_security_data.json"

CAMERA_ID = "CAM-001"
OBJECT_TYPE = "person"
CONFIDENCE = 0.94
MODEL_HASH = "TEST_MODEL_HASH"

def main():

    files = sorted(
        file for file in os.listdir(INPUT_DIR)
        if file.lower().endswith((".jpg", ".jpeg", ".png"))
    )

    security_events = []

    print("=== MULTI-FRAME SECURITY GENERATION ===")
    print(f"Frames found: {len(files)}")
    print()

    for index, filename in enumerate(files):

        file_path = os.path.join(
            INPUT_DIR,
            filename
        )

        evidence_hash, signature = sign_evidence(
            file_path
        )

        event = {
            "detectionID": f"TEST-{index + 1:03d}",
            "cameraID": CAMERA_ID,
            "evidenceFile": file_path,
            "objectType": OBJECT_TYPE,
            "confidence": CONFIDENCE,
            "frameHash": evidence_hash.hex(),
            "signature": signature.hex(),
            "modelHash": MODEL_HASH
        }

        security_events.append(event)

        print(
            f"{filename} -> "
            f"{event['detectionID']} -> security generated"
        )

    with open(OUTPUT_FILE, "w") as file:
        json.dump(
            security_events,
            file,
            indent=4
        )

    print()
    print("=== SECURITY GENERATION COMPLETE ===")
    print(f"Events generated : {len(security_events)}")
    print(f"Output file      : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
