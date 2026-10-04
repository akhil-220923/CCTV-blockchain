import cv2
import os

INPUT_DIR = "test_frames/multiple"
OUTPUT_DIR = "test_frames/detected"

os.makedirs(OUTPUT_DIR, exist_ok=True)

files = sorted(
    file for file in os.listdir(INPUT_DIR)
    if file.lower().endswith((".jpg", ".jpeg", ".png"))
)

print("=== MULTI-FRAME TEST DETECTION ===")
print(f"Input frames: {len(files)}")
print()

for index, filename in enumerate(files):

    input_path = os.path.join(INPUT_DIR, filename)

    frame = cv2.imread(input_path)

    if frame is None:
        print(f"WARNING: Could not read {filename}")
        continue

    height, width = frame.shape[:2]

    # ------------------------------------------------
    # TEMPORARY TEST DETECTION
    # This will later be replaced by best.pt
    # ------------------------------------------------

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

    # Draw label
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

    output_path = os.path.join(
        OUTPUT_DIR,
        f"detected_{index:03d}.jpg"
    )

    cv2.imwrite(output_path, frame)

    print(
        f"{filename} -> "
        f"{os.path.basename(output_path)}"
    )

print()
print("=== DETECTION PROCESSING COMPLETE ===")
print(f"Output folder: {OUTPUT_DIR}")
