import cv2
import os

VIDEO_FILE = "../video/test_cctv.mp4"
OUTPUT_DIR = "test_frames/multiple"

os.makedirs(OUTPUT_DIR, exist_ok=True)

cap = cv2.VideoCapture(VIDEO_FILE)

if not cap.isOpened():
    print("ERROR: Could not open video.")
    exit(1)

total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps = cap.get(cv2.CAP_PROP_FPS)

print("=== MULTI-FRAME CCTV TEST ===")
print(f"Total frames : {total_frames}")
print(f"FPS          : {fps}")

# Process one frame every 2 seconds
if fps > 0:
    frame_interval = int(fps * 2)
else:
    frame_interval = 50

frame_number = 0
saved_count = 0

while True:

    success, frame = cap.read()

    if not success:
        break

    if frame_number % frame_interval == 0:

        output_file = os.path.join(
            OUTPUT_DIR,
            f"frame_{saved_count:03d}.jpg"
        )

        cv2.imwrite(output_file, frame)

        print(
            f"Saved frame {frame_number} -> {output_file}"
        )

        saved_count += 1

    frame_number += 1

cap.release()

print()
print("=== PROCESSING COMPLETE ===")
print(f"Frames examined : {frame_number}")
print(f"Frames saved    : {saved_count}")
print(f"Output folder   : {OUTPUT_DIR}")
