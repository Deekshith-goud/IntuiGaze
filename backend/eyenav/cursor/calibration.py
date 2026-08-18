"""9-point calibration session for the gaze cursor system.

Runs a fullscreen Tkinter overlay displaying calibration targets one at a time.
Collects raw gaze feature vectors while the user fixates each target.
The resulting data is passed to GazeScreenMapper.fit().

Protocol:
    1. 9 targets arranged in a 3×3 grid, normalized to [0.1, 0.9] so targets
       are not at extreme screen edges (which cause discomfort).
    2. Each target is shown for SETTLE_FRAMES (discarded) + COLLECT_FRAMES.
    3. The median feature vector per target is used (robust to blinks/noise).
    4. If insufficient valid frames are collected for a target, it is retried.

Target sequence is randomized to prevent fixation bias patterns.
Press ESC at any time to cancel.
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# 9 calibration targets (normalized screen coordinates)
_CALIBRATION_POINTS_NORM: list[tuple[float, float]] = [
    (0.1, 0.1), (0.5, 0.1), (0.9, 0.1),
    (0.1, 0.5), (0.5, 0.5), (0.9, 0.5),
    (0.1, 0.9), (0.5, 0.9), (0.9, 0.9),
]

_SETTLE_FRAMES = 25    # Discard these frames while eye is settling (≈0.8s at 30fps)
_COLLECT_FRAMES = 50   # Frames to collect per target (≈1.7s at 30fps)
_MIN_VALID_FRAMES = 25  # Minimum to accept a target (retry if below)


@dataclass
class CalibrationData:
    """Output of a completed calibration session.

    Attributes:
        gaze_samples: Shape (N, 6). One row per calibration point collected.
        screen_samples: Shape (N, 2). Corresponding screen pixel coordinates.
        screen_width: Monitor width in pixels.
        screen_height: Monitor height in pixels.
        success: Whether the session completed without errors.
        error: Error message if success=False.
    """
    gaze_samples: np.ndarray
    screen_samples: np.ndarray
    screen_width: int
    screen_height: int
    success: bool = True
    error: str = ""


def _extract_features(landmarks) -> np.ndarray | None:
    """Extract 6-d feature vector from EyeLandmarks for GazeScreenMapper."""
    lx, ly = landmarks.left_pupil
    rx, ry = landmarks.right_pupil
    return np.array(
        [lx, ly, rx, ry, landmarks.head_yaw, landmarks.head_pitch],
        dtype=np.float32,
    )


class CalibrationSession:
    """Runs a fullscreen interactive 9-point calibration session.

    Displays one colored target dot at a time. Waits for gaze to settle,
    then records gaze feature vectors. Uses median across frames for
    robustness to outliers and micro-saccades.

    Args:
        extractor: An initialized FaceLandmarkExtractor instance.
        cap: An open OpenCV VideoCapture instance.
        randomize: Whether to randomize target order (recommended: True).

    Example::

        session = CalibrationSession(extractor, cap)
        data = session.run()
        if data.success:
            mapper.fit(data.gaze_samples, data.screen_samples)
            mapper.save()
    """

    def __init__(self, extractor, cap, randomize: bool = True) -> None:
        self._extractor = extractor
        self._cap = cap
        self._randomize = randomize

    def run(self) -> CalibrationData:
        """Run the calibration session and return collected data.

        This call blocks until the session is complete or cancelled.
        """
        import tkinter as tk

        import cv2

        points = list(_CALIBRATION_POINTS_NORM)
        if self._randomize:
            random.shuffle(points)

        root = tk.Tk()
        root.attributes("-fullscreen", True)
        root.attributes("-topmost", True)
        root.configure(bg="black")
        root.title("EyeNav — Gaze Calibration")
        root.focus_force()

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()

        canvas = tk.Canvas(root, bg="black", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        status_var = tk.StringVar(value="")
        progress_var = tk.StringVar(value="")
        tk.Label(root, textvariable=status_var, fg="white", bg="black",
                 font=("Arial", 20)).place(relx=0.5, rely=0.93, anchor="center")
        tk.Label(root, textvariable=progress_var, fg="#00FFAA", bg="black",
                 font=("Arial", 15)).place(relx=0.5, rely=0.97, anchor="center")

        # Mutable state shared between outer scope and Tkinter callbacks
        state = {
            "point_idx": 0,
            "frame_count": 0,
            "buffer": [],
            "gaze_data": [],
            "screen_data": [],
            "cancelled": False,
            "done": False,
        }

        def draw_target(nx: float, ny: float, color: str) -> None:
            canvas.delete("target")
            px, py = int(nx * sw), int(ny * sh)
            for r, fill in [(28, "white"), (14, color), (5, "black")]:
                canvas.create_oval(px - r, py - r, px + r, py + r,
                                   fill=fill, outline=fill, tags="target")

        def on_escape(_event) -> None:
            state["cancelled"] = True
            root.destroy()

        root.bind("<Escape>", on_escape)

        def tick() -> None:
            if state["cancelled"] or state["done"]:
                if not state["cancelled"]:
                    root.destroy()
                return

            idx = state["point_idx"]
            if idx >= len(points):
                state["done"] = True
                root.destroy()
                return

            nx, ny = points[idx]
            fc = state["frame_count"]
            total_needed = _SETTLE_FRAMES + _COLLECT_FRAMES

            progress_var.set(f"Target {idx + 1} / {len(points)}")

            # Visual feedback: amber while settling, green while collecting
            if fc < _SETTLE_FRAMES:
                draw_target(nx, ny, "#FFA500")
                status_var.set("Move your gaze to the dot…")
            else:
                draw_target(nx, ny, "#00FF00")
                remaining = total_needed - fc
                status_var.set(f"Hold steady… ({remaining} frames left)")

            # Capture frame and extract gaze features
            ret, frame = self._cap.read()
            if ret and frame is not None:
                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                lm = self._extractor.process_frame(rgb)
                if lm is not None and fc >= _SETTLE_FRAMES:
                    feats = _extract_features(lm)
                    if feats is not None:
                        state["buffer"].append(feats)

            state["frame_count"] += 1

            if fc >= total_needed - 1:
                buf = state["buffer"]
                if len(buf) >= _MIN_VALID_FRAMES:
                    median_feats = np.median(np.array(buf), axis=0)
                    state["gaze_data"].append(median_feats)
                    state["screen_data"].append(
                        np.array([nx * sw, ny * sh], dtype=np.float64)
                    )
                    logger.info(
                        "Calibration point %d/%d accepted (%d frames). screen=(%.0f, %.0f)",
                        idx + 1, len(points), len(buf), nx * sw, ny * sh,
                    )
                    state["point_idx"] += 1
                else:
                    logger.warning(
                        "Calibration point %d: only %d valid frames. Retrying.",
                        idx + 1, len(buf),
                    )
                state["frame_count"] = 0
                state["buffer"] = []

            root.after(33, tick)  # ~30fps

        # Brief intro screen before starting
        canvas.create_text(
            sw // 2, sh // 2,
            text="Gaze Calibration\n\nLook at each dot as it appears.\nKeep your head still.\n\nStarting in 2 seconds…\n\n(Press ESC to cancel)",
            fill="white", font=("Arial", 26), justify="center",
        )
        root.after(2000, tick)
        root.mainloop()

        if state["cancelled"]:
            return CalibrationData(
                gaze_samples=np.zeros((0, 6)),
                screen_samples=np.zeros((0, 2)),
                screen_width=sw, screen_height=sh,
                success=False, error="Calibration cancelled by user.",
            )

        n = len(state["gaze_data"])
        if n < 6:
            return CalibrationData(
                gaze_samples=np.zeros((0, 6)),
                screen_samples=np.zeros((0, 2)),
                screen_width=sw, screen_height=sh,
                success=False,
                error=f"Only {n} calibration points collected (need ≥ 6).",
            )

        return CalibrationData(
            gaze_samples=np.array(state["gaze_data"], dtype=np.float32),
            screen_samples=np.array(state["screen_data"], dtype=np.float64),
            screen_width=sw, screen_height=sh,
            success=True,
        )
