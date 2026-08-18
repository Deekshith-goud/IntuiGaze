import csv
import logging
import random
import sys
import threading
import time
import tkinter as tk
import winsound
from collections import deque
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

# Add project root to path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.eyenav.vision.landmarks import FaceLandmarkExtractor
from scripts.run_desktop import get_valid_camera

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CalibrationML")

class CalibrationEngine:
    def __init__(self, num_targets=50) -> None:
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg="#000000")
        self.root.config(cursor="none") # Hide physical mouse cursor

        # Bind keys
        self.root.bind('<Escape>', lambda e: self.close())
        self.root.bind('<space>', self.on_space_pressed)

        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()

        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg="#000000", highlightthickness=0)
        self.canvas.pack()

        # State
        self.num_targets = num_targets
        self.targets_completed = 0
        self.target_x = -1.0
        self.target_y = -1.0
        self.target_radius = 25

        self.is_running = True
        self.frame_history = deque(maxlen=15) # Last 15 frames of geometry (0.5 seconds)

        # Prepare CSV
        Path("data").mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_path = Path("data") / f"calibration_{timestamp}.csv"

        with open(self.csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['gaze_x', 'gaze_y', 'head_pitch', 'head_yaw', 'head_roll', 'target_x', 'target_y'])

        # UI Elements
        self.target_id = self.canvas.create_oval(0, 0, 0, 0, fill="#00FF00", outline="white", width=2)
        self.text_id = self.canvas.create_text(
            self.width/2, self.height/2,
            text="Look at the dot.\nPress SPACEBAR to lock coordinate.\nPress ESC to exit.",
            fill="white", font=("Consolas", 24), justify="center"
        )

        # Start Camera
        self.cap = get_valid_camera()
        if not self.cap:
            logger.error("No camera found.")
            sys.exit(1)

        self.extractor = FaceLandmarkExtractor(max_faces=1)
        self.vision_thread = threading.Thread(target=self.vision_loop)
        self.vision_thread.daemon = True
        self.vision_thread.start()

        self.spawn_target()

    def spawn_target(self) -> None:
        margin = 100
        self.target_x = random.randint(margin, self.width - margin)
        self.target_y = random.randint(margin, self.height - margin)

        self.canvas.coords(
            self.target_id,
            self.target_x - self.target_radius, self.target_y - self.target_radius,
            self.target_x + self.target_radius, self.target_y + self.target_radius
        )

        # Clear the history so they can't spam spacebar instantly using old gaze data
        self.frame_history.clear()

    def on_space_pressed(self, event) -> None:
        if len(self.frame_history) < 15:
            # Need to look at it for at least 0.5s to gather enough data
            winsound.Beep(300, 100)
            return

        # 1. Average the last 15 frames for perfect, jitter-free ground truth
        data_matrix = np.array(self.frame_history)
        avg_gaze_x, avg_gaze_y, avg_pitch, avg_yaw, avg_roll = np.mean(data_matrix, axis=0)

        # 2. Save to CSV
        with open(self.csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([avg_gaze_x, avg_gaze_y, avg_pitch, avg_yaw, avg_roll, self.target_x, self.target_y])

        # 3. UI Feedback
        self.targets_completed += 1
        winsound.Beep(1000, 100)

        if self.targets_completed >= self.num_targets:
            self.canvas.delete("all")
            self.canvas.create_text(
                self.width/2, self.height/2,
                text=f"CALIBRATION COMPLETE!\nSaved {self.num_targets} coordinates.\nPress ESC to close.",
                fill="#00FF00", font=("Consolas", 36), justify="center"
            )
        else:
            self.canvas.itemconfig(self.text_id, text=f"Progress: {self.targets_completed} / {self.num_targets}")
            self.spawn_target()

    def vision_loop(self) -> None:
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret: break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            landmarks = self.extractor.process_frame(rgb_frame)

            if landmarks:
                self.frame_history.append([
                    landmarks.gaze_x,
                    landmarks.gaze_y,
                    landmarks.head_pitch,
                    landmarks.head_yaw,
                    landmarks.head_roll
                ])

            time.sleep(0.01)

    def close(self) -> None:
        self.is_running = False
        self.root.quit()
        if self.cap: self.cap.release()
        self.extractor.close()

if __name__ == "__main__":
    app = CalibrationEngine(num_targets=50)
    app.root.mainloop()
