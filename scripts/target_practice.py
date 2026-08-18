import logging
import random
import sys
import threading
import time
import tkinter as tk
import winsound  # Windows native sound
from pathlib import Path

import cv2
import numpy as np
import pyautogui

# Add project root to path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.eyenav.desktop import DesktopController
from backend.eyenav.telemetry import TelemetryLogger
from backend.eyenav.vision.landmarks import FaceLandmarkExtractor
from scripts.run_desktop import get_valid_camera

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TargetPractice")

# Neon Theme Colors
BG_COLOR = "#0B0C10"
TARGET_COLOR = "#66FCF1"
TARGET_OUTLINE = "#45A29E"
TEXT_COLOR = "#C5C6C7"
HIGHLIGHT_COLOR = "#F2A900"
ERROR_COLOR = "#FF3333"

class TargetPracticeGame:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg=BG_COLOR)
        self.root.config(cursor="crosshair")

        # Press ESC to exit
        self.root.bind('<Escape>', lambda e: self.root.quit())

        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()

        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack()

        self.state = "START" # START, PLAYING, GAMEOVER
        self.time_elapsed = 0.0
        self.total_target_time = 0.0

        self.target_radius = 50
        self.target_x = -1.0
        self.target_y = -1.0
        self.target_spawn_time = 0

        self.hits = 0
        self.misses = 0

        # UI Elements
        self.target_id = None
        self.target_glow_id = None

        # Start Screen UI
        self.title_text = self.canvas.create_text(
            self.width/2, self.height/2 - 50, text="EYENAV: CYBER AIM", fill=TARGET_COLOR, font=("Consolas", 48, "bold"), anchor="center"
        )
        self.start_text = self.canvas.create_text(
            self.width/2, self.height/2 + 50, text="Stare at the center and BLINK to start.", fill=TEXT_COLOR, font=("Consolas", 24), anchor="center"
        )

        # HUD UI (Clinical Dashboard)
        # We put a dark gray bar at the bottom to ensure the text is always visible
        self.hud_bg = self.canvas.create_rectangle(
            0, self.height - 40, self.width, self.height, fill="#1A1A1A", outline=""
        )
        self.hud_text = self.canvas.create_text(
            self.width/2, self.height - 20, text="", fill=TEXT_COLOR, font=("Consolas", 14), anchor="center"
        )

        # Initialize Backend
        self.cap = get_valid_camera()
        if not self.cap:
            logger.error("No camera found.")
            sys.exit(1)

        self.extractor = FaceLandmarkExtractor(max_faces=1)
        self.telemetry = TelemetryLogger()
        self.controller = DesktopController(telemetry_logger=self.telemetry)

        self.controller.on_blink_detected = self.handle_blink

        self.is_running = True
        self.vision_thread = threading.Thread(target=self.vision_loop)
        self.vision_thread.daemon = True
        self.vision_thread.start()

        self.game_loop()

    def start_game(self) -> None:
        self.state = "PLAYING"
        self.time_elapsed = 0.0
        self.total_target_time = 0.0
        self.hits = 0
        self.misses = 0

        self.canvas.itemconfig(self.title_text, state="hidden")
        self.canvas.itemconfig(self.start_text, state="hidden")

        # Create Target
        self.target_glow_id = self.canvas.create_oval(0, 0, 0, 0, fill="", outline=TARGET_OUTLINE, width=4)
        self.target_id = self.canvas.create_oval(0, 0, 0, 0, fill=TARGET_COLOR, outline="white", width=2)

        self.spawn_target()

    def spawn_target(self) -> None:
        margin = 150
        # Prevent spawning in the bottom 50 pixels to avoid the HUD
        self.target_x = random.randint(margin, self.width - margin)
        self.target_y = random.randint(margin, self.height - margin - 50)
        self.target_spawn_time = time.time()

        self.update_target_visuals()

    def update_target_visuals(self) -> None:
        if self.state != "PLAYING": return

        self.canvas.coords(
            self.target_id,
            self.target_x - self.target_radius, self.target_y - self.target_radius,
            self.target_x + self.target_radius, self.target_y + self.target_radius
        )
        self.canvas.coords(
            self.target_glow_id,
            self.target_x - (self.target_radius*1.3), self.target_y - (self.target_radius*1.3),
            self.target_x + (self.target_radius*1.3), self.target_y + (self.target_radius*1.3)
        )

    def handle_blink(self) -> None:
        if self.state == "START":
            winsound.Beep(800, 200)
            self.start_game()
            return
        elif self.state == "GAMEOVER":
            winsound.Beep(800, 200)
            self.canvas.delete("all")
            self.start_game()
            return

        if self.state == "PLAYING":
            cursor_x, cursor_y = pyautogui.position()
            dist = np.sqrt((cursor_x - self.target_x)**2 + (cursor_y - self.target_y)**2)

            # Hit detection using the forgiveness multiplier (1.5x of current shrinking radius)
            if dist <= self.target_radius * 1.5:
                # HIT!
                self.hits += 1
                time_taken = time.time() - self.target_spawn_time
                self.total_target_time += time_taken

                winsound.Beep(1000, 100)
                self.spawn_target()
            else:
                # MISS! (False Positive)
                self.misses += 1
                winsound.Beep(300, 150)

    def end_game(self) -> None:
        self.state = "GAMEOVER"
        self.canvas.delete("all")

        accuracy = (self.hits / (self.hits + self.misses)) * 100 if (self.hits + self.misses) > 0 else 0

        rank = "C"
        if self.score > 2000 and accuracy > 80: rank = "S"
        elif self.score > 1000 and accuracy > 60: rank = "A"
        elif self.score > 500: rank = "B"

        self.canvas.create_text(
            self.width/2, self.height/2 - 100, text="GAME OVER", fill=ERROR_COLOR, font=("Consolas", 48, "bold")
        )
        self.canvas.create_text(
            self.width/2, self.height/2 - 20, text=f"FINAL SCORE: {self.score}", fill=TARGET_COLOR, font=("Consolas", 36)
        )
        self.canvas.create_text(
            self.width/2, self.height/2 + 30, text=f"ACCURACY: {accuracy:.1f}%", fill=TEXT_COLOR, font=("Consolas", 24)
        )
        self.canvas.create_text(
            self.width/2, self.height/2 + 80, text=f"RANK: {rank}", fill=HIGHLIGHT_COLOR, font=("Consolas", 48, "bold")
        )
        self.canvas.create_text(
            self.width/2, self.height/2 + 150, text="BLINK to play again. ESC to exit.", fill="gray", font=("Consolas", 16)
        )

    def game_loop(self) -> None:
        if self.state == "PLAYING":
            # 1. Update Timer
            self.time_elapsed += 0.033 # roughly 30fps
            # 2. Update HUD
            avg_time = (self.total_target_time / self.hits) if self.hits > 0 else 0.0

            hud_str = (
                f"TIME: {int(self.time_elapsed)}s  |  "
                f"HITS: {self.hits}  |  "
                f"MISSES: {self.misses}  |  "
                f"AVG TIME/TARGET: {avg_time:.2f}s"
            )
            self.canvas.itemconfig(self.hud_text, text=hud_str)

        self.root.after(33, self.game_loop) # 30 fps

    def vision_loop(self) -> None:
        logger.info("Vision loop started.")
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            landmarks = self.extractor.process_frame(rgb_frame)
            if landmarks:
                # Inject target coordinates into controller for telemetry synchronization!
                if self.state == "PLAYING":
                    self.controller.target_x = float(self.target_x)
                    self.controller.target_y = float(self.target_y)
                else:
                    self.controller.target_x = -1.0
                    self.controller.target_y = -1.0

                # This will automatically log the telemetry row including the target!
                self.controller.update(landmarks)

            time.sleep(0.01)

    def run(self) -> None:
        self.root.mainloop()
        self.is_running = False
        if self.cap:
            self.cap.release()
        self.extractor.close()
        self.telemetry.close()

if __name__ == "__main__":
    game = TargetPracticeGame()
    game.run()
