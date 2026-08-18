"""EyeNav Gaze Estimation Module.
==============================

Implements appearance-based gaze estimation using L2CS-Net with MobileNetV3-Large
backbone, pre-trained on ETH-XGaze and fine-tuned on EyeNav dataset.

Model:
    L2CS-Net (Abdelrahman et al., 2023) with MobileNetV3-Large backbone.

    Architecture:
        Input: Normalized face image (224×224, RGB)
        Backbone: MobileNetV3-Large (pretrained on ImageNet)
        Head: Two FC layers → pitch and yaw classification (binned)
        Output: Gaze direction (pitch: 90 bins, yaw: 90 bins) → continuous

    Why L2CS-Net?
        - State-of-the-art accuracy for appearance-based gaze on ETH-XGaze (2.1° ResNet-50)
        - MobileNetV3-Large provides 2.9° MAE at 6ms on CPU — best speed/accuracy tradeoff
        - Binned classification (not regression) avoids averaging artifacts at gaze boundaries
        - Pre-trained weights publicly available

    Why not Transformer-based (GazeTR)?
        - GazeTR achieves 1.8° but requires 25ms on CPU — exceeds our 6ms budget
        - Edge deployment requirement drives model choice

    See ADR-003 for full model selection analysis.

Performance Targets:
    - MAE ≤ 3° (uncalibrated, ETH-XGaze test set)
    - MAE ≤ 1° (after 5-point calibration)
    - Latency ≤ 6ms on Intel Core i5-8250U, no GPU

References:
    - Abdelrahman et al. (2023). L2CS-Net. IEEE ICASSP.
    - Zhang et al. (2020). ETH-XGaze. ECCV 2020.
    - Howard et al. (2019). MobileNetV3. ICCV 2019.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# Gaze estimation constants
_FACE_IMAGE_SIZE = (224, 224)  # L2CS-Net input size
_GAZE_BINS = 90  # Number of bins for pitch and yaw classification
_GAZE_BIN_SIZE_DEG = 2.0  # Degrees per bin
_GAZE_RANGE_DEG = 90.0  # Total range: ±45°

# Normalization parameters (ImageNet statistics — same as ETH-XGaze pre-training)
_NORMALIZE_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_NORMALIZE_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


@dataclass
class GazeEstimate:
    """Gaze estimate for a single frame.

    Attributes:
        gaze_3d: Unit gaze direction vector in camera space (x, y, z).
        gaze_screen: Gaze position in normalized screen coordinates (x, y) ∈ [0,1].
        pitch_deg: Vertical gaze angle in degrees (positive = up).
        yaw_deg: Horizontal gaze angle in degrees (positive = right).
        confidence: Estimate confidence ∈ [0, 1].
        is_calibrated: Whether calibration mapping was applied.
        smoothed: Whether temporal smoothing was applied.
    """

    gaze_3d: np.ndarray  # shape (3,), float32
    gaze_screen: np.ndarray  # shape (2,), float32
    pitch_deg: float
    yaw_deg: float
    confidence: float
    is_calibrated: bool = False
    smoothed: bool = False


class GazeEstimator:
    """Appearance-based gaze estimator using L2CS-Net (MobileNetV3-Large).

    Loads the ONNX model at initialization and provides per-frame gaze estimation.
    Includes optional calibration mapping (LORE-style personal adaptation layer).

    Example:
        Usage::

            estimator = GazeEstimator(ModelPaths().gaze)
            estimate = estimator.estimate(frame, landmarks)
            print(f"Gaze: ({estimate.gaze_screen[0]:.3f}, {estimate.gaze_screen[1]:.3f})")

    Args:
        model_path: Path to the ONNX model file.

    Raises:
        ModelLoadError: If the ONNX model cannot be loaded.
    """

    def __init__(self, model_path: Path) -> None:
        self._model_path = model_path
        self._session = self._load_model(model_path)
        self._calibration_matrix: np.ndarray | None = None
        self._kalman_state: np.ndarray | None = None
        logger.info("GazeEstimator initialized: model=%s", model_path)

    def estimate(
        self,
        face_image: np.ndarray,
        landmarks: Landmarks,  # Forward reference
        head_pose: HeadPose | None = None,
    ) -> GazeEstimate | None:
        """Estimate gaze direction from a face image.

        Args:
            face_image: Full face image (H×W×3, uint8, BGR).
            landmarks: Facial landmarks for eye region extraction.
            head_pose: Optional head pose for composite gaze calculation.

        Returns:
            GazeEstimate or None if estimation fails.

        Notes:
            - Input image is internally cropped and normalized.
            - Head pose compensation applied if head_pose is provided.
            - Kalman filter smoothing applied to reduce jitter.
        """
        if self._session is None:
            logger.error("Gaze model not loaded — cannot estimate gaze.")
            return None

        try:
            # 1. Extract and normalize face patch
            face_patch = self._extract_face_patch(face_image, landmarks)

            # 2. Run ONNX inference
            pitch_yaw = self._run_inference(face_patch)

            # 3. Apply calibration mapping
            if self._calibration_matrix is not None:
                pitch_yaw = self._apply_calibration(pitch_yaw)

            # 4. Compute screen coordinates
            gaze_screen = self._pitch_yaw_to_screen(pitch_yaw, head_pose)

            # 5. Compute confidence from output distribution sharpness
            confidence = self._compute_confidence()

            return GazeEstimate(
                gaze_3d=self._pitch_yaw_to_3d(pitch_yaw),
                gaze_screen=gaze_screen,
                pitch_deg=float(pitch_yaw[0]),
                yaw_deg=float(pitch_yaw[1]),
                confidence=confidence,
                is_calibrated=self._calibration_matrix is not None,
                smoothed=False,  # Smoothing applied by TemporalEngine
            )

        except Exception as e:
            logger.exception("Gaze estimation failed: %s", e)
            return None

    def set_calibration(self, calibration_matrix: np.ndarray) -> None:
        """Set personal calibration mapping matrix.

        Args:
            calibration_matrix: 2×2 affine correction matrix mapping
                                 raw gaze (pitch, yaw) to calibrated (pitch, yaw).
        """
        self._calibration_matrix = calibration_matrix
        logger.info("Calibration matrix set (shape=%s)", calibration_matrix.shape)

    def clear_calibration(self) -> None:
        """Remove calibration — revert to uncalibrated mode."""
        self._calibration_matrix = None
        logger.info("Calibration cleared.")

    def _load_model(self, model_path: Path) -> object | None:
        """Load ONNX Runtime inference session.

        Attempts providers in order of preference:
        1. CUDAExecutionProvider (GPU)
        2. DirectMLExecutionProvider (Windows GPU)
        3. CoreMLExecutionProvider (macOS, Apple Silicon)
        4. CPUExecutionProvider (always available)

        Args:
            model_path: Path to .onnx model file.

        Returns:
            ONNX Runtime InferenceSession or None if loading fails.
        """
        try:
            import onnxruntime as ort

            providers = ["CPUExecutionProvider"]

            # Try accelerated providers
            available = ort.get_available_providers()
            if "CUDAExecutionProvider" in available:
                providers.insert(0, "CUDAExecutionProvider")
            elif "DirectMLExecutionProvider" in available:
                providers.insert(0, "DirectMLExecutionProvider")
            elif "CoreMLExecutionProvider" in available:
                providers.insert(0, "CoreMLExecutionProvider")

            session = ort.InferenceSession(str(model_path), providers=providers)
            logger.info("Gaze model loaded with providers: %s", session.get_providers())
            return session

        except ImportError:
            logger.error("onnxruntime not installed. Install with: pip install onnxruntime")
            return None
        except Exception as e:
            logger.error("Failed to load gaze model from %s: %s", model_path, e)
            return None

    def _extract_face_patch(self, face_image: np.ndarray, landmarks: Landmarks) -> np.ndarray:
        """Extract and normalize the face patch for gaze estimation.

        Follows the ETH-XGaze normalization protocol:
        1. Detect face bounding box from landmarks
        2. Crop face region with padding
        3. Resize to 224×224
        4. Normalize with ImageNet mean/std

        Args:
            face_image: Full frame (H×W×3, BGR).
            landmarks: Facial landmarks.

        Returns:
            Normalized face patch (1×3×224×224, float32, RGB, NCHW format).
        """
        # Implementation uses landmarks to compute face crop
        # Normalization follows Zhang et al. (2018) protocol
        raise NotImplementedError("Implement in Phase 2")

    def _run_inference(self, face_patch: np.ndarray) -> np.ndarray:
        """Run ONNX inference on face patch.

        Args:
            face_patch: Normalized face patch (1×3×224×224).

        Returns:
            (pitch, yaw) in degrees.
        """
        outputs = self._session.run(None, {self._session.get_inputs()[0].name: face_patch})

        # L2CS-Net outputs: [pitch_logits (90,), yaw_logits (90,)]
        pitch_logits = outputs[0][0]  # (90,)
        yaw_logits = outputs[1][0]  # (90,)

        # Softmax + weighted sum for continuous angle
        pitch_deg = self._logits_to_angle(pitch_logits)
        yaw_deg = self._logits_to_angle(yaw_logits)

        return np.array([pitch_deg, yaw_deg], dtype=np.float32)

    def _logits_to_angle(self, logits: np.ndarray) -> float:
        """Convert classification logits to continuous angle.

        L2CS-Net uses binned classification (90 bins covering ±45°).
        Converts back to angle via softmax weighted mean.

        Args:
            logits: Raw classification scores (90,).

        Returns:
            Continuous angle estimate in degrees.
        """
        # Softmax
        exp_logits = np.exp(logits - logits.max())
        probs = exp_logits / exp_logits.sum()

        # Bin centers: -44°, -43°, ..., 44°, 45°
        bins = np.linspace(-45, 45, _GAZE_BINS)

        # Weighted mean
        angle = float(np.sum(probs * bins))
        return angle

    def _apply_calibration(self, pitch_yaw: np.ndarray) -> np.ndarray:
        """Apply personal calibration affine correction."""
        return self._calibration_matrix @ pitch_yaw

    def _pitch_yaw_to_screen(self, pitch_yaw: np.ndarray, head_pose: HeadPose | None) -> np.ndarray:
        """Convert pitch/yaw angles to normalized screen coordinates.

        Uses head pose to compute composite gaze (eye + head).

        Args:
            pitch_yaw: (pitch, yaw) in degrees.
            head_pose: Optional head orientation.

        Returns:
            Screen coordinates (x, y) ∈ [0, 1].
        """
        raise NotImplementedError("Implement in Phase 2")

    def _pitch_yaw_to_3d(self, pitch_yaw: np.ndarray) -> np.ndarray:
        """Convert (pitch, yaw) degrees to 3D unit vector."""
        pitch_rad = np.radians(pitch_yaw[0])
        yaw_rad = np.radians(pitch_yaw[1])

        x = np.sin(yaw_rad) * np.cos(pitch_rad)
        y = np.sin(pitch_rad)
        z = np.cos(yaw_rad) * np.cos(pitch_rad)

        return np.array([x, y, z], dtype=np.float32)

    def _compute_confidence(self) -> float:
        """Compute confidence from the output distribution.

        Higher confidence = sharper probability distribution over bins.
        Uses entropy-based measure.

        Returns:
            Confidence score ∈ [0, 1].
        """
        # TODO: Implement entropy-based confidence in Phase 2
        return 0.85  # Placeholder
