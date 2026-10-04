import cv2
import os

VIDEO_FILE = "../video/test_cctv.mp4"
OUTPUT_DIR = "test_frames"

os.makedirs(OUTPUT_DIR, exist_ok=True)

cap = cv2.VideoCapture(VIDEO_FILE)

if not cap.isOpened():
    print("ERROR: Could not open video.")
    exit(1)

total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps = cap.get(cv2.CAP_PROP_FPS)

print("=== CCTV VIDEO TEST ===")
print(f"Total frames : {total_frames}")
print(f"FPS          : {fps}")

target_frame = total_frames // 2

cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

success, frame = cap.read()

if not success:
    print("ERROR: Could not read selected frame.")
    cap.release()
    exit(1)

output_file = os.path.join(
    OUTPUT_DIR,
    "test_frame_001.jpg"
)

cv2.imwrite(output_file, frame)

cap.release()

print()
print("Frame extracted successfully.")
print(f"Frame number : {target_frame}")
print(f"Saved to     : {output_file}")
