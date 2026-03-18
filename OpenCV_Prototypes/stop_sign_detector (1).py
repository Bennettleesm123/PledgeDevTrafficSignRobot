"""
Milestone 1: Stationary Vision Test - Stop Sign Detector
=========================================================
Method: Color Masking (HSV red detection + octagon shape check)

Chosen over OCR/feature matching because:
  - Runs at ~30fps with no extra installs
  - Pure OpenCV + NumPy math, works on any laptop
  - OCR (Tesseract) runs at ~5fps and needs an external engine installed

Requirements:
    pip install opencv-python numpy

Usage:
    # Static image:
    python stop_sign_detector.py --image path/to/image.jpg

    # Live webcam:
    python stop_sign_detector.py --camera
"""

import cv2
import numpy as np
import argparse


def detect_stop_sign(frame):
    """
    Detect a stop sign using red color masking + octagon contour check.
    Returns: (detected: bool, annotated_frame)
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Red wraps around 0 and 180 in HSV, so we need two ranges
    mask1 = cv2.inRange(hsv, np.array([0,   120,  70]), np.array([10,  255, 255]))
    mask2 = cv2.inRange(hsv, np.array([170, 120,  70]), np.array([180, 255, 255]))
    red_mask = cv2.bitwise_or(mask1, mask2)

    # Clean up noise with morphological ops
    kernel   = np.ones((5, 5), np.uint8)
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN,  kernel)
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    detected = False
    output   = frame.copy()

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 1500:   # ignore tiny red blobs (brake lights, clothing, etc.)
            continue

        peri   = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)

        # Octagon = 8 sides; allow 6-10 for angle/distance tolerance
        if 6 <= len(approx) <= 10:
            x, y, w, h = cv2.boundingRect(approx)
            if 0.7 < (w / float(h)) < 1.3:   # roughly square bounding box
                detected = True
                cv2.drawContours(output, [approx], -1, (0, 255, 0), 3)
                cv2.rectangle(output, (x, y), (x + w, y + h), (0, 200, 255), 2)
                cv2.putText(output, "STOP SIGN", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # Status banner at top of frame
    color  = (0, 255, 0) if detected else (0, 0, 255)
    status = "STOP SIGN DETECTED" if detected else "Scanning..."
    cv2.putText(output, status, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

    return detected, output


def run_on_image(path):
    frame = cv2.imread(path)
    if frame is None:
        print(f"[ERROR] Could not load image: {path}")
        return
    detected, output = detect_stop_sign(frame)
    print("STOP SIGN DETECTED" if detected else "No stop sign found")
    cv2.imshow("Stop Sign Detector", output)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def run_on_camera():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Could not open webcam.")
        return
    print("Press 'q' to quit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        _, output = detect_stop_sign(frame)
        cv2.imshow("Stop Sign Detector", output)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stop Sign Detector")
    group  = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--image",  type=str, help="Path to a test image")
    group.add_argument("--camera", action="store_true", help="Use live webcam")
    args = parser.parse_args()

    if args.image:
        run_on_image(args.image)
    else:
        run_on_camera()
