"""EyeNav Vision — Landmark Extraction.
====================================

Wraps MediaPipe FaceLandmarker Tasks API to provide high-precision 478-point
landmarks including iris tracking. Also computes derived features like the
Eye Aspect Ratio (EAR) for blink detection.

ADR Reference: ADR-005 (FaceMesh for Landmarks)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision

    _HAS_MEDIAPIPE = True
except ImportError:
    _HAS_MEDIAPIPE = False

logger = logging.getLogger(__name__)

# MediaPipe standard eye indices (6 points for EAR calculation)
LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]

# Iris centers (when refine_landmarks/output_facial_transformation_matrixes=True)
# Wait, Tasks API guarantees 478 landmarks when we output blendshapes.
LEFT_IRIS_CENTER = 468
RIGHT_IRIS_CENTER = 473


@dataclass
class EyeLandmarks:
    """Extracted eye state from a single frame."""

    left_ear: float
    right_ear: float
    left_pupil: tuple[float, float]  # Normalized (x, y)
    right_pupil: tuple[float, float]  # Normalized (x, y)
    raw_points: np.ndarray  # Shape (478, 2)

    # Computed Heuristics for Demo
    gaze_x: float  # -1 (Left) to 1 (Right)
    gaze_y: float  # -1 (Up) to 1 (Down)
    brow_raise: float  # > 0 means raised, < 0 means furrowed

    # 3D Head Pose (Pitch, Yaw, Roll in degrees, Z in approximate mm/scale)
    head_pitch: float = 0.0
    head_yaw: float = 0.0
    head_roll: float = 0.0
    head_z: float = 0.0


class FaceLandmarkExtractor:
    """Extracts 478-point facial landmarks and derived eye features."""

    def __init__(self, max_faces: int = 1) -> None:
        if not _HAS_MEDIAPIPE:
            raise ImportError(
                "MediaPipe is required for the vision pipeline. Install with: pip install mediapipe"
            )

        # Try to find the task model
        model_path = Path(__file__).resolve().parent.parent.parent.parent / "face_landmarker.task"
        if not model_path.exists():
            # Fallback to current working directory
            model_path = Path("face_landmarker.task")
            if not model_path.exists():
                raise FileNotFoundError(
                    "face_landmarker.task not found! Please download it: "
                    "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
                )

        base_options = python.BaseOptions(model_asset_path=str(model_path))
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=True,  # Implicitly requires 478 landmarks
            output_facial_transformation_matrixes=True,
            num_faces=max_faces,
        )

        self._landmarker = vision.FaceLandmarker.create_from_options(options)

        # State for temporal smoothing (Exponential Moving Average)
        self._smoothed_gaze_x = 0.0
        self._smoothed_gaze_y = 0.0
        self._smoothed_lp: tuple[float, float] | None = None
        self._smoothed_rp: tuple[float, float] | None = None
        self._alpha = 0.05  # Smoothing factor (lower = smoother but more lag)

        # Auto-Calibration State
        self._calibration_frames = 0
        self._gaze_x_baseline_accum = 0.0
        self._gaze_y_baseline_accum = 0.0
        self._brow_baseline_accum = 0.0
        self._eye_dist_accum = 0.0

        self._gaze_x_baseline = 0.0
        self._gaze_y_baseline = 0.0
        self._brow_baseline = None
        self._eye_dist_baseline = None

        logger.info(
            "FaceLandmarkExtractor (Tasks API) initialized. Please look center and neutral for 1 second."
        )

    def process_frame(self, rgb_image: np.ndarray) -> EyeLandmarks | None:
        """Process an RGB image and extract eye landmarks.

        Args:
            rgb_image: Numpy array of shape (H, W, 3) in RGB format.

        Returns:
            EyeLandmarks object if a face is detected, None otherwise.
        """
        # Convert numpy array to MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

        # Process using Tasks API
        detection_result = self._landmarker.detect(mp_image)

        if not detection_result.face_landmarks:
            return None

        # We only process the first face found
        landmarks = detection_result.face_landmarks[0]

        # Convert to numpy array
        points = np.array([[lm.x, lm.y] for lm in landmarks], dtype=np.float32)

        # If the model fails to return the full 478 points
        if len(points) < 478:
            logger.warning("FaceMesh did not return iris landmarks (got %d points).", len(points))
            return None

        left_ear = self._compute_ear(points, LEFT_EYE_INDICES)
        right_ear = self._compute_ear(points, RIGHT_EYE_INDICES)

        # --- Gaze Vector Calculation (Distance/Scale Invariant) ---
        # Gaze X/Y calculation using eye bounding boxes
        left_eye_pts = points[LEFT_EYE_INDICES]
        right_eye_pts = points[RIGHT_EYE_INDICES]

        # Center of eyes
        left_center = np.mean(left_eye_pts, axis=0)
        right_center = np.mean(right_eye_pts, axis=0)

        # Eye width and height for normalization
        left_width = np.linalg.norm(left_eye_pts[0] - left_eye_pts[3])
        left_height = np.linalg.norm(left_eye_pts[1] - left_eye_pts[5])

        # Calculate physical distance proxy (distance between eyes in normalized coordinates)
        eye_dist = float(np.linalg.norm(left_center - right_center))

        # --- Gaze Vector Calculation (Distance/Scale Invariant) ---
        left_gaze_vec = (points[LEFT_IRIS_CENTER] - left_center) / np.array(
            [left_width, left_height]
        )
        right_gaze_vec = (points[RIGHT_IRIS_CENTER] - right_center) / np.array(
            [left_width, left_height]
        )

        # Restore the raw full-image pupil coordinates to preserve the head-navigation macro effect
        raw_lp = (float(points[LEFT_IRIS_CENTER][0]), float(points[LEFT_IRIS_CENTER][1]))
        raw_rp = (float(points[RIGHT_IRIS_CENTER][0]), float(points[RIGHT_IRIS_CENTER][1]))

        # Scale coordinates around the center of the image based on distance from camera
        if self._eye_dist_baseline is not None:
            scale = self._eye_dist_baseline / max(eye_dist, 1e-6)
            left_pupil = (0.5 + (raw_lp[0] - 0.5) * scale, 0.5 + (raw_lp[1] - 0.5) * scale)
            right_pupil = (0.5 + (raw_rp[0] - 0.5) * scale, 0.5 + (raw_rp[1] - 0.5) * scale)
        else:
            left_pupil = raw_lp
            right_pupil = raw_rp

        # Average the two eyes (x is flipped because camera is mirrored)
        # Apply a MASSIVE sensitivity multiplier so minimal eye movement crosses the screen
        SENSITIVITY = 8.0
        raw_gaze_x = float(-(left_gaze_vec[0] + right_gaze_vec[0]) / 2.0) * SENSITIVITY
        raw_gaze_y = float((left_gaze_vec[1] + right_gaze_vec[1]) / 2.0) * SENSITIVITY

        # Brow Raise (distance from eye center to brow inner/outer)
        left_brow_dist = left_center[1] - points[105][1]
        right_brow_dist = right_center[1] - points[334][1]
        brow_raise = float((left_brow_dist / left_height + right_brow_dist / left_height) / 2.0)

        # --- 3D Head Pose Extraction ---
        head_pitch, head_yaw, head_roll, head_z = 0.0, 0.0, 0.0, 0.0
        if detection_result.facial_transformation_matrixes:
            # 4x4 matrix
            trans_mat = detection_result.facial_transformation_matrixes[0]

            # Extract 3x3 rotation matrix
            rmat = trans_mat[0:3, 0:3]

            # Extract translation vector (Z distance is index 2)
            head_z = float(trans_mat[2, 3])

            # Decompose rotation matrix into Euler angles
            angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(rmat)
            head_pitch = float(angles[0])
            head_yaw = float(angles[1])
            head_roll = float(angles[2])

        # Auto-calibration for the first 30 frames
        if self._brow_baseline is None:
            self._calibration_frames += 1
            self._gaze_x_baseline_accum += raw_gaze_x
            self._gaze_y_baseline_accum += raw_gaze_y
            self._brow_baseline_accum += brow_raise
            self._eye_dist_accum += eye_dist

            if self._calibration_frames >= 30:  # 1 second at 30fps
                self._gaze_x_baseline = self._gaze_x_baseline_accum / 30.0
                self._gaze_y_baseline = self._gaze_y_baseline_accum / 30.0
                self._brow_baseline = self._brow_baseline_accum / 30.0
                self._eye_dist_baseline = self._eye_dist_accum / 30.0
                logger.info(
                    "Auto-calibrated. Brow: %.2f, Gaze Center: (%.2f, %.2f), Eye Dist: %.4f",
                    self._brow_baseline,
                    self._gaze_x_baseline,
                    self._gaze_y_baseline,
                    self._eye_dist_baseline,
                )

            # During calibration, return neutral values
            return EyeLandmarks(
                left_ear,
                right_ear,
                left_pupil,
                right_pupil,
                points,
                0.0,
                0.0,
                0.0,
                head_pitch,
                head_yaw,
                head_roll,
                head_z,
            )

        # Apply baseline offsets
        calibrated_gaze_x = raw_gaze_x - self._gaze_x_baseline
        calibrated_gaze_y = raw_gaze_y - self._gaze_y_baseline
        brow_raise_norm = brow_raise - self._brow_baseline

        # Clip to ensure it doesn't fly way off screen
        calibrated_gaze_x = max(-1.0, min(1.0, calibrated_gaze_x))
        calibrated_gaze_y = max(-1.0, min(1.0, calibrated_gaze_y))

        # Apply Temporal Smoothing (EMA)
        self._smoothed_gaze_x = (self._alpha * calibrated_gaze_x) + (
            (1.0 - self._alpha) * self._smoothed_gaze_x
        )
        self._smoothed_gaze_y = (self._alpha * calibrated_gaze_y) + (
            (1.0 - self._alpha) * self._smoothed_gaze_y
        )

        if self._smoothed_lp is None:
            self._smoothed_lp = left_pupil
            self._smoothed_rp = right_pupil
        else:
            self._smoothed_lp = (
                self._alpha * left_pupil[0] + (1 - self._alpha) * self._smoothed_lp[0],
                self._alpha * left_pupil[1] + (1 - self._alpha) * self._smoothed_lp[1],
            )
            self._smoothed_rp = (
                self._alpha * right_pupil[0] + (1 - self._alpha) * self._smoothed_rp[0],
                self._alpha * right_pupil[1] + (1 - self._alpha) * self._smoothed_rp[1],
            )

        return EyeLandmarks(
            left_ear=left_ear,
            right_ear=right_ear,
            left_pupil=self._smoothed_lp,
            right_pupil=self._smoothed_rp,
            raw_points=points,
            gaze_x=self._smoothed_gaze_x,
            gaze_y=self._smoothed_gaze_y,
            brow_raise=brow_raise_norm,
            head_pitch=head_pitch,
            head_yaw=head_yaw,
            head_roll=head_roll,
            head_z=head_z,
        )

    def _compute_ear(self, points: np.ndarray, eye_indices: list[int]) -> float:
        """Computes the Eye Aspect Ratio (EAR) for blink detection.
        EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||).
        """
        p1 = points[eye_indices[0]]
        p2 = points[eye_indices[1]]
        p3 = points[eye_indices[2]]
        p4 = points[eye_indices[3]]
        p5 = points[eye_indices[4]]
        p6 = points[eye_indices[5]]

        # Vertical distances
        v1 = np.linalg.norm(p2 - p6)
        v2 = np.linalg.norm(p3 - p5)

        # Horizontal distance
        h1 = np.linalg.norm(p1 - p4)

        if h1 == 0:
            return 0.0

        return float((v1 + v2) / (2.0 * h1))

    def close(self) -> None:
        """Release MediaPipe resources."""
        self._landmarker.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
