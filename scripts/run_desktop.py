#!/usr/bin/env python3
"""EyeNav Desktop Launcher.
=======================

Runs the EyeNav vision engine in OS-Control Mode.
Takes over the physical mouse via absolute gaze mapping.

Usage:
    python scripts/run_desktop.py              # Normal launch (loads saved calibration)
    python scripts/run_desktop.py --calibrate  # Force recalibration before launch
    python scripts/run_desktop.py --no-record  # Disable recording telemetry to CSV

Calibration:
    On first launch, or with --calibrate, a fullscreen 9-point calibration
    session runs before cursor control begins. Calibration is saved to
    ~/.eyenav/gaze_calibration.json and loaded automatically on subsequent runs.

Failsafe:
    Drag the physical mouse to any corner of the screen to trigger the PyAutoGUI
    failsafe and kill the process immediately.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

# Ensure UTF-8 output encoding across Windows consoles
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import cv2
import numpy as np
import pyautogui
from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

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
console = Console()


def get_valid_camera() -> cv2.VideoCapture | None:
    """Scan for a working webcam with a non-black feed."""
    logger.info("Scanning for valid webcam...")
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

    console.print(
        Panel(
            "[bold cyan]Starting 9-Point Gaze Calibration...[/]\n"
            "[dim]A structured fullscreen setup is now active. Follow the circle across your screen.[/dim]",
            box=box.ROUNDED,
            border_style="cyan",
        )
    )

    session = CalibrationSession(extractor, cap, randomize=True)
    data = session.run()

    if not data.success:
        console.print(
            Panel(
                f"[bold red][FAILED] Calibration uncompleted: {data.error}[/]\n"
                "[dim]Starting without calibration -- gaze cursor control will remain inactive.[/dim]",
                box=box.ROUNDED,
                border_style="red",
            )
        )
        return mapper

    try:
        mapper.fit(data.gaze_samples, data.screen_samples)
        mapper.save()
        console.print(
            Panel(
                "[bold bright_green][OK] Calibration fitted and saved to ~/.eyenav/gaze_calibration.json[/]\n"
                f"[dim]Accepted {len(data.gaze_samples)} targets across screen resolution ({sw}x{sh})[/dim]",
                box=box.ROUNDED,
                border_style="bright_green",
            )
        )
    except Exception as e:
        console.print(
            Panel(
                f"[bold red][ERROR] Failed to fit calibration model: {e}[/]",
                box=box.ROUNDED,
                border_style="red",
            )
        )

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
    parser.add_argument(
        "--invert-eyes", action="store_true",
        help="Invert eye gesture assignments (Left Eye = Primary Click, Right Eye = Context/Drag).",
    )
    args = parser.parse_args()

    # 1. Header Banner
    header_text = Text()
    header_text.append("INTUIGAZE // OS DESKTOP CONTROLLER\n", style="bold bright_cyan")
    header_text.append("Real-Time Hands-Free Navigation Engine • Closed-Loop Multi-Modal Control", style="dim white")
    console.print(
        Panel(
            Align.center(header_text),
            box=box.HEAVY,
            border_style="bright_cyan",
            subtitle="[dim]PyAutoGUI Active Mouse Takeover Subsystem[/dim]",
            subtitle_align="center",
        )
    )

    # 2. Safety Invariant & Gesture Matrix
    primary_eye = "LEFT EYE" if args.invert_eyes else "RIGHT EYE"
    secondary_eye = "RIGHT EYE" if args.invert_eyes else "LEFT EYE"

    console.print(
        Panel(
            "[bold bright_yellow][FAILSAFE ENGAGED][/]  •  [bold white]Active Gesture Matrix[/]\n\n"
            f"  • [bold white]{primary_eye} Wink:[/] Left Click (Select)      • [bold white]Double Wink:[/] Double Click\n"
            f"  • [bold white]{secondary_eye} Wink:[/] Right Click (Context Menu)   • [bold white]{secondary_eye} Hold 1s:[/] Drag & Drop Latch\n"
            "  • [bold white]Both Eyes Closed 2.0s:[/] Scroll Mode        • [bold white]Both Eyes Closed 3.5s:[/] Standby Mode\n"
            "  • [bold white]Brow Raise (>0.35):[/] Snap Fixation Anchor   • [bold bright_red]Corner of Screen:[/] Emergency Stop Failsafe",
            box=box.ROUNDED,
            border_style="yellow",
        )
    )

    cap = get_valid_camera()
    if cap is None:
        console.print("[bold red][ERROR] No working webcam detected. Exiting controller.[/]")
        sys.exit(1)

    extractor = FaceLandmarkExtractor(max_faces=1)

    # ── Calibration ──────────────────────────────────────────────────────────
    sw, sh = pyautogui.size()
    mapper = GazeScreenMapper(sw, sh)

    if args.calibrate:
        console.print("[bold cyan][CALIBRATION][/] Forced recalibration requested.")
        mapper = run_calibration(extractor, cap)
    elif mapper.load():
        console.print("[bold green][CALIBRATION][/] Loaded saved calibration profile from disk.")
    else:
        console.print("[bold yellow][CALIBRATION][/] No saved profile found. Initializing 9-point session...")
        mapper = run_calibration(extractor, cap)

    if mapper.is_fitted:
        console.print("[bold bright_green][OK] Calibration active -- gaze cursor control engaged.[/]")
    else:
        console.print("[bold yellow][WARN] No active calibration profile -- cursor tracking will remain idle. Re-run with --calibrate.[/]")

    console.print("[dim]Starting desktop actuation loop in 3 seconds...[/]")
    time.sleep(3)

    # ── Main loop ─────────────────────────────────────────────────────────────
    telemetry = TelemetryLogger() if not args.no_record else None
    controller = DesktopController(
        mapper=mapper,
        telemetry_logger=telemetry,
        invert_eyes=args.invert_eyes,
    )
    overlay = HUDOverlay()

    controller.on_lock_toggled = overlay.set_status
    controller.on_drag_mode_toggled = overlay.set_drag_mode
    controller.on_standby_toggled = overlay.set_standby_mode
    controller.on_gesture_event = lambda name, color: overlay.flash(name, color)
    controller.on_blink_detected = lambda: overlay.flash("[CLICK]", "#FBBF24")

    console.print(
        Panel(
            "[bold green][ONLINE][/] IntuiGaze Desktop Tracking Active  •  Gaze Cursor Engaged\n"
            "[dim]A floating status pill is active at the top of your display.\n"
            "Wink to click  •  Hold left 1s to drag  •  Both eyes 2s = scroll  •  Corner = Stop[/dim]",
            box=box.ROUNDED,
            border_style="green",
        )
    )

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
                overlay.set_face_detected(True)
            else:
                overlay.set_face_detected(False)

            overlay.update()
            time.sleep(0.01)  # ~30fps

    except pyautogui.FailSafeException:
        console.print("\n[bold red][FAILSAFE TRIGGERED] Mouse corner emergency stop activated. Control returned to user.[/]")
    except KeyboardInterrupt:
        console.print("\n[bold yellow][SHUTDOWN] Interrupted by user. Shutting down IntuiGaze Desktop...[/]")
    finally:
        try:
            pyautogui.mouseUp()
        except Exception:
            pass
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
