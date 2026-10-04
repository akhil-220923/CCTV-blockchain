import json
import os

from security_module import sign_evidence


INPUT_FILE = "timestamped_detection_data.json"
OUTPUT_FILE = "timestamped_security_data.json"

CAMERA_ID = "CAM-001"
MODEL_HASH = "TEST_MODEL_HASH"


def main():

    with open(INPUT_FILE, "r") as file:
        detections = json.load(file)

    security_events = []

    print("=== TIMESTAMP-AWARE SECURITY GENERATION ===")
    print(f"Detections loaded: {len(detections)}")
    print()

    for index, detection in enumerate(detections):

        evidence_file = detection["evidenceFile"]

        if not os.path.exists(evidence_file):
            print(
                f"ERROR: Evidence not found: {evidence_file}"
            )
            continue

        # Calculate SHA-256 and create Ed25519 signature
        evidence_hash, signature = sign_evidence(
            evidence_file
        )

        event = {
            "detectionID": f"TIME-TEST-{index + 1:03d}",
            "cameraID": CAMERA_ID,

            # Actual video information
            "frameNumber": detection["frameNumber"],
            "videoTimestamp": detection["videoTimestamp"],
            "timestampSeconds": detection["timestampSeconds"],

            # Detection information
            "evidenceFile": evidence_file,
            "objectType": detection["objectType"],
            "confidence": detection["confidence"],

            # Security information
            "frameHash": evidence_hash.hex(),
            "signature": signature.hex(),

            # Test model identifier
            "modelHash": MODEL_HASH
        }

        security_events.append(event)

        print(
            f"{event['detectionID']} | "
            f"Frame {event['frameNumber']} | "
            f"{event['videoTimestamp']} | "
            f"Security generated ✓"
        )

    with open(OUTPUT_FILE, "w") as file:
        json.dump(
            security_events,
            file,
            indent=4
        )

    print()
    print("=== SECURITY GENERATION COMPLETE ===")
    print(
        f"Events generated : {len(security_events)}"
    )
    print(
        f"Output file      : {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
