#!/usr/bin/env python3
"""EyeNav Desktop Launcher.
=======================

Runs the EyeNav vision engine in OS-Control Mode.
Takes over the physical mouse and keyboard via PyAutoGUI.
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

from backend.eyenav.desktop import DesktopController
from backend.eyenav.overlay import HUDOverlay
from backend.eyenav.telemetry import TelemetryLogger
from backend.eyenav.vision.landmarks import FaceLandmarkExtractor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("EyeNav-Desktop")

def get_valid_camera():
    """Scans for a valid non-black camera feed."""
    logger.info("Scanning for valid webcam...")
    for index in range(4):
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW) if sys.platform.startswith('win') else cv2.VideoCapture(index)
        if not cap.isOpened():
            cap.release()
            continue

        for _ in range(5):
            ret, frame = cap.read()

        if ret and frame is not None and np.sum(frame) > 0:
            logger.info(f"Found valid camera at index {index}")
            return cap
        cap.release()
    return None

def main() -> None:
    parser = argparse.ArgumentParser(description="EyeNav OS Desktop Controller")
    parser.add_argument("--record", action="store_true", help="Record raw eye telemetry to a CSV file.")
    args = parser.parse_args()

    print("="*50)
    print("         EyeNav OS Desktop Controller")
    print("="*50)
    print("\nWARNING: This script will take over your physical mouse.")
    print("If you lose control, forcefully drag your physical mouse")
    print("into any of the 4 extreme corners of your monitor to trigger")
    print("the PyAutoGUI Failsafe and crash the script.")
    print("\nStarting in 3 seconds...")
    time.sleep(3)

    cap = get_valid_camera()
    if cap is None:
        logger.error("Could not find a working webcam. Exiting.")
        sys.exit(1)

    try:
        extractor = FaceLandmarkExtractor(max_faces=1)

        telemetry = TelemetryLogger() if args.record else None
        controller = DesktopController(telemetry_logger=telemetry)

        overlay = HUDOverlay()

        # Wire up callbacks
        controller.on_lock_toggled = overlay.set_status
        controller.on_blink_detected = lambda: overlay.flash("⚡ BLINK", "#FFFF00")

        logger.info("Entering OS control loop. Press Ctrl+C in terminal to stop.")

        while True:
            ret, frame = cap.read()
            if not ret:
                logger.error("Lost camera feed.")
                break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            landmarks = extractor.process_frame(rgb_frame)

            if landmarks is not None:
                controller.update(landmarks)

            # Update Tkinter UI
            overlay.update()

            # Sleep slightly to maintain ~30fps and not fry the CPU
            time.sleep(0.01)

    except pyautogui.FailSafeException:
        print("\n\n!!! FAILSAFE TRIGGERED !!!")
        print("Control returned to user.")
    except KeyboardInterrupt:
        print("\n\nShutting down EyeNav Desktop...")
    finally:
        if 'overlay' in locals():
            overlay.destroy()
        if cap:
            cap.release()
        try:
            extractor.close()
        except:
            pass
        if 'telemetry' in locals() and telemetry is not None:
            telemetry.close()

if __name__ == "__main__":
    main()
