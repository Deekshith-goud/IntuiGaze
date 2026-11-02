"""EyeNav Desktop HUD Overlay.
===========================

A sleek, visible, non-intrusive floating status pill for the normal desktop session.
Floats at the top center of the screen, providing immediate visual feedback
on tracking status, scroll mode, face detection, and click/blink gestures.
"""

from __future__ import annotations

import time
import tkinter as tk


class HUDOverlay:
    """A sleek floating status pill for the normal desktop tracking session."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # Remove titlebar and borders
        self.root.attributes("-topmost", True)  # Always stay on top

        sw = self.root.winfo_screenwidth()
        self.w, self.h = 320, 36
        x = int(sw / 2 - self.w / 2)
        y = 14
        self.root.geometry(f"{self.w}x{self.h}+{x}+{y}")
        self.root.configure(bg="#0F172A")

        self.canvas = tk.Canvas(
            self.root,
            width=self.w,
            height=self.h,
            bg="#0F172A",
            highlightthickness=1,
            highlightbackground="#334155",
            bd=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self._is_locked = False
        self._is_dragging = False
        self._is_standby = False
        self._face_detected = True
        self._flash_text: str | None = None
        self._flash_color = "#38BDF8"
        self._flash_until = 0.0

        self._draw()

    def set_status(self, is_locked: bool) -> None:
        """Update scroll mode status."""
        self._is_locked = is_locked
        self._draw()

    def set_drag_mode(self, is_dragging: bool) -> None:
        """Update drag and drop latch mode."""
        self._is_dragging = is_dragging
        self._draw()

    def set_standby_mode(self, is_standby: bool) -> None:
        """Update standby / pause mode."""
        self._is_standby = is_standby
        self._draw()

    def set_face_detected(self, detected: bool) -> None:
        """Update face detection state."""
        if self._face_detected != detected:
            self._face_detected = detected
            self._draw()

    def flash(self, text: str, color: str = "#FBBF24", duration: float = 0.6) -> None:
        """Briefly flash a gesture/click badge on the right side of the pill."""
        self._flash_text = text
        self._flash_color = color
        self._flash_until = time.time() + duration
        self._draw()

    def _draw(self) -> None:
        self.canvas.delete("all")
        cy = self.h / 2

        # Status Dot & Labels
        if not self._face_detected:
            dot_color = "#EF4444"
            main_text = "INTUIGAZE  |  SEARCHING..."
            badge_text = "[NO FACE]"
            badge_color = "#EF4444"
        elif self._is_standby:
            dot_color = "#64748B"
            main_text = "INTUIGAZE  |  STANDBY"
            badge_text = "[STANDBY]"
            badge_color = "#64748B"
        elif self._is_dragging:
            dot_color = "#A855F7"
            main_text = "INTUIGAZE  |  DRAGGING"
            badge_text = "[DRAGGING]"
            badge_color = "#A855F7"
        elif self._is_locked:
            dot_color = "#38BDF8"
            main_text = "INTUIGAZE  |  SCROLL MODE"
            badge_text = "[SCROLL]"
            badge_color = "#38BDF8"
        else:
            dot_color = "#10B981"
            main_text = "INTUIGAZE  |  ACTIVE"
            badge_text = "[TRACKING]"
            badge_color = "#64748B"

        # Check flash override for badge
        if time.time() < self._flash_until and self._flash_text:
            badge_text = self._flash_text
            badge_color = self._flash_color

        # Draw Status Dot (radius 4px)
        self.canvas.create_oval(14, cy - 4, 22, cy + 4, fill=dot_color, outline="")

        # Draw Main Status Text
        self.canvas.create_text(
            30, cy,
            text=main_text,
            fill="#F8FAFC",
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        )

        # Draw Right Badge
        self.canvas.create_text(
            self.w - 14, cy,
            text=badge_text,
            fill=badge_color,
            font=("Segoe UI", 8, "bold"),
            anchor="e",
        )

    def update(self) -> None:
        """Process Tkinter events and update flash state."""
        if self._flash_text and time.time() > self._flash_until:
            self._flash_text = None
            self._draw()
        self.root.update()

    def destroy(self) -> None:
        try:
            self.root.destroy()
        except Exception:
            pass
