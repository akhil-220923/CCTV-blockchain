import cv2
import os
import json

INPUT_DIR = "test_frames/timestamped"
OUTPUT_DIR = "test_frames/timestamped_detected"
METADATA_FILE = "timestamped_frames.json"
OUTPUT_METADATA = "timestamped_detection_data.json"

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(METADATA_FILE, "r") as file:
    frames = json.load(file)

print("=== TIMESTAMP-AWARE TEST DETECTION ===")
print(f"Frames loaded: {len(frames)}")
print()

detections = []

for index, frame_info in enumerate(frames):

    input_file = frame_info["evidenceFile"]

    image = cv2.imread(input_file)

    if image is None:
        print(f"ERROR: Could not read {input_file}")
        continue

    height, width = image.shape[:2]

    # Temporary test bounding box
    x1 = int(width * 0.30)
    y1 = int(height * 0.20)
    x2 = int(width * 0.60)
    y2 = int(height * 0.85)

    object_type = "person"
    confidence = 0.94

    label = f"TEST: {object_type} {confidence:.2f}"

    cv2.rectangle(
        image,
        (x1, y1),
        (x2, y2),
        (0, 255, 0),
        2
    )

    cv2.putText(
        image,
        label,
        (x1, max(y1 - 10, 20)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )

    output_file = os.path.join(
        OUTPUT_DIR,
        f"detected_{index:03d}.jpg"
    )

    cv2.imwrite(output_file, image)

    detection = {
        "frameNumber": frame_info["frameNumber"],
        "videoTimestamp": frame_info["timestamp"],
        "timestampSeconds": frame_info["timestampSeconds"],
        "evidenceFile": output_file,
        "objectType": object_type,
        "confidence": confidence
    }

    detections.append(detection)

    print(
        f"{output_file} | "
        f"Frame {frame_info['frameNumber']} | "
        f"Video time {frame_info['timestamp']} | "
        f"{object_type} {confidence:.2f}"
    )


with open(OUTPUT_METADATA, "w") as file:
    json.dump(detections, file, indent=4)

print()
print("=== DETECTION PROCESSING COMPLETE ===")
print(f"Detections generated : {len(detections)}")
print(f"Metadata file         : {OUTPUT_METADATA}")
