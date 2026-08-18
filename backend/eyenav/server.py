"""EyeNav API Server.
=================

FastAPI server that streams live eye tracking data over WebSockets
to the Next.js frontend UI.
"""

import asyncio
import json
import logging
import sys

import cv2
import numpy as np
from backend.eyenav.vision.landmarks import FaceLandmarkExtractor
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="EyeNav Stream Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BLINK_THRESHOLD = 0.20


def get_valid_camera():
    """Scans for a valid non-black camera feed."""
    for index in range(4):
        cap = (
            cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if sys.platform.startswith("win")
            else cv2.VideoCapture(index)
        )
        if not cap.isOpened():
            cap.release()
            continue

        for _ in range(5):
            ret, frame = cap.read()

        if ret and frame is not None and np.sum(frame) > 0:
            return cap
        cap.release()
    return None


class VisionEngine:
    def __init__(self) -> None:
        self.extractor = FaceLandmarkExtractor(max_faces=1)
        self.cap = get_valid_camera()
        if self.cap is None:
            logger.error("Failed to find valid webcam!")

    def read_state(self) -> dict:
        if self.cap is None:
            return {"error": "no_camera"}

        ret, frame = self.cap.read()
        if not ret:
            return {"error": "frame_read_failed"}

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        landmarks = self.extractor.process_frame(rgb_frame)

        if landmarks is None:
            return {"error": "no_face"}

        is_blinking = (landmarks.left_ear < BLINK_THRESHOLD) and (
            landmarks.right_ear < BLINK_THRESHOLD
        )

        brow_state = "NEUTRAL"
        if landmarks.brow_raise > 0.4:
            brow_state = "RAISED"
        elif landmarks.brow_raise < -0.2:
            brow_state = "FURROWED"

        return {
            "gaze_x": landmarks.gaze_x,
            "gaze_y": landmarks.gaze_y,
            "is_blinking": is_blinking,
            "brow_state": brow_state,
            "brow_raise_val": landmarks.brow_raise,
            "left_ear": landmarks.left_ear,
            "right_ear": landmarks.right_ear,
        }

    def close(self) -> None:
        if self.cap:
            self.cap.release()
        self.extractor.close()


# Global engine instance
vision_engine = None


@app.on_event("startup")
async def startup_event() -> None:
    global vision_engine
    logger.info("Initializing Vision Engine...")
    vision_engine = VisionEngine()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    global vision_engine
    if vision_engine:
        logger.info("Shutting down Vision Engine...")
        vision_engine.close()


@app.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    logger.info("Frontend connected to /stream")
    try:
        while True:
            # Run the vision processing in a background thread to avoid blocking asyncio
            state = await asyncio.to_thread(vision_engine.read_state)

            await websocket.send_text(json.dumps(state))

            # Send at ~30 FPS
            await asyncio.sleep(1.0 / 30.0)

    except WebSocketDisconnect:
        logger.info("Frontend disconnected")
    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
