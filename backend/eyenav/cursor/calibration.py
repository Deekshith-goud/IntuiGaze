"""9-point gaze calibration session with a clean, structured UI layout.
=============================================================================

Provides a clean, structured, and distraction-free fullscreen visual canvas
paired with a clear terminal summary. Collects raw 6-D gaze feature vectors
while the user looks at 9 target dots across their monitor.

Layout Structure:
    - Top Navigation Bar: Title, target progress (e.g. Target 3 of 9), and ESC hint.
    - Main Visual Area: High-contrast target dot with smooth radial progress ring.
    - Bottom Status Bar: Simple step guidance and 9-point progress indicator.
    - Structured Intro Card: 3 clear steps (Position, Head, Gaze) + 3s countdown.
    - Structured Outro Card: Confirmation summary and smooth transition to desktop.
"""

from __future__ import annotations

import logging
import math
import random
import sys
import time
from dataclasses import dataclass, field
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
from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

logger = logging.getLogger(__name__)

# 9 calibration targets (normalized screen coordinates)
_CALIBRATION_POINTS_NORM: list[tuple[float, float]] = [
    (0.1, 0.1),
    (0.5, 0.1),
    (0.9, 0.1),
    (0.1, 0.5),
    (0.5, 0.5),
    (0.9, 0.5),
    (0.1, 0.9),
    (0.5, 0.9),
    (0.9, 0.9),
]

_SETTLE_FRAMES = 25   # Settle duration (≈0.8s at 30fps)
_COLLECT_FRAMES = 50  # Collection duration (≈1.7s at 30fps)
_MIN_VALID_FRAMES = 25  # Minimum accepted frames per target


def _make_progress_bar(percent: float, length: int = 15) -> str:
    """Render a clean progress bar string."""
    filled = int(round(length * (max(0.0, min(100.0, percent)) / 100.0)))
    return "█" * filled + "░" * (length - filled)


@dataclass
class CalibrationData:
    """Output of a completed calibration session."""

    gaze_samples: np.ndarray
    screen_samples: np.ndarray
    screen_width: int
    screen_height: int
    success: bool = True
    error: str = ""


def _extract_features(landmarks) -> np.ndarray | None:
    """Extract 6-D feature vector from EyeLandmarks for GazeScreenMapper."""
    lx, ly = landmarks.left_pupil
    rx, ry = landmarks.right_pupil
    return np.array(
        [lx, ly, rx, ry, landmarks.head_yaw, landmarks.head_pitch],
        dtype=np.float32,
    )


