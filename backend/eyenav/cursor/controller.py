"""GazeCursorController — Absolute gaze-mapped cursor with adaptive smoothing.

This replaces the joystick-velocity model in the original DesktopController.

Pipeline per frame:
    EyeLandmarks
      → extract 6-feature vector (iris positions + head pose)
      → GazeScreenMapper.map()          # personalized polynomial map
      → SaccadeFixationDetector.update() # intent gate: saccade vs fixation
      → OneEuroFilter                    # adaptive jitter suppression
      → LagCompensationPredictor         # counteract camera→inference latency
      → pyautogui.moveTo()               # OS cursor

Cursor modes:
    CURSOR: Normal gaze-driven cursor (default).
    SCROLL: Long blink (>2s) toggles scroll mode; vertical gaze = scroll direction.

Click gesture:
    Double blink within 0.6s → left click.
    If the mapper is fitted, each click also feeds back into the online adapter.

Physical override:
    If the user moves the physical mouse > 15px from the last commanded
    position, eye tracking pauses for 2 seconds (same as original system).
"""

from __future__ import annotations

import logging
import platform
import time
from collections import deque

import numpy as np
import pyautogui
from backend.eyenav.cursor.filter import OneEuroFilter
from backend.eyenav.cursor.mapping import GazeScreenMapper
from backend.eyenav.cursor.predictor import LagCompensationPredictor
from backend.eyenav.cursor.saccade import GazeState, SaccadeFixationDetector
from backend.eyenav.vision.landmarks import EyeLandmarks

logger = logging.getLogger(__name__)

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.0  # Remove pyautogui's internal sleep for minimum latency

_BLINK_CLOSE_THRESHOLD = 0.68   # EAR below (baseline × this) = closed
_LONG_CLOSE_DURATION_S = 2.0    # Trigger scroll mode toggle
_DOUBLE_BLINK_WINDOW_S = 0.6    # Max gap between two blinks for double-blink
_CLICK_COOLDOWN_S = 1.0         # Minimum time between clicks
_PHYSICAL_OVERRIDE_PX = 15      # Physical mouse movement detection threshold
_PHYSICAL_PAUSE_S = 2.0         # How long to pause after physical override


def _extract_features(lm: EyeLandmarks) -> np.ndarray:
    """Extract 6-feature vector from EyeLandmarks for GazeScreenMapper."""
    lx, ly = lm.left_pupil
    rx, ry = lm.right_pupil
    return np.array([lx, ly, rx, ry, lm.head_yaw, lm.head_pitch], dtype=np.float32)


