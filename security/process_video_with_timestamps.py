import cv2
import os
import json

VIDEO_FILE = "../video/test_cctv.mp4"

OUTPUT_DIR = "test_frames/timestamped"
METADATA_FILE = "timestamped_frames.json"

os.makedirs(OUTPUT_DIR, exist_ok=True)

cap = cv2.VideoCapture(VIDEO_FILE)

if not cap.isOpened():
    print("ERROR: Could not open video.")
    exit(1)

total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps = cap.get(cv2.CAP_PROP_FPS)

print("=== TIMESTAMP-AWARE CCTV PROCESSING ===")
print(f"Total frames : {total_frames}")
print(f"FPS          : {fps}")

# Extract one frame every 2 seconds
interval_seconds = 2
frame_interval = max(1, int(fps * interval_seconds))

metadata = []

frame_number = 0
event_index = 0

while True:

    success, frame = cap.read()

    if not success:
        break

    if frame_number % frame_interval == 0:

        timestamp_seconds = frame_number / fps

        minutes = int(timestamp_seconds // 60)
        seconds = timestamp_seconds % 60

        filename = f"frame_{event_index:03d}.jpg"
        output_file = os.path.join(
            OUTPUT_DIR,
            filename
        )

        cv2.imwrite(output_file, frame)

        frame_info = {
            "frameNumber": frame_number,
            "timestampSeconds": round(timestamp_seconds, 3),
            "timestamp": f"{minutes:02d}:{seconds:06.3f}",
            "evidenceFile": output_file
        }

        metadata.append(frame_info)

        print(
            f"Frame {frame_number:5d} "
            f"| Video time {frame_info['timestamp']} "
            f"| {filename}"
        )

        event_index += 1

    frame_number += 1

cap.release()

with open(METADATA_FILE, "w") as file:
    json.dump(metadata, file, indent=4)

print()
print("=== PROCESSING COMPLETE ===")
print(f"Frames extracted : {len(metadata)}")
print(f"Metadata file    : {METADATA_FILE}")
