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
    SCROLL: Long bilateral blink (>2s) toggles scroll mode; vertical gaze = scroll direction.

Click gesture:
    Right-eye wink (one-eye blink of 0.10s–0.80s with left eye open) → left click.
    Natural bilateral blinks (both eyes) are ignored to prevent accidental clicks.
    If the mapper is fitted, each click also feeds back into the online adapter.

Physical override:
    If the user moves the physical mouse > 15px from the last commanded
    position, eye tracking pauses for 2 seconds (same as original system).
"""

from __future__ import annotations

import logging
import math
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

_BLINK_CLOSE_THRESHOLD = 0.68  # EAR below (baseline × this) = closed
_WINK_OPEN_THRESHOLD = 0.78  # Opposite eye must be >= this to confirm wink
_MIN_WINK_DURATION_S = 0.10  # Minimum wink closure duration
_MAX_WINK_DURATION_S = 0.75  # Maximum single wink closure duration
_DOUBLE_CLICK_WINDOW_S = 0.50  # Double-wink completion threshold
_DRAG_HOLD_DURATION_S = 1.00  # Hold secondary wink >= this to latch drag
_LONG_CLOSE_DURATION_S = 2.0  # Both eyes closed duration to toggle scroll mode
_STANDBY_CLOSE_DURATION_S = 3.5  # Both eyes closed duration to toggle standby
_BROW_RAISE_THRESHOLD = 0.35  # Brow raise elevation threshold
_BROW_RAISE_DURATION_S = 0.40  # Duration required to trigger brow gesture
_CLICK_COOLDOWN_S = 0.25  # Minimum cooldown between click actions
_PHYSICAL_OVERRIDE_PX = 15  # Physical mouse movement detection threshold
_PHYSICAL_PAUSE_S = 2.0  # How long to pause after physical override
_FIXATION_DEADZONE_PX = 45.0  # Deadzone for fixation stability


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

    def __init__(
        self,
        mapper: GazeScreenMapper | None = None,
        invert_eyes: bool = False,
    ) -> None:
        self.screen_width, self.screen_height = pyautogui.size()
        self._mapper = mapper or GazeScreenMapper(self.screen_width, self.screen_height)
        self._invert_eyes = invert_eyes

        # Adaptive gaze filters (one per screen axis)
        # min_cutoff: very low (0.05) to eliminate wobble when staring at a point.
        # beta: extremely low (0.001) because pixel velocities are in the thousands, so we don't want cutoff to explode.
        self._filter_x = OneEuroFilter(min_cutoff=0.05, beta=0.001)
        self._filter_y = OneEuroFilter(min_cutoff=0.05, beta=0.001)

        self._saccade = SaccadeFixationDetector(
            saccade_vel_px=500.0,  # Prevent noise from triggering fast-movement mode
            fixation_vel_px=150.0,
            min_fixation_ms=80.0,
        )
        self._predictor = LagCompensationPredictor(prediction_horizon_ms=45.0)

        # Separate running EAR baselines for left and right eyes
        self._left_ear_history: deque[float] = deque(maxlen=90)
        self._right_ear_history: deque[float] = deque(maxlen=90)

        # Primary eye gesture state (Right eye default: Click & Double Click, or Drop)
        self._is_primary_winking = False
        self._primary_wink_start_time: float | None = None
        self._last_primary_click_time = 0.0

        # Secondary eye gesture state (Left eye default: Right Click & Drag Latch)
        self._is_secondary_winking = False
        self._secondary_wink_start_time: float | None = None
        self._drag_triggered = False
        self._is_dragging = False

        # Bilateral closure state (Scroll toggle >= 2s, Standby toggle >= 3.5s)
        self._both_closed_start: float | None = None
        self._scroll_triggered = False
        self._standby_triggered = False

        # Modes
        self._is_scroll_mode = False
        self._is_standby = False
        self._scroll_amount = 150
        if platform.system() == "Darwin":
            self._scroll_amount *= -1

        # Brow raise gesture state (Fixation anchor snap / recenter)
        self._brow_raise_start: float | None = None
        self._brow_raise_triggered = False

        # Physical override guard
        self._last_commanded_x, self._last_commanded_y = pyautogui.position()
        self._pause_until = 0.0

        # Store last gaze features for click-based online adaptation
        self._last_features: np.ndarray | None = None

        # Fixation gravity well — cursor anchors to the centroid and only
        # moves when the eye deliberately departs by > _FIXATION_DEADZONE_PX.
        self._fixation_anchor: tuple[float, float] | None = None

        # Public callbacks
        self.on_scroll_mode_toggled = None
        self.on_standby_toggled = None
        self.on_drag_mode_toggled = None
        self.on_blink_detected = None
        self.on_gesture_event = None  # Callable[[str, str], None] -> (name, color)

        logger.info(
            "GazeCursorController ready. Screen=%dx%d  Calibrated=%s  InvertEyes=%s",
            self.screen_width,
            self.screen_height,
            self._mapper.is_fitted,
            self._invert_eyes,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Main update — called once per frame
    # ──────────────────────────────────────────────────────────────────────────

    def update(self, landmarks: EyeLandmarks) -> None:
        """Process one frame and update cursor / execute gestures."""
        now = time.monotonic()

        # ── Physical override guard ──────────────────────────────────────────
        cx, cy = pyautogui.position()
        if (
            abs(cx - self._last_commanded_x) > _PHYSICAL_OVERRIDE_PX
            or abs(cy - self._last_commanded_y) > _PHYSICAL_OVERRIDE_PX
        ):
            if now > self._pause_until:
                logger.info("Physical mouse override detected. Pausing 2s.")
            self._pause_until = now + _PHYSICAL_PAUSE_S

        if now < self._pause_until:
            self._last_commanded_x = cx
            self._last_commanded_y = cy
            return

        # ── Multi-Modal Eye & Facial Gesture Processing ───────────────────────
        self._process_eye_gestures(landmarks, now)

        # Standby mode suppresses cursor movement
        if self._is_standby:
            return

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
            # Eye is moving fast — release the anchor so cursor follows freely
            self._fixation_anchor = None
            target_x, target_y = raw_sx, raw_sy
        else:
            # During fixation: apply gravity well
            if self._fixation_anchor is None:
                # First fixation frame — lock the anchor to the stable centroid
                self._fixation_anchor = (stable_x, stable_y)

            ax, ay = self._fixation_anchor
            dist_from_anchor = math.hypot(raw_sx - ax, raw_sy - ay)

            if dist_from_anchor < _FIXATION_DEADZONE_PX:
                # Inside dead zone → hold perfectly still at anchor
                target_x, target_y = ax, ay
            else:
                # Outside dead zone → the user made a deliberate small movement
                # Update the anchor to the new stable centroid and follow
                self._fixation_anchor = (stable_x, stable_y)
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
    # State and Calibration access
    # ──────────────────────────────────────────────────────────────────────────

    @property
    def mapper(self) -> GazeScreenMapper:
        return self._mapper

    @property
    def is_calibrated(self) -> bool:
        return self._mapper.is_fitted

    @property
    def is_scroll_mode(self) -> bool:
        return self._is_scroll_mode

    @property
    def is_dragging(self) -> bool:
        return self._is_dragging

    @property
    def is_standby(self) -> bool:
        return self._is_standby

    @property
    def _is_winking(self) -> bool:
        return self._is_primary_winking

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _emit_gesture(self, name: str, color: str) -> None:
        """Notify external listeners (such as the HUD overlay)."""
        if self.on_gesture_event:
            try:
                self.on_gesture_event(name, color)
            except Exception as e:
                logger.debug("on_gesture_event callback error: %s", e)

    def _process_eye_gestures(self, *args, **kwargs) -> None:
        """Full state machine for multi-modal eye and facial gestures."""
        if args and isinstance(args[0], EyeLandmarks):
            lm = args[0]
            left_ear = lm.left_ear
            right_ear = lm.right_ear
            brow_raise = lm.brow_raise
            t = args[1] if len(args) > 1 else kwargs.get("now", kwargs.get("now_or_right", time.monotonic()))
        elif args and isinstance(args[0], (int, float)):
            left_ear = float(args[0])
            right_ear = float(args[1]) if len(args) > 1 else kwargs.get("right_ear", 0.28)
            brow_raise = float(args[2]) if len(args) > 2 else kwargs.get("brow_raise", 0.0)
            t = float(args[3]) if len(args) > 3 else kwargs.get("now", kwargs.get("now_or_right", time.monotonic()))
        else:
            left_ear = float(kwargs.get("left_ear", 0.28))
            right_ear = float(kwargs.get("right_ear", 0.28))
            brow_raise = float(kwargs.get("brow_raise", 0.0))
            t = float(kwargs.get("now", kwargs.get("now_or_right", time.monotonic())))

        left_base = np.median(self._left_ear_history) if len(self._left_ear_history) >= 5 else 0.28
        right_base = np.median(self._right_ear_history) if len(self._right_ear_history) >= 5 else 0.28

        # Only update running baselines with open-eye frames so closures don't drag down baseline
        if left_ear >= left_base * 0.75:
            self._left_ear_history.append(left_ear)
        elif len(self._left_ear_history) < 5:
            self._left_ear_history.append(left_ear)

        if right_ear >= right_base * 0.75:
            self._right_ear_history.append(right_ear)
        elif len(self._right_ear_history) < 5:
            self._right_ear_history.append(right_ear)

        left_closed = left_ear < (left_base * _BLINK_CLOSE_THRESHOLD)
        right_closed = right_ear < (right_base * _BLINK_CLOSE_THRESHOLD)

        left_open = left_ear >= (left_base * _WINK_OPEN_THRESHOLD)
        right_open = right_ear >= (right_base * _WINK_OPEN_THRESHOLD)

        if not self._invert_eyes:
            primary_closed, secondary_closed = right_closed, left_closed
            primary_open, secondary_open = right_open, left_open
        else:
            primary_closed, secondary_closed = left_closed, right_closed
            primary_open, secondary_open = left_open, right_open

        # ── 1. Bilateral Eye Closure (Natural Blinks, Scroll Mode, Standby) ───
        if left_closed and right_closed:
            # Cancel single-eye winks immediately on bilateral closure
            self._is_primary_winking = False
            self._primary_wink_start_time = None
            self._is_secondary_winking = False
            self._secondary_wink_start_time = None

            if self._both_closed_start is None:
                self._both_closed_start = t
            duration = t - self._both_closed_start

            # Bilateral >= 3.5s -> Toggle Standby Mode
            if duration >= _STANDBY_CLOSE_DURATION_S and not self._standby_triggered:
                self._standby_triggered = True
                self._is_standby = not self._is_standby
                logger.info("Long bilateral closure (>=3.5s) → Standby toggled: %s", self._is_standby)
                if self._is_dragging:
                    pyautogui.mouseUp()
                    self._is_dragging = False
                    if self.on_drag_mode_toggled:
                        self.on_drag_mode_toggled(False)
                if self.on_standby_toggled:
                    self.on_standby_toggled(self._is_standby)
                if self._is_standby:
                    self._emit_gesture("[STANDBY]", "#64748B")
                else:
                    self._emit_gesture("[ACTIVE]", "#10B981")
                return

            # Bilateral >= 2.0s -> Toggle Scroll Mode
            if duration >= _LONG_CLOSE_DURATION_S and not self._scroll_triggered and not self._standby_triggered:
                self._scroll_triggered = True
                self._is_scroll_mode = not self._is_scroll_mode
                logger.info("Long bilateral closure (>=2.0s) → Scroll mode toggled: %s", self._is_scroll_mode)
                if self.on_scroll_mode_toggled:
                    self.on_scroll_mode_toggled(self._is_scroll_mode)
                if self._is_scroll_mode:
                    self._emit_gesture("[SCROLL]", "#38BDF8")
                else:
                    self._emit_gesture("[TRACKING]", "#10B981")
                return

            return

        # Both eyes are not closed -> reset bilateral closure trackers
        self._both_closed_start = None
        self._scroll_triggered = False
        self._standby_triggered = False

        # If in Standby, a deliberate wink from either eye wakes the system
        if self._is_standby:
            if (primary_closed and secondary_open) or (secondary_closed and primary_open):
                self._is_standby = False
                logger.info("Deliberate wink detected → waking up from standby.")
                if self.on_standby_toggled:
                    self.on_standby_toggled(False)
                self._emit_gesture("[ACTIVE]", "#10B981")
            return

        # ── 2. Primary Eye Wink (Right Eye: Click, Double Click, Drop) ─────────
        if primary_closed and secondary_open:
            if not self._is_primary_winking:
                self._is_primary_winking = True
                self._primary_wink_start_time = t
            elif self._primary_wink_start_time and (t - self._primary_wink_start_time) > _MAX_WINK_DURATION_S:
                # Canceled due to holding too long
                self._is_primary_winking = False
                self._primary_wink_start_time = None
            return

        if self._is_primary_winking and primary_open:
            self._is_primary_winking = False
            if self._primary_wink_start_time is not None:
                wink_dur = t - self._primary_wink_start_time
                self._primary_wink_start_time = None

                if _MIN_WINK_DURATION_S <= wink_dur <= _MAX_WINK_DURATION_S:
                    # If dragging, primary wink releases drag & drop!
                    if self._is_dragging:
                        pyautogui.mouseUp()
                        self._is_dragging = False
                        logger.info("Primary wink dropped drag lock.")
                        if self.on_drag_mode_toggled:
                            self.on_drag_mode_toggled(False)
                        self._emit_gesture("[DROPPED]", "#10B981")
                        self._last_primary_click_time = t
                        return

                    # Normal mode: Check for Double Click vs Single Click
                    time_since_last = t - self._last_primary_click_time
                    if 0 < time_since_last <= _DOUBLE_CLICK_WINDOW_S:
                        # Rapid double wink -> Double Click
                        logger.info("Rapid double wink (%.2fs gap) → double click.", time_since_last)
                        pyautogui.doubleClick()
                        self._emit_gesture("[DOUBLE]", "#F59E0B")
                        self._last_primary_click_time = 0.0
                    elif time_since_last > _CLICK_COOLDOWN_S:
                        # Single Left Click
                        logger.info("Primary wink detected (%.2fs) → left click.", wink_dur)
                        pyautogui.click()
                        self._emit_gesture("[CLICK]", "#FBBF24")

                        # Online adaptation: confirmed click = user's target intention
                        if self._last_features is not None and self._mapper.is_fitted:
                            cx, cy = pyautogui.position()
                            self._mapper.update_online(
                                self._last_features,
                                np.array([cx, cy], dtype=np.float64),
                            )

                        if self.on_blink_detected:
                            self.on_blink_detected()

                        self._last_primary_click_time = t

        # ── 3. Secondary Eye Wink (Left Eye: Right Click & Drag Latch) ─────────
        if secondary_closed and primary_open:
            if not self._is_secondary_winking:
                self._is_secondary_winking = True
                self._secondary_wink_start_time = t
                self._drag_triggered = False
            else:
                hold_dur = t - self._secondary_wink_start_time
                if hold_dur >= _DRAG_HOLD_DURATION_S and not self._drag_triggered:
                    # Latch Drag & Drop Lock!
                    self._drag_triggered = True
                    self._is_dragging = True
                    pyautogui.mouseDown()
                    logger.info("Secondary eye held (%.2fs) → Drag Lock engaged (mouseDown).", hold_dur)
                    if self.on_drag_mode_toggled:
                        self.on_drag_mode_toggled(True)
                    self._emit_gesture("[DRAGGING]", "#A855F7")
            return

        if self._is_secondary_winking and secondary_open:
            self._is_secondary_winking = False
            if not self._drag_triggered and self._secondary_wink_start_time is not None:
                wink_dur = t - self._secondary_wink_start_time
                if _MIN_WINK_DURATION_S <= wink_dur <= _MAX_WINK_DURATION_S:
                    # Single Left Wink -> Right Click (Context Menu)
                    logger.info("Secondary wink detected (%.2fs) → right click.", wink_dur)
                    pyautogui.rightClick()
                    self._emit_gesture("[RIGHT CLICK]", "#38BDF8")
            self._secondary_wink_start_time = None
            self._drag_triggered = False

        # ── 4. Upper Facial Gesture: Brow Raise (Fixation Anchor Snap / Center) ─
        if brow_raise > _BROW_RAISE_THRESHOLD:
            if self._brow_raise_start is None:
                self._brow_raise_start = t
            elif (t - self._brow_raise_start) >= _BROW_RAISE_DURATION_S and not self._brow_raise_triggered:
                self._brow_raise_triggered = True
                logger.info("Brow raise detected (elev=%.2f) → snapping anchor / recentering.", brow_raise)
                if self._fixation_anchor is not None:
                    ax, ay = self._fixation_anchor
                    pyautogui.moveTo(int(ax), int(ay))
                    self._last_commanded_x, self._last_commanded_y = int(ax), int(ay)
                else:
                    cx, cy = self.screen_width // 2, self.screen_height // 2
                    pyautogui.moveTo(cx, cy)
                    self._last_commanded_x, self._last_commanded_y = cx, cy
                self._emit_gesture("[ANCHOR]", "#14B8A6")
        else:
            self._brow_raise_start = None
            self._brow_raise_triggered = False

    def _handle_scroll(self, landmarks: EyeLandmarks) -> None:
        """Vertical gaze → scroll in scroll mode."""
        gy = -landmarks.gaze_y  # Invert: look up = positive gy
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