class GazeCursorController:
    """Production gaze cursor controller with absolute gaze mapping.

    Replaces the joystick-velocity approach of the original DesktopController.
    Requires a fitted GazeScreenMapper to operate in full mode; without one,
    the cursor will not move (safe default).

    Args:
        mapper: A GazeScreenMapper instance (may or may not be fitted).
                If None, creates a new un-fitted mapper.

    Callbacks:
        on_scroll_mode_toggled: Called with (is_scroll_mode: bool) when the
                                scroll mode changes (long blink).
        on_blink_detected: Called with no arguments on a confirmed click blink.
    """

    def __init__(self, mapper: GazeScreenMapper | None = None) -> None:
        self.screen_width, self.screen_height = pyautogui.size()
        self._mapper = mapper or GazeScreenMapper(self.screen_width, self.screen_height)

        # Adaptive gaze filters (one per screen axis)
        # min_cutoff: very low (0.05) to eliminate wobble when staring at a point.
        # beta: extremely low (0.001) because pixel velocities are in the thousands, so we don't want cutoff to explode.
        self._filter_x = OneEuroFilter(min_cutoff=0.05, beta=0.001)
        self._filter_y = OneEuroFilter(min_cutoff=0.05, beta=0.001)

        self._saccade = SaccadeFixationDetector(
            saccade_vel_px=500.0,    # Prevent noise from triggering fast-movement mode
            fixation_vel_px=150.0,
            min_fixation_ms=80.0,
        )
        self._predictor = LagCompensationPredictor(prediction_horizon_ms=45.0)

        # Blink / intent state
        self._ear_history: deque[float] = deque(maxlen=90)
        self._is_blinking = False
        self._last_blink_time = 0.0
        self._last_click_time = 0.0
        self._eyes_closed_start: float | None = None
        self._long_close_triggered = False

        # Scroll mode
        self._is_scroll_mode = False
        self._scroll_amount = 150
        if platform.system() == "Darwin":
            self._scroll_amount *= -1

        # Physical override guard
        self._last_commanded_x, self._last_commanded_y = pyautogui.position()
        self._pause_until = 0.0

        # Store last gaze features for click-based online adaptation
        self._last_features: np.ndarray | None = None

        # Public callbacks
        self.on_scroll_mode_toggled = None
        self.on_blink_detected = None

        logger.info(
            "GazeCursorController ready. Screen=%dx%d  Calibrated=%s",
            self.screen_width, self.screen_height, self._mapper.is_fitted,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Main update — called once per frame
    # ──────────────────────────────────────────────────────────────────────────

    def update(self, landmarks: EyeLandmarks) -> None:
        """Process one frame and update cursor / execute gestures."""
        now = time.monotonic()

        # ── Physical override guard ──────────────────────────────────────────
        cx, cy = pyautogui.position()
        if (abs(cx - self._last_commanded_x) > _PHYSICAL_OVERRIDE_PX or
                abs(cy - self._last_commanded_y) > _PHYSICAL_OVERRIDE_PX):
            if now > self._pause_until:
                logger.info("Physical mouse override detected. Pausing 2s.")
            self._pause_until = now + _PHYSICAL_PAUSE_S

        if now < self._pause_until:
            self._last_commanded_x = cx
            self._last_commanded_y = cy
            return

        # ── Blink / intent processing ────────────────────────────────────────
        avg_ear = (landmarks.left_ear + landmarks.right_ear) / 2.0
        self._ear_history.append(avg_ear)
        baseline = (sum(self._ear_history) / len(self._ear_history)
                    if self._ear_history else 0.25)
        closed = avg_ear < (baseline * _BLINK_CLOSE_THRESHOLD)
        self._process_blink(closed, now)

        if self._is_scroll_mode:
            self._handle_scroll(landmarks)
            return

        # ── Cursor positioning (requires fitted mapper) ───────────────────────
        if not self._mapper.is_fitted:
            return

        features = _extract_features(landmarks)
        self._last_features = features

        raw_sx, raw_sy = self._mapper.map(features)

        # ── Saccade / fixation classification ────────────────────────────────
        gaze_state, (stable_x, stable_y) = self._saccade.update(raw_sx, raw_sy, now)

        if gaze_state == GazeState.SACCADE:
            target_x, target_y = raw_sx, raw_sy
        else:
            # During fixation: use stable centroid
            target_x, target_y = stable_x, stable_y

        # ── One Euro Filter ───────────────────────────────────────────────────
        filtered_x = self._filter_x(target_x, now)
        filtered_y = self._filter_y(target_y, now)

        # ── Move cursor ───────────────────────────────────────────────────────
        final_x = int(np.clip(filtered_x, 0, self.screen_width - 1))
        final_y = int(np.clip(filtered_y, 0, self.screen_height - 1))

        try:
            pyautogui.moveTo(final_x, final_y)
            self._last_commanded_x = final_x
            self._last_commanded_y = final_y
        except pyautogui.FailSafeException:
            logger.error("FAILSAFE TRIGGERED.")
            raise

    # ──────────────────────────────────────────────────────────────────────────
    # Calibration access
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def mapper(self) -> GazeScreenMapper:
        return self._mapper

    @property
    def is_calibrated(self) -> bool:
        return self._mapper.is_fitted

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _process_blink(self, closed: bool, now: float) -> None:
        """State machine for blink, double-blink, and long-close detection."""
        if closed:
            if self._eyes_closed_start is None:
                self._eyes_closed_start = now
            duration = now - self._eyes_closed_start
            if duration >= _LONG_CLOSE_DURATION_S and not self._long_close_triggered:
                self._is_scroll_mode = not self._is_scroll_mode
                self._long_close_triggered = True
                logger.info("Long blink → scroll mode: %s", self._is_scroll_mode)
                if self.on_scroll_mode_toggled:
                    self.on_scroll_mode_toggled(self._is_scroll_mode)
            if not self._is_blinking:
                self._is_blinking = True
        else:
            if self._is_blinking:
                self._is_blinking = False
                if not self._long_close_triggered:
                    if now - self._last_click_time > _CLICK_COOLDOWN_S:
                        since_last = now - self._last_blink_time
                        if 0 < since_last < _DOUBLE_BLINK_WINDOW_S:
                            # Double blink → click
                            logger.info("Double blink detected → left click.")
                            pyautogui.click()
                            # Online adaptation: cursor click = confirmed gaze point
                            if self._last_features is not None and self._mapper.is_fitted:
                                cx, cy = pyautogui.position()
                                self._mapper.update_online(
                                    self._last_features,
                                    np.array([cx, cy], dtype=np.float64),
                                )
                            if self.on_blink_detected:
                                self.on_blink_detected()
                            self._last_click_time = now
                            self._last_blink_time = 0.0
                        else:
                            self._last_blink_time = now
                self._eyes_closed_start = None
                self._long_close_triggered = False

    def _handle_scroll(self, landmarks: EyeLandmarks) -> None:
        """Vertical gaze → scroll in scroll mode."""
        gy = -landmarks.gaze_y   # Invert: look up = positive gy
        deadzone = 0.20
        if abs(gy) > deadzone:
            magnitude = (abs(gy) - deadzone) / (1.0 - deadzone)
            direction = 1 if gy > 0 else -1
            amount = int(direction * magnitude * self._scroll_amount)
            if abs(amount) > 5:
                pyautogui.scroll(amount)

    def reset_filters(self) -> None:
        """Reset filter state after face loss / reacquisition."""
        self._filter_x.reset()
        self._filter_y.reset()
        self._saccade.reset()
        self._predictor.reset()
