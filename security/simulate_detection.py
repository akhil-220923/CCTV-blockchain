import cv2
import os

INPUT_FILE = "test_frames/test_frame_001.jpg"
OUTPUT_DIR = "test_frames"
OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "test_frame_001_detected.jpg"
)

# Read the real CCTV frame
frame = cv2.imread(INPUT_FILE)

if frame is None:
    print("ERROR: Could not read input frame.")
    exit(1)

height, width = frame.shape[:2]

print("=== TEST DETECTION ===")
print(f"Frame width  : {width}")
print(f"Frame height : {height}")

# --------------------------------------------------
# TEMPORARY TEST DETECTION
# This will later be replaced by YOLO best.pt
# --------------------------------------------------

x1 = int(width * 0.30)
y1 = int(height * 0.20)
x2 = int(width * 0.60)
y2 = int(height * 0.85)

object_type = "person"
confidence = 0.94

# Draw bounding box
cv2.rectangle(
    frame,
    (x1, y1),
    (x2, y2),
    (0, 255, 0),
    2
)

# Detection label
label = f"TEST: {object_type} {confidence:.2f}"

cv2.putText(
    frame,
    label,
    (x1, max(y1 - 10, 20)),
    cv2.FONT_HERSHEY_SIMPLEX,
    0.7,
    (0, 255, 0),
    2
)

# Save annotated evidence frame
cv2.imwrite(OUTPUT_FILE, frame)

print()
print("Detection created successfully.")
print(f"Object type : {object_type}")
print(f"Confidence  : {confidence}")
print(f"Bounding box: [{x1}, {y1}, {x2}, {y2}]")
print(f"Saved to    : {OUTPUT_FILE}")