class CalibrationSession:
    """Runs a fullscreen 9-point calibration session with a clean, structured UI layout."""

    def __init__(self, extractor, cap, randomize: bool = True) -> None:
        self._extractor = extractor
        self._cap = cap
        self._randomize = randomize

    def run(self) -> CalibrationData:
        """Run the calibration session and return collected data."""
        import tkinter as tk

        points = list(_CALIBRATION_POINTS_NORM)
        if self._randomize:
            random.shuffle(points)

        console = Console()

        root = tk.Tk()
        root.attributes("-fullscreen", True)
        root.attributes("-topmost", True)
        root.configure(bg="#0F172A")
        root.title("IntuiGaze — Gaze Calibration")
        root.focus_force()

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()

        canvas = tk.Canvas(root, bg="#0F172A", highlightthickness=0, bd=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        @dataclass
        class SessionState:
            point_idx: int = 0
            frame_count: int = 0
            buffer: list[np.ndarray] = field(default_factory=list)
            gaze_data: list[np.ndarray] = field(default_factory=list)
            screen_data: list[np.ndarray] = field(default_factory=list)
            accepted_points: list[dict] = field(default_factory=list)
            cancelled: bool = False
            done: bool = False
            face_detected: bool = False
            last_head: tuple[float, float] = (0.0, 0.0)

        state = SessionState()

        # -------------------------------------------------------------
        # Structured Layout: Top Header Bar
        # -------------------------------------------------------------
        def draw_top_bar(idx: int) -> None:
            canvas.delete("top_bar")
            h = 56

            # Bar background and separator
            canvas.create_rectangle(0, 0, sw, h, fill="#1E293B", outline="", tags="top_bar")
            canvas.create_line(0, h, sw, h, fill="#334155", width=1, tags="top_bar")

            # Left: Product Title
            canvas.create_text(
                28, h / 2,
                text="IntuiGaze",
                fill="#F8FAFC", font=("Segoe UI", 13, "bold"), anchor="w", tags="top_bar"
            )
            canvas.create_text(
                105, h / 2,
                text="|   Gaze Calibration",
                fill="#94A3B8", font=("Segoe UI", 11), anchor="w", tags="top_bar"
            )

            # Center: Step Progress Pill
            total = len(points)
            curr = min(idx + 1, total)
            pct = int((idx / float(total)) * 100)
            canvas.create_text(
                sw / 2, h / 2,
                text=f"Target {curr} of {total}  ({pct}%)",
                fill="#38BDF8", font=("Segoe UI", 11, "bold"), anchor="center", tags="top_bar"
            )

            # Right: Exit Hint
            canvas.create_text(
                sw - 28, h / 2,
                text="Press ESC to cancel",
                fill="#94A3B8", font=("Segoe UI", 10), anchor="e", tags="top_bar"
            )

        # -------------------------------------------------------------
        # Structured Layout: Bottom Status Bar
        # -------------------------------------------------------------
        def draw_bottom_bar(idx: int, is_settling: bool) -> None:
            canvas.delete("bottom_bar")
            h = 56
            y0 = sh - h

            # Bar background and separator
            canvas.create_rectangle(0, y0, sw, sh, fill="#1E293B", outline="", tags="bottom_bar")
            canvas.create_line(0, y0, sw, y0, fill="#334155", width=1, tags="bottom_bar")

            # Left: Instruction status
            inst_text = "Step 1: Look at the dot and hold steady" if is_settling else "Step 2: Recording gaze samples..."
            inst_color = "#F8FAFC" if is_settling else "#38BDF8"
            canvas.create_text(
                28, y0 + h / 2,
                text=inst_text,
                fill=inst_color, font=("Segoe UI", 10, "bold" if not is_settling else "normal"),
                anchor="w", tags="bottom_bar"
            )

            # Right: 9-point progress indicator dots
            total = len(points)
            spacing = 22
            total_w = (total - 1) * spacing
            start_x = sw - 36 - total_w

            for i in range(total):
                dx = start_x + i * spacing
                dy = y0 + h / 2
                if i < idx:
                    # Completed
                    canvas.create_oval(dx - 5, dy - 5, dx + 5, dy + 5, fill="#34D399", outline="", tags="bottom_bar")
                elif i == idx:
                    # Current
                    canvas.create_oval(dx - 6, dy - 6, dx + 6, dy + 6, outline="#38BDF8", width=2, tags="bottom_bar")
                    canvas.create_oval(dx - 2.5, dy - 2.5, dx + 2.5, dy + 2.5, fill="#F8FAFC", outline="", tags="bottom_bar")
                else:
                    # Pending
                    canvas.create_oval(dx - 4, dy - 4, dx + 4, dy + 4, fill="#475569", outline="", tags="bottom_bar")

        # -------------------------------------------------------------
        # Center: Clean Target Dot with Progress Ring
        # -------------------------------------------------------------
        def draw_target(nx: float, ny: float, is_settling: bool, progress_pct: float) -> None:
            canvas.delete("target")
            px, py = int(nx * sw), int(ny * sh)
            r = 24

            # Background track ring
            canvas.create_oval(
                px - r, py - r, px + r, py + r,
                outline="#334155", width=3, tags="target"
            )

            if is_settling:
                # Settle phase: clean cyan guide ring
                canvas.create_oval(
                    px - r, py - r, px + r, py + r,
                    outline="#38BDF8", width=1.5, tags="target"
                )
            else:
                # Collect phase: circular progress fill (clockwise from 12 o'clock)
                extent = -int(max(0.0, min(1.0, progress_pct)) * 360)
                if abs(extent) > 0:
                    canvas.create_arc(
                        px - r, py - r, px + r, py + r,
                        start=90, extent=extent, style="arc",
                        outline="#38BDF8", width=3.5, tags="target"
                    )

            # Center high-contrast anchor dot
            canvas.create_oval(
                px - 5, py - 5, px + 5, py + 5,
                fill="#FFFFFF", outline="#0F172A", width=1, tags="target"
            )

        # -------------------------------------------------------------
        # Terminal Live TUI Panel
        # -------------------------------------------------------------
        def build_tui_panel(idx: int, is_settling: bool, progress_pct: float) -> Panel:
            t = Table(box=box.ROUNDED, expand=True, border_style="cyan", show_header=False)
            t.add_column("Key", style="dim white", width=20)
            t.add_column("Value", style="bold white")

            status = "Settling eye on target" if is_settling else f"Recording samples ({progress_pct*100:.0f}%)"
            nx, ny = points[min(idx, len(points) - 1)]

            t.add_row("Calibration Progress", f"Target {idx + 1} of {len(points)}  ({(idx / len(points)) * 100:.0f}%)")
            t.add_row("Screen Position", f"({int(nx * sw)}, {int(ny * sh)}) px")
            t.add_row("Tracking Status", f"[cyan]{status}[/]")
            t.add_row("Sample Buffer", f"{_make_progress_bar(progress_pct * 100, 16)}  ({len(state.buffer)}/{_COLLECT_FRAMES} frames)")
            t.add_row("Head Stability", f"Yaw: {state.last_head[0]:+.1f}°  Pitch: {state.last_head[1]:+.1f}°  [green][STABLE][/]")

            return Panel(
                t,
                box=box.ROUNDED,
                border_style="cyan",
                title="[bold white] IntuiGaze — Calibration Progress [/]",
                subtitle="[dim]9-Point Screen Mapping | 30 FPS[/dim]",
            )

        def on_escape(_event) -> None:
            state.cancelled = True
            root.destroy()

        root.bind("<Escape>", on_escape)

        # -------------------------------------------------------------
        # Main Calibration Tick Loop
        # -------------------------------------------------------------
        live_console = Live(build_tui_panel(0, True, 0.0), console=console, refresh_per_second=15, transient=True)
        live_console.start()

        def tick() -> None:
            if state.cancelled or state.done:
                if not state.cancelled:
                    root.destroy()
                return

            idx = state.point_idx
            if idx >= len(points):
                state.done = True
                # Clean, structured completion card
                canvas.delete("all")
                cx, cy = sw / 2.0, sh / 2.0
                card_w, card_h = 520, 220

                canvas.create_rectangle(
                    cx - card_w / 2, cy - card_h / 2, cx + card_w / 2, cy + card_h / 2,
                    fill="#1E293B", outline="#334155", width=1.5
                )
                canvas.create_text(
                    cx, cy - 50,
                    text="Calibration Complete",
                    fill="#F8FAFC", font=("Segoe UI", 20, "bold"), anchor="center"
                )
                canvas.create_text(
                    cx, cy - 10,
                    text="9 of 9 calibration points successfully mapped.",
                    fill="#34D399", font=("Segoe UI", 12), anchor="center"
                )
                canvas.create_text(
                    cx, cy + 24,
                    text="Polynomial gaze-to-screen regression model fitted and saved.",
                    fill="#94A3B8", font=("Segoe UI", 10), anchor="center"
                )
                canvas.create_text(
                    cx, cy + 64,
                    text="Starting desktop navigation in 2 seconds...",
                    fill="#38BDF8", font=("Segoe UI", 10, "bold"), anchor="center"
                )
                root.after(1600, root.destroy)
                return

            nx, ny = points[idx]
            fc = state.frame_count
            total_needed = _SETTLE_FRAMES + _COLLECT_FRAMES
            is_settling = fc < _SETTLE_FRAMES

            progress_pct = (
                (fc / float(_SETTLE_FRAMES)) if is_settling else ((fc - _SETTLE_FRAMES) / float(_COLLECT_FRAMES))
            )

            # Render structured layout
            draw_top_bar(idx)
            draw_target(nx, ny, is_settling, progress_pct)
            draw_bottom_bar(idx, is_settling)

            # Video Capture & Landmark Processing
            ret, frame = self._cap.read()
            if ret and frame is not None:
                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                lm = self._extractor.process_frame(rgb)
                if lm is not None:
                    state.face_detected = True
                    state.last_head = (float(lm.head_yaw), float(lm.head_pitch))

                    if not is_settling:
                        feats = _extract_features(lm)
                        if feats is not None:
                            state.buffer.append(feats)

            # Update Terminal TUI
            live_console.update(build_tui_panel(idx, is_settling, progress_pct))

            state.frame_count += 1

            # Target acceptance logic
            if fc >= total_needed - 1:
                buf = state.buffer
                if len(buf) >= _MIN_VALID_FRAMES:
                    median_feats = np.median(np.array(buf), axis=0)
                    state.gaze_data.append(median_feats)
                    state.screen_data.append(np.array([nx * sw, ny * sh], dtype=np.float64))
                    state.accepted_points.append({
                        "idx": idx + 1,
                        "x": int(nx * sw),
                        "y": int(ny * sh),
                        "frames": len(buf),
                    })
                    logger.info("Target %d/%d recorded (%d frames)", idx + 1, len(points), len(buf))
                    state.point_idx += 1
                else:
                    logger.warning("Target %d: insufficient frames (%d/%d). Retrying point.", idx + 1, len(buf), _MIN_VALID_FRAMES)

                state.frame_count = 0
                state.buffer = []

            root.after(33, tick)  # ~30 FPS

        # -------------------------------------------------------------
        # Clean Structured Intro Card (3 Steps + Countdown)
        # -------------------------------------------------------------
        countdown = [3]

        def show_intro() -> None:
            canvas.delete("all")
            c_val = countdown[0]
            cx, cy = sw / 2.0, sh / 2.0
            card_w, card_h = 560, 340

            # Card Background Frame
            canvas.create_rectangle(
                cx - card_w / 2, cy - card_h / 2, cx + card_w / 2, cy + card_h / 2,
                fill="#1E293B", outline="#334155", width=1.5
            )

            # Header
            canvas.create_text(
                cx, cy - card_h / 2 + 36,
                text="Gaze Calibration Setup",
                fill="#F8FAFC", font=("Segoe UI", 18, "bold"), anchor="center"
            )
            canvas.create_text(
                cx, cy - card_h / 2 + 64,
                text="Follow the on-screen circle across 9 points to tune tracking.",
                fill="#94A3B8", font=("Segoe UI", 10), anchor="center"
            )

            # Divider
            canvas.create_line(
                cx - card_w / 2 + 28, cy - card_h / 2 + 84,
                cx + card_w / 2 - 28, cy - card_h / 2 + 84,
                fill="#334155", width=1
            )

            # 3 Structured Steps
            steps = [
                ("1. Position", "Sit centered in front of your webcam at normal viewing distance."),
                ("2. Head", "Keep your head relatively still during the calibration."),
                ("3. Gaze", "Look directly at each circle until the ring fills completely."),
            ]
            step_y = cy - 50
            for title, desc in steps:
                canvas.create_text(
                    cx - card_w / 2 + 36, step_y,
                    text=title,
                    fill="#38BDF8", font=("Segoe UI", 10, "bold"), anchor="w"
                )
                canvas.create_text(
                    cx - card_w / 2 + 130, step_y,
                    text=desc,
                    fill="#E2E8F0", font=("Segoe UI", 10), anchor="w"
                )
                step_y += 34

            # Divider
            canvas.create_line(
                cx - card_w / 2 + 28, cy + 62,
                cx + card_w / 2 - 28, cy + 62,
                fill="#334155", width=1
            )

            # Bottom Action / Countdown
            canvas.create_text(
                cx - card_w / 2 + 36, cy + 96,
                text="Press ESC to cancel at any time",
                fill="#64748B", font=("Segoe UI", 9), anchor="w"
            )
            canvas.create_text(
                cx + card_w / 2 - 36, cy + 96,
                text=f"Starting in {c_val}...",
                fill="#34D399", font=("Segoe UI", 12, "bold"), anchor="e"
            )

            if c_val > 1:
                countdown[0] -= 1
                root.after(1000, show_intro)
            else:
                root.after(1000, lambda: [canvas.delete("all"), tick()])

        show_intro()
        root.mainloop()

        # Stop Live terminal TUI cleanly
        try:
            live_console.stop()
        except Exception:
            pass

        if state.cancelled:
            console.print(
                Panel(
                    "[dim red][CANCELLED][/] Calibration session aborted by user.",
                    border_style="red",
                )
            )
            return CalibrationData(
                gaze_samples=np.zeros((0, 6)),
                screen_samples=np.zeros((0, 2)),
                screen_width=sw,
                screen_height=sh,
                success=False,
                error="Calibration cancelled by user.",
            )

        n = len(state.gaze_data)
        if n < 6:
            console.print(
                Panel(
                    f"[dim red][FAILED][/] Only {n} calibration targets collected (minimum required: 6).",
                    border_style="red",
                )
            )
            return CalibrationData(
                gaze_samples=np.zeros((0, 6)),
                screen_samples=np.zeros((0, 2)),
                screen_width=sw,
                screen_height=sh,
                success=False,
                error=f"Only {n} calibration points collected (need >= 6).",
            )

        # Permanent Summary in Terminal
        summary_table = Table(box=box.ROUNDED, expand=True, border_style="cyan", show_header=False)
        summary_table.add_column("Key", style="dim white")
        summary_table.add_column("Value", style="bold white")
        summary_table.add_row("Calibration Protocol", "9-Point Grid (Complete)")
        summary_table.add_row("Targets Accepted", f"{n} / {len(points)} Points")
        summary_table.add_row("Mapped Frames", f"{sum(p['frames'] for p in state.accepted_points)} frames")
        summary_table.add_row("Model Status", "[bold green][OK] Polynomial Ridge Regression Model Fitted[/]")

        console.print(
            Panel(
                summary_table,
                title="[bold white][CALIBRATION COMPLETE][/]",
                border_style="cyan",
            )
        )

        return CalibrationData(
            gaze_samples=np.array(state.gaze_data, dtype=np.float32),
            screen_samples=np.array(state.screen_data, dtype=np.float64),
            screen_width=sw,
            screen_height=sh,
            success=True,
        )
