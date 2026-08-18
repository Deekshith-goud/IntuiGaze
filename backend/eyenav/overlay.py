import time
import tkinter as tk


class HUDOverlay:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # Remove window borders
        self.root.attributes("-topmost", True)  # Always on top

        # Make the background transparent (Windows specific)
        self.bg_color = "black"
        self.root.config(bg=self.bg_color)
        self.root.attributes("-transparentcolor", self.bg_color)

        # Position top center
        screen_width = self.root.winfo_screenwidth()
        window_width = 300
        x = int(screen_width / 2 - window_width / 2)
        self.root.geometry(f"{window_width}x60+{x}+20")

        # Create the label
        self.label = tk.Label(
            self.root,
            text="🟢 ACTIVE",
            font=("Segoe UI", 16, "bold"),
            fg="#00FF00",
            bg=self.bg_color,
        )
        self.label.pack(expand=True, fill="both")

        self.flash_until = 0
        self.base_text = "🟢 ACTIVE"
        self.base_color = "#00FF00"

    def set_status(self, is_locked: bool) -> None:
        if is_locked:
            self.base_text = "🔴 SCROLL MODE (Look Up/Down)"
            self.base_color = "#FF3333"
        else:
            self.base_text = "🟢 ACTIVE"
            self.base_color = "#00FF00"

    def flash(self, text: str, color: str, duration: float = 0.5) -> None:
        self.label.config(text=text, fg=color)
        self.flash_until = time.time() + duration

    def update(self) -> None:
        """Must be called in the main execution loop to keep Tkinter responsive."""
        if time.time() > self.flash_until:
            self.label.config(text=self.base_text, fg=self.base_color)
        self.root.update()

    def destroy(self) -> None:
        self.root.destroy()
