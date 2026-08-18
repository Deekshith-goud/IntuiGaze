"""EyeNav Desktop Controller.
=========================

Translates eye tracking heuristics directly into OS-level mouse and scroll events
using PyAutoGUI.
"""

import logging
import platform
import time
from collections import deque

import pyautogui
from backend.eyenav.vision.landmarks import EyeLandmarks

logger = logging.getLogger(__name__)

# Failsafe allows user to regain control by moving mouse to corners
pyautogui.FAILSAFE = True


class DesktopController:
    def __init__(self, telemetry_logger=None) -> None:
        self.screen_width, self.screen_height = pyautogui.size()
        logger.info(
            f"Initialized Desktop Controller. Screen size: {self.screen_width}x{self.screen_height}"
        )

        self.telemetry_logger = telemetry_logger

        # Target Practice State
        self.target_x = -1.0
        self.target_y = -1.0

        # ML Spatial Model
        self.model = None

        # Configuration
        self.deadzone = 0.25
        self.max_speed = 2000  # pixels per second (Exponential max speed)
        self.last_time = time.time()

        # Physical Override State
        self.last_commanded_x, self.last_commanded_y = pyautogui.position()
        self.pause_until = 0.0

        # Intent State
        self.is_blinking = False
        self.last_single_blink_time = 0.0
        self.last_click_time = 0.0
        self.ear_history = deque(maxlen=150)  # 5 seconds of EAR history at 30fps
        self.eyes_closed_start_time = None
        self.is_long_close_triggered = False

        self.brow_history = deque(maxlen=150)  # 5 seconds of Eyebrow baseline
        self.last_lock_toggle_time = 0

        self.is_locked = False
        self.on_lock_toggled = None  # Callback for HUD
        self.on_blink_detected = None  # Callback for HUD

        self.scroll_amount = 150  # Windows scroll ticks

        # Invert scrolling on Mac if necessary, but we are on Windows
        if platform.system() == "Darwin":
            self.scroll_amount *= -1

    def update(self, landmarks: EyeLandmarks) -> None:
        """Processes a frame of landmarks and executes OS commands."""
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
        newly_blinked = False

        # Check for Physical Mouse Override
        current_x, current_y = pyautogui.position()

        # If the mouse moved significantly without our command, the user moved the physical mouse
        if (
            abs(current_x - self.last_commanded_x) > 10
            or abs(current_y - self.last_commanded_y) > 10
        ):
            if current_time > self.pause_until:
                logger.info("Physical mouse movement detected. Pausing eye tracking for 2 seconds.")
            self.pause_until = current_time + 2.0

        if current_time < self.pause_until:
            # Sync commanded position to current physical position so we don't instantly trigger override again
            self.last_commanded_x = current_x
            self.last_commanded_y = current_y
            return

        # 1. EAR Intent (Double Blink to Click, 2s Close to Lock)
        current_ear = (landmarks.left_ear + landmarks.right_ear) / 2.0
        self.ear_history.append(current_ear)

        baseline_ear = (
            sum(self.ear_history) / len(self.ear_history) if len(self.ear_history) > 0 else 0.25
        )
        currently_closed = current_ear < (baseline_ear * 0.70)

        if currently_closed:
            if self.eyes_closed_start_time is None:
                self.eyes_closed_start_time = current_time

            # Check for Long Close (2s) -> Toggle Lock
            if (current_time - self.eyes_closed_start_time) > 2.0:
                if not self.is_long_close_triggered:
                    self.is_locked = not self.is_locked
                    logger.info(f"Long Eye Close detected! Lock toggled to: {self.is_locked}")
                    if self.on_lock_toggled:
                        self.on_lock_toggled(self.is_locked)
                    self.is_long_close_triggered = True

            if not self.is_blinking:
                self.is_blinking = True
        else:
            # Eyes just opened
            if self.is_blinking:
                self.is_blinking = False

                # Only process as a blink if it wasn't a 2s long close
                if not self.is_long_close_triggered:
                    if current_time - self.last_click_time > 1.0:
                        time_since_last_blink = current_time - self.last_single_blink_time
                        if time_since_last_blink < 0.6:
                            # DOUBLE BLINK DETECTED!
                            if not self.is_locked:
                                logger.info("Double Blink intent detected: Executing Left Click")
                                pyautogui.click()
                                newly_blinked = True
                                if self.on_blink_detected:
                                    self.on_blink_detected()

                            self.last_click_time = current_time
                            self.last_single_blink_time = 0.0
                        else:
                            # SINGLE BLINK
                            self.last_single_blink_time = current_time

                # Reset state for next blink
                self.eyes_closed_start_time = None
                self.is_long_close_triggered = False

        # If LOCKED, Gaze becomes Scroll Wheel
        # Invert the gaze vectors because camera is mirrored
        gx = -landmarks.gaze_x
        gy = -landmarks.gaze_y

        if self.is_locked:
            # Scroll Mode
            if abs(gy) > self.deadzone:
                # Scroll speed based on how far up/down they look
                magnitude = (abs(gy) - self.deadzone) / (1.0 - self.deadzone)
                direction = (
                    -1 if gy > 0 else 1
                )  # Map gaze up (gy>0) to scroll up (positive scroll val in windows)
                scroll_amt = int(direction * magnitude * 200)
                if abs(scroll_amt) > 5:
                    pyautogui.scroll(scroll_amt)
            return  # Skip mouse movement

        # 2. Exponential Joystick Mouse Movement (Active Mode)
        x, y = pyautogui.position()
        new_x, new_y = x, y

        gx = -landmarks.gaze_x
        gy = -landmarks.gaze_y

        if abs(gx) > self.deadzone:
            magnitude = ((abs(gx) - self.deadzone) / (1.0 - self.deadzone)) ** 1.5
            direction = 1 if gx > 0 else -1
            new_x += direction * magnitude * self.max_speed * dt

        if abs(gy) > self.deadzone:
            magnitude = ((abs(gy) - self.deadzone) / (1.0 - self.deadzone)) ** 1.5
            direction = 1 if gy > 0 else -1
            if direction == 1:
                magnitude *= 1.8  # Anatomical downward boost
            new_y += direction * magnitude * self.max_speed * dt

        # Move if position changed significantly
        if new_x != current_x or new_y != current_y:
            # Clamp to screen edges
            new_x = max(0, min(new_x, self.screen_width - 1))
            new_y = max(0, min(new_y, self.screen_height - 1))
            try:
                pyautogui.moveTo(new_x, new_y)
                self.last_commanded_x = int(new_x)
                self.last_commanded_y = int(new_y)
            except pyautogui.FailSafeException:
                logger.error("FAILSAFE TRIGGERED! Mouse reached corner of screen. Exiting...")
                raise

        # 3. Telemetry Logging
        if self.telemetry_logger:
            is_physical_override = current_time < self.pause_until
            event_tag = ""
            if newly_blinked:
                event_tag = "CLICK"
            elif self.is_locked and (abs(scroll_amt) > 5 if "scroll_amt" in locals() else False):
                event_tag = "SCROLL"

            self.telemetry_logger.log_frame(
                gaze_x=landmarks.gaze_x,
                gaze_y=landmarks.gaze_y,
                left_ear=landmarks.left_ear,
                right_ear=landmarks.right_ear,
                brow_raise=landmarks.brow_raise,
                head_pitch=landmarks.head_pitch,
                head_yaw=landmarks.head_yaw,
                head_roll=landmarks.head_roll,
                head_z=landmarks.head_z,
                cursor_x=current_x,
                cursor_y=current_y,
                target_x=self.target_x,
                target_y=self.target_y,
                is_locked=self.is_locked,
                is_blinking=self.is_blinking,
                is_physical_override=is_physical_override,
                event_tag=event_tag,
            )
