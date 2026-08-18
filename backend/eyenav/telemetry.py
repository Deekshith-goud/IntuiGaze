import csv
import logging
import queue
import threading
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class TelemetryLogger:
    def __init__(self, output_dir="data") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filepath = self.output_dir / f"telemetry_{timestamp}.csv"

        self.queue = queue.Queue()
        self.is_running = True

        # Start background writer thread
        self.writer_thread = threading.Thread(target=self._writer_loop, daemon=True)
        self.writer_thread.start()

        logger.info(f"Telemetry Recorder initialized. Saving to {self.filepath}")

    def log_frame(
        self,
        gaze_x: float,
        gaze_y: float,
        left_ear: float,
        right_ear: float,
        brow_raise: float,
        head_pitch: float,
        head_yaw: float,
        head_roll: float,
        head_z: float,
        cursor_x: float,
        cursor_y: float,
        is_locked: bool,
        is_blinking: bool,
        is_physical_override: bool,
        event_tag: str = "",
        target_x: float = -1.0,
        target_y: float = -1.0,
    ) -> None:
        """Queues a frame of data to be written to CSV."""
        if not self.is_running:
            return

        row = {
            "timestamp": time.time(),
            "gaze_x": round(gaze_x, 4),
            "gaze_y": round(gaze_y, 4),
            "left_ear": round(left_ear, 4),
            "right_ear": round(right_ear, 4),
            "brow_raise": round(brow_raise, 4),
            "head_pitch": round(head_pitch, 4),
            "head_yaw": round(head_yaw, 4),
            "head_roll": round(head_roll, 4),
            "head_z": round(head_z, 4),
            "cursor_x": int(cursor_x),
            "cursor_y": int(cursor_y),
            "target_x": int(target_x),
            "target_y": int(target_y),
            "is_locked": int(is_locked),
            "is_blinking": int(is_blinking),
            "is_physical_override": int(is_physical_override),
            "event_tag": event_tag,
        }
        self.queue.put(row)

    def _writer_loop(self) -> None:
        """Background thread that drains the queue and writes to disk."""
        fieldnames = [
            "timestamp",
            "gaze_x",
            "gaze_y",
            "left_ear",
            "right_ear",
            "brow_raise",
            "head_pitch",
            "head_yaw",
            "head_roll",
            "head_z",
            "cursor_x",
            "cursor_y",
            "target_x",
            "target_y",
            "is_locked",
            "is_blinking",
            "is_physical_override",
            "event_tag",
        ]

        with open(self.filepath, mode="w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            while self.is_running or not self.queue.empty():
                try:
                    row = self.queue.get(timeout=1.0)
                    writer.writerow(row)
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Error writing telemetry: {e}")

    def close(self) -> None:
        self.is_running = False
        self.writer_thread.join(timeout=2.0)
        logger.info("Telemetry Recorder shut down cleanly.")
