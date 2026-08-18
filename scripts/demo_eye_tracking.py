import sys
import time
from pathlib import Path

# Add project root to path so we can import backend
sys.path.append(str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np

try:
    from backend.eyenav.vision.landmarks import (
        LEFT_EYE_INDICES,
        RIGHT_EYE_INDICES,
        FaceLandmarkExtractor,
    )
except ImportError as e:
    print(f"Error importing EyeNav backend: {e}")
    print("Make sure you run this script from the project root or have the backend in your PYTHONPATH.")
    sys.exit(1)

# EAR Threshold for Blink Detection
BLINK_THRESHOLD = 0.20

def draw_hud(frame, fps, landmarks, is_blinking) -> None:
    """Draws a Heads-Up Display (HUD) on the frame."""
    h, w = frame.shape[:2]

    # HUD Background
    cv2.rectangle(frame, (10, 10), (320, 260), (0, 0, 0), -1)
    cv2.rectangle(frame, (10, 10), (320, 260), (200, 200, 200), 2)

    # Title
    cv2.putText(frame, "EyeNav Live Tracking Demo", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # FPS
    cv2.putText(frame, f"FPS: {fps:.1f}", (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # EAR Values
    cv2.putText(frame, f"Left EAR:  {landmarks.left_ear:.3f}", (20, 95),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(frame, f"Right EAR: {landmarks.right_ear:.3f}", (20, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # --- New Metrics ---
    # Eyebrows
    brow_state = "NEUTRAL"
    if landmarks.brow_raise > 0.4: brow_state = "RAISED"
    elif landmarks.brow_raise < -0.2: brow_state = "FURROWED / LOWERED"
    cv2.putText(frame, f"Eyebrows: {brow_state} ({landmarks.brow_raise:.2f})", (20, 155),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

    # Gaze X
    gaze_x_dir = "CENTER"
    if landmarks.gaze_x > 0.15: gaze_x_dir = "RIGHT"
    elif landmarks.gaze_x < -0.15: gaze_x_dir = "LEFT"
    cv2.putText(frame, f"Gaze X:   {gaze_x_dir} ({landmarks.gaze_x:.2f})", (20, 185),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    # Gaze Y
    gaze_y_dir = "CENTER"
    if landmarks.gaze_y > 0.15: gaze_y_dir = "DOWN"
    elif landmarks.gaze_y < -0.15: gaze_y_dir = "UP"
    cv2.putText(frame, f"Gaze Y:   {gaze_y_dir} ({landmarks.gaze_y:.2f})", (20, 210),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    # Blink Alert
    if is_blinking:
        cv2.putText(frame, "BLINK DETECTED", (20, 245),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        # Also flash big text in center
        cv2.putText(frame, "BLINK!", (w//2 - 100, h//2),
                    cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 0, 255), 4)

def draw_eye_mesh(frame, points, indices, color=(0, 255, 0)) -> None:
    """Draws the contour of the eye."""
    h, w = frame.shape[:2]
    pts = []
    for idx in indices:
        x, y = int(points[idx][0] * w), int(points[idx][1] * h)
        pts.append((x, y))

    pts = np.array(pts, np.int32)
    pts = pts.reshape((-1, 1, 2))
    cv2.polylines(frame, [pts], True, color, 1)

def draw_pupil(frame, pupil_norm, color=(0, 255, 255)) -> None:
    """Draws a crosshair on the pupil."""
    h, w = frame.shape[:2]
    x, y = int(pupil_norm[0] * w), int(pupil_norm[1] * h)

    cv2.circle(frame, (x, y), 3, color, -1)
    cv2.line(frame, (x - 10, y), (x + 10, y), color, 1)
    cv2.line(frame, (x, y - 10), (x, y + 10), color, 1)

def get_valid_camera():
    """Scans for a valid camera that doesn't just return black frames."""
    print("Scanning for a valid webcam...")
    for index in range(4): # Try indices 0, 1, 2, 3
        # Use CAP_DSHOW on Windows for better webcam compatibility
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW) if sys.platform.startswith('win') else cv2.VideoCapture(index)

        if not cap.isOpened():
            cap.release()
            continue

        # Read a few frames to let the camera warm up
        for _ in range(5):
            ret, frame = cap.read()

        if ret and frame is not None:
            # Check if the frame is completely black (sum of all pixels is 0)
            if np.sum(frame) > 0:
                print(f"Found valid camera at index {index} (Resolution: {frame.shape[1]}x{frame.shape[0]})")
                return cap

        cap.release()

    return None

def main() -> None:
    print("Initializing EyeNav FaceMesh Tracker...")
    extractor = FaceLandmarkExtractor(max_faces=1)

    cap = get_valid_camera()

    if cap is None or not cap.isOpened():
        print("Error: Could not find a working webcam. Are you sure it's plugged in and not used by another app?")
        return

    print("\n--- EyeNav Live Tracking Started ---")
    print("Press 'q' to quit.")

    prev_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Flip frame horizontally for a mirror effect
            frame = cv2.flip(frame, 1)

            # Convert to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Extract landmarks
            landmarks = extractor.process_frame(rgb_frame)

            # FPS Calculation
            curr_time = time.time()
            fps = 1.0 / (curr_time - prev_time)
            prev_time = curr_time

            if landmarks:
                # Determine blink state
                is_blinking = (landmarks.left_ear < BLINK_THRESHOLD) and (landmarks.right_ear < BLINK_THRESHOLD)
                eye_color = (0, 0, 255) if is_blinking else (0, 255, 0)

                # Draw meshes
                draw_eye_mesh(frame, landmarks.raw_points, LEFT_EYE_INDICES, eye_color)
                draw_eye_mesh(frame, landmarks.raw_points, RIGHT_EYE_INDICES, eye_color)

                # Draw pupils if not blinking
                if not is_blinking:
                    draw_pupil(frame, landmarks.left_pupil)
                    draw_pupil(frame, landmarks.right_pupil)

                draw_hud(frame, fps, landmarks, is_blinking)
            else:
                # Need dummy landmarks for HUD
                from backend.eyenav.vision.landmarks import EyeLandmarks
                dummy = EyeLandmarks(0, 0, (0,0), (0,0), np.zeros((478,2)), 0, 0, 0)
                draw_hud(frame, fps, dummy, False)
                h, w = frame.shape[:2]
                cv2.putText(frame, "NO FACE DETECTED", (w//2 - 150, h//2),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

            # Show output
            cv2.imshow("EyeNav - Gaze Tracking Prototype", frame)

            # Quit on 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        print("Cleaning up...")
        cap.release()
        cv2.destroyAllWindows()
        extractor.close()

if __name__ == "__main__":
    main()
