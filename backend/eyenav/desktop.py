"""EyeNav Desktop Controller.
=========================

Thin wrapper around GazeCursorController that preserves the existing
public API (callbacks, update() signature) so run_desktop.py requires
minimal changes.

The old joystick-velocity model has been fully replaced by the new
absolute gaze mapping pipeline in cursor/controller.py.
"""

from __future__ import annotations

import logging

from backend.eyenav.cursor.controller import GazeCursorController
from backend.eyenav.cursor.mapping import GazeScreenMapper
from backend.eyenav.vision.landmarks import EyeLandmarks

logger = logging.getLogger(__name__)


class DesktopController:
    """Backward-compatible wrapper around GazeCursorController.

    Exposes the same .update(landmarks) interface and callback attributes
    as the previous implementation, while internally using the full
    gaze mapping pipeline.
    """

    def __init__(
        self,
        mapper: GazeScreenMapper | None = None,
        telemetry_logger=None,
    ) -> None:
        self._controller = GazeCursorController(mapper=mapper)
        self._telemetry = telemetry_logger

        # Proxy callback attributes so callers can still do:
        #   controller.on_lock_toggled = overlay.set_status
        #   controller.on_blink_detected = lambda: overlay.flash(...)
        self._controller.on_blink_detected = None

    # ── Public callback properties ───────────────────────────────────────────

    @property
    def on_lock_toggled(self):
        """Maps to scroll mode toggled (API compatibility)."""
        return self._controller.on_scroll_mode_toggled

    @on_lock_toggled.setter
    def on_lock_toggled(self, cb):
        self._controller.on_scroll_mode_toggled = cb

    @property
    def on_blink_detected(self):
        return self._controller.on_blink_detected

    @on_blink_detected.setter
    def on_blink_detected(self, cb):
        self._controller.on_blink_detected = cb

    # ── Public state properties ──────────────────────────────────────────────

    @property
    def is_calibrated(self) -> bool:
        return self._controller.is_calibrated

    @property
    def mapper(self) -> GazeScreenMapper:
        return self._controller.mapper

    # ── Main update ──────────────────────────────────────────────────────────

    def update(self, landmarks: EyeLandmarks) -> None:
        """Process one frame of landmarks."""
        self._controller.update(landmarks)

        if self._telemetry:
            try:
                import pyautogui
                cx, cy = pyautogui.position()
                self._telemetry.log_frame(
                    gaze_x=landmarks.gaze_x,
                    gaze_y=landmarks.gaze_y,
                    left_ear=landmarks.left_ear,
                    right_ear=landmarks.right_ear,
                    lx=landmarks.left_pupil[0],
                    ly=landmarks.left_pupil[1],
                    rx=landmarks.right_pupil[0],
                    ry=landmarks.right_pupil[1],
                    brow_raise=landmarks.brow_raise,
                    head_pitch=landmarks.head_pitch,
                    head_yaw=landmarks.head_yaw,
                    head_roll=landmarks.head_roll,
                    head_z=landmarks.head_z,
                    cursor_x=cx,
                    cursor_y=cy,
                    target_x=-1.0,
                    target_y=-1.0,
                    is_locked=self._controller._is_scroll_mode,
                    is_blinking=self._controller._is_blinking,
                    is_physical_override=False,
                    event_tag="",
                )
            except Exception:
                pass
