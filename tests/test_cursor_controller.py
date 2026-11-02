"""Unit tests for GazeCursorController multi-modal eye and facial gestures."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from backend.eyenav.cursor.controller import GazeCursorController
from backend.eyenav.vision.landmarks import EyeLandmarks


def _make_dummy_landmarks(
    left_ear: float = 0.30,
    right_ear: float = 0.30,
    brow_raise: float = 0.0,
) -> EyeLandmarks:
    """Create test EyeLandmarks with controlled features."""
    import numpy as np
    return EyeLandmarks(
        left_ear=left_ear,
        right_ear=right_ear,
        left_pupil=(0.5, 0.5),
        right_pupil=(0.5, 0.5),
        raw_points=np.zeros((478, 2), dtype=np.float32),
        gaze_x=0.0,
        gaze_y=0.0,
        brow_raise=brow_raise,
        head_pitch=0.0,
        head_yaw=0.0,
        head_roll=0.0,
        head_z=0.0,
    )


class TestEyeGestures:
    """Tests for multi-modal ocular & facial gestures and safety gates."""

    @patch("pyautogui.click")
    @patch("pyautogui.rightClick")
    @patch("pyautogui.moveTo")
    @patch("pyautogui.position", return_value=(500, 500))
    def test_right_eye_wink_triggers_left_click(self, mock_pos, mock_move, mock_rclick, mock_click):
        """Right-eye wink (right closed, left open) must trigger a left click."""
        controller = GazeCursorController()
        blink_callback = MagicMock()
        gesture_callback = MagicMock()
        controller.on_blink_detected = blink_callback
        controller.on_gesture_event = gesture_callback

        t = 100.0
        # Warmup with open eyes to establish baseline (EAR = 0.30)
        for _ in range(20):
            controller._process_eye_gestures(left_ear=0.30, right_ear=0.30, now=t)
            t += 0.033

        # Start right-eye wink (right closed: 0.12, left open: 0.30) for 0.25s
        for _ in range(7):
            controller._process_eye_gestures(left_ear=0.30, right_ear=0.12, now=t)
            t += 0.033

        # Right eye re-opens
        controller._process_eye_gestures(left_ear=0.30, right_ear=0.30, now=t)

        # Assert left click triggered, right click NOT triggered
        assert mock_click.called
        assert not mock_rclick.called
        assert blink_callback.called
        assert gesture_callback.called

    @patch("pyautogui.click")
    @patch("pyautogui.rightClick")
    @patch("pyautogui.moveTo")
    @patch("pyautogui.position", return_value=(500, 500))
    def test_left_eye_wink_triggers_right_click(self, mock_pos, mock_move, mock_rclick, mock_click):
        """Left-eye wink (left closed, right open) must trigger a right click (context menu)."""
        controller = GazeCursorController()
        gesture_callback = MagicMock()
        controller.on_gesture_event = gesture_callback

        t = 100.0
        for _ in range(20):
            controller._process_eye_gestures(left_ear=0.30, right_ear=0.30, now=t)
            t += 0.033

        # Left eye winks (left closed: 0.12, right open: 0.30) for 0.25s
        for _ in range(7):
            controller._process_eye_gestures(left_ear=0.12, right_ear=0.30, now=t)
            t += 0.033

        # Left eye re-opens
        controller._process_eye_gestures(left_ear=0.30, right_ear=0.30, now=t)

        # Assert right click triggered, left click NOT triggered
        assert mock_rclick.called
        assert not mock_click.called
        assert gesture_callback.called

    @patch("pyautogui.click")
    @patch("pyautogui.doubleClick")
    @patch("pyautogui.moveTo")
    @patch("pyautogui.position", return_value=(500, 500))
    def test_rapid_double_right_wink_triggers_double_click(self, mock_pos, mock_move, mock_dclick, mock_click):
        """Two consecutive right winks within 0.5s must trigger a double click."""
        controller = GazeCursorController()
        t = 100.0

        for _ in range(20):
            controller._process_eye_gestures(left_ear=0.30, right_ear=0.30, now=t)
            t += 0.033

        # 1st Right Wink (0.20s)
        for _ in range(6):
            controller._process_eye_gestures(left_ear=0.30, right_ear=0.12, now=t)
            t += 0.033
        controller._process_eye_gestures(left_ear=0.30, right_ear=0.30, now=t)
        t += 0.10  # 100ms pause with open eyes

        # 2nd Right Wink (0.20s) within 0.5s window
        for _ in range(6):
            controller._process_eye_gestures(left_ear=0.30, right_ear=0.12, now=t)
            t += 0.033
        controller._process_eye_gestures(left_ear=0.30, right_ear=0.30, now=t)

        # Assert double click was triggered
        assert mock_dclick.called

    @patch("pyautogui.mouseDown")
    @patch("pyautogui.mouseUp")
    @patch("pyautogui.click")
    @patch("pyautogui.moveTo")
    @patch("pyautogui.position", return_value=(500, 500))
    def test_left_wink_hold_latches_drag_and_right_wink_drops(
        self, mock_pos, mock_move, mock_click, mock_mup, mock_mdown
    ):
        """Holding left eye closed >= 1.0s engages Drag Lock; right wink drops."""
        controller = GazeCursorController()
        drag_callback = MagicMock()
        controller.on_drag_mode_toggled = drag_callback

        t = 100.0
        for _ in range(20):
            controller._process_eye_gestures(left_ear=0.30, right_ear=0.30, now=t)
            t += 0.033

        assert not controller.is_dragging

        # Hold left eye closed for 1.2s (left closed, right open)
        for _ in range(36):
            controller._process_eye_gestures(left_ear=0.12, right_ear=0.30, now=t)
            t += 0.033

        # Drag lock must be latched (mouseDown called)
        assert controller.is_dragging
        assert mock_mdown.called
        assert drag_callback.called

        # Left eye re-opens; drag lock remains latched while navigating with both eyes open
        for _ in range(10):
            controller._process_eye_gestures(left_ear=0.30, right_ear=0.30, now=t)
            t += 0.033
        assert controller.is_dragging

        # Right wink drops the item (mouseUp called)
        for _ in range(6):
            controller._process_eye_gestures(left_ear=0.30, right_ear=0.12, now=t)
            t += 0.033
        controller._process_eye_gestures(left_ear=0.30, right_ear=0.30, now=t)

        assert not controller.is_dragging
        assert mock_mup.called

    @patch("pyautogui.click")
    @patch("pyautogui.rightClick")
    @patch("pyautogui.moveTo")
    @patch("pyautogui.position", return_value=(500, 500))
    def test_natural_bilateral_blink_does_not_click(self, mock_pos, mock_move, mock_rclick, mock_click):
        """Natural bilateral blink (both eyes closed) must NOT trigger any click."""
        controller = GazeCursorController()
        blink_callback = MagicMock()
        controller.on_blink_detected = blink_callback

        t = 100.0
        # Warmup with open eyes (EAR = 0.30)
        for _ in range(20):
            controller._process_eye_gestures(left_ear=0.30, right_ear=0.30, now=t)
            t += 0.033

        # Natural blink: BOTH eyes close for 0.20s (EAR = 0.12)
        for _ in range(6):
            controller._process_eye_gestures(left_ear=0.12, right_ear=0.12, now=t)
            t += 0.033

        # Both eyes re-open
        controller._process_eye_gestures(left_ear=0.30, right_ear=0.30, now=t)

        # Assert no click triggered
        assert not mock_click.called
        assert not mock_rclick.called
        assert not blink_callback.called

    @patch("pyautogui.click")
    @patch("pyautogui.moveTo")
    @patch("pyautogui.position", return_value=(500, 500))
    def test_bilateral_long_closure_toggles_scroll_mode(self, mock_pos, mock_move, mock_click):
        """Holding both eyes closed for >= 2.0s toggles scroll mode."""
        controller = GazeCursorController()
        scroll_callback = MagicMock()
        controller.on_scroll_mode_toggled = scroll_callback

        t = 100.0
        for _ in range(20):
            controller._process_eye_gestures(left_ear=0.30, right_ear=0.30, now=t)
            t += 0.033

        assert not controller.is_scroll_mode

        # Close both eyes for 2.2 seconds
        for _ in range(70):
            controller._process_eye_gestures(left_ear=0.12, right_ear=0.12, now=t)
            t += 0.033

        assert controller.is_scroll_mode
        assert scroll_callback.called
        assert not mock_click.called

    @patch("pyautogui.click")
    @patch("pyautogui.moveTo")
    @patch("pyautogui.position", return_value=(500, 500))
    def test_bilateral_prolonged_closure_toggles_standby_mode(self, mock_pos, mock_move, mock_click):
        """Holding both eyes closed for >= 3.5s toggles Standby mode."""
        controller = GazeCursorController()
        standby_callback = MagicMock()
        controller.on_standby_toggled = standby_callback

        t = 100.0
        for _ in range(20):
            controller._process_eye_gestures(left_ear=0.30, right_ear=0.30, now=t)
            t += 0.033

        assert not controller.is_standby

        # Close both eyes for 3.6 seconds (110 frames at 30fps)
        for _ in range(110):
            controller._process_eye_gestures(left_ear=0.12, right_ear=0.12, now=t)
            t += 0.033

        assert controller.is_standby
        assert standby_callback.called

    @patch("pyautogui.moveTo")
    @patch("pyautogui.position", return_value=(500, 500))
    def test_brow_raise_triggers_anchor_snap(self, mock_pos, mock_move):
        """Elevating eyebrows (>0.35) for 0.4s triggers fixation anchor snap."""
        controller = GazeCursorController()
        controller._fixation_anchor = (640.0, 480.0)

        t = 100.0
        for _ in range(20):
            lm = _make_dummy_landmarks(brow_raise=0.0)
            controller._process_eye_gestures(lm, now_or_right=t)
            t += 0.033

        # Raise eyebrows for 0.45s (14 frames)
        for _ in range(14):
            lm = _make_dummy_landmarks(brow_raise=0.45)
            controller._process_eye_gestures(lm, now_or_right=t)
            t += 0.033

        # Assert moveTo was called to snap anchor to (640, 480)
        assert mock_move.called
        mock_move.assert_called_with(640, 480)

    @patch("pyautogui.click")
    @patch("pyautogui.rightClick")
    @patch("pyautogui.moveTo")
    @patch("pyautogui.position", return_value=(500, 500))
    def test_invert_eyes_reverses_click_roles(self, mock_pos, mock_move, mock_rclick, mock_click):
        """When invert_eyes=True, Left Wink clicks and Right Wink right-clicks."""
        controller = GazeCursorController(invert_eyes=True)
        t = 100.0

        for _ in range(20):
            controller._process_eye_gestures(left_ear=0.30, right_ear=0.30, now=t)
            t += 0.033

        # Left eye winks (left closed: 0.12, right open: 0.30)
        for _ in range(6):
            controller._process_eye_gestures(left_ear=0.12, right_ear=0.30, now=t)
            t += 0.033
        controller._process_eye_gestures(left_ear=0.30, right_ear=0.30, now=t)

        # Inverted: Left wink must trigger primary click!
        assert mock_click.called
        assert not mock_rclick.called
