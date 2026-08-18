#!/usr/bin/env python3
"""EyeNav Desktop Launcher.
=======================

Runs the EyeNav vision engine in OS-Control Mode.
Takes over the physical mouse via absolute gaze mapping.

Usage:
    python scripts/run_desktop.py              # Normal launch (loads saved calibration)
    python scripts/run_desktop.py --calibrate  # Force recalibration before launch
    python scripts/run_desktop.py --record     # Record telemetry to CSV

Calibration:
    On first launch, or with --calibrate, a fullscreen 9-point calibration
    session runs before cursor control begins. Calibration is saved to
    ~/.eyenav/gaze_calibration.json and loaded automatically on subsequent runs.

Failsafe:
    Drag the physical mouse to any corner of the screen to trigger the PyAutoGUI
    failsafe and kill the process immediately.
"""

import argparse
import logging
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import pyautogui

# Add project root to path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.eyenav.cursor.calibration import CalibrationSession
from backend.eyenav.cursor.mapping import GazeScreenMapper
from backend.eyenav.desktop import DesktopController
from backend.eyenav.overlay import HUDOverlay
from backend.eyenav.telemetry import TelemetryLogger
from backend.eyenav.vision.landmarks import FaceLandmarkExtractor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("EyeNav-Desktop")


def get_valid_camera() -> cv2.VideoCapture | None:
    """Scan for a working webcam with a non-black feed."""
    logger.info("Scanning for valid webcam…")
    for index in range(4):
        backend = cv2.CAP_DSHOW if sys.platform.startswith("win") else cv2.CAP_ANY
        cap = cv2.VideoCapture(index, backend)
        if not cap.isOpened():
            cap.release()
            continue
        # Warm up: read a few frames
        for _ in range(5):
            ret, frame = cap.read()
        if ret and frame is not None and np.sum(frame) > 0:
            logger.info("Found valid camera at index %d.", index)
            return cap
        cap.release()
    return None


def run_calibration(extractor: FaceLandmarkExtractor, cap: cv2.VideoCapture) -> GazeScreenMapper:
    """Run the 9-point calibration session and return a fitted mapper."""
    sw, sh = pyautogui.size()
    mapper = GazeScreenMapper(sw, sh)

    logger.info("Starting 9-point calibration session…")
    session = CalibrationSession(extractor, cap, randomize=True)
    data = session.run()

    if not data.success:
        logger.error("Calibration failed: %s", data.error)
        logger.info("Starting without calibration — cursor will be inactive.")
        return mapper

    try:
        mapper.fit(data.gaze_samples, data.screen_samples)
        mapper.save()
        logger.info("Calibration complete and saved.")
    except Exception as e:
        logger.error("Failed to fit calibration model: %s", e)

    return mapper


def main() -> None:
    parser = argparse.ArgumentParser(description="EyeNav OS Desktop Controller")
    parser.add_argument(
        "--calibrate", action="store_true",
        help="Force a new calibration session before launching.",
    )
    parser.add_argument(
        "--no-record", action="store_true",
        help="Disable recording raw eye telemetry to a CSV file.",
    )
    args = parser.parse_args()

    print("=" * 55)
    print("         EyeNav OS Desktop Controller")
    print("=" * 55)
    print("\nWARNING: This script will take over your physical mouse.")
    print("Drag the mouse to any corner of the screen to trigger")
    print("the PyAutoGUI Failsafe and stop the script.\n")

    cap = get_valid_camera()
    if cap is None:
        logger.error("No working webcam found. Exiting.")
        sys.exit(1)

    extractor = FaceLandmarkExtractor(max_faces=1)

    # ── Calibration ──────────────────────────────────────────────────────────
    sw, sh = pyautogui.size()
    mapper = GazeScreenMapper(sw, sh)

    if args.calibrate:
        print("\n[Calibration] Forced recalibration requested.")
        mapper = run_calibration(extractor, cap)
    elif mapper.load():
        print("\n[Calibration] Loaded saved calibration profile.")
    else:
        print("\n[Calibration] No saved calibration found. Starting calibration session…")
        mapper = run_calibration(extractor, cap)

    if mapper.is_fitted:
        print("\n✅ Calibration active — cursor will follow your gaze.")
    else:
        print("\n⚠️  No calibration — cursor will not move. Re-run with --calibrate.")

    print("\nStarting in 3 seconds…")
    time.sleep(3)

    # ── Main loop ─────────────────────────────────────────────────────────────
    telemetry = TelemetryLogger() if not args.no_record else None
    controller = DesktopController(mapper=mapper, telemetry_logger=telemetry)
    overlay = HUDOverlay()

    controller.on_lock_toggled = overlay.set_status
    controller.on_blink_detected = lambda: overlay.flash("⚡ BLINK", "#FFFF00")

    logger.info("Entering OS control loop. Ctrl+C or mouse corner to stop.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.error("Lost camera feed.")
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            landmarks = extractor.process_frame(rgb)

            if landmarks is not None:
                controller.update(landmarks)

            overlay.update()
            time.sleep(0.01)  # ~30fps

    except pyautogui.FailSafeException:
        print("\n\n!!! FAILSAFE TRIGGERED !!!")
        print("Control returned to user.")
    except KeyboardInterrupt:
        print("\n\nShutting down EyeNav Desktop…")
    finally:
        overlay.destroy()
        cap.release()
        try:
            extractor.close()
        except Exception:
            pass
        if telemetry is not None:
            telemetry.close()
        # Save any online adaptation that happened during the session
        if controller.is_calibrated:
            controller.mapper.save()
            logger.info("Calibration profile saved on exit.")


if __name__ == "__main__":
    main()
