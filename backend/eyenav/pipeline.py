"""EyeNav Pipeline — Main Orchestration Module.
============================================

This module contains the EyeNavPipeline class, which orchestrates the entire
vision pipeline from camera acquisition to OS command execution.

Design:
    The pipeline is designed as a staged processor where each stage:
    - Has a defined latency budget
    - Can fail gracefully without crashing the pipeline
    - Emits Prometheus metrics for observability
    - Is independently replaceable (strategy pattern)

Pipeline Timing Budget (30ms total at 30fps):
    Camera acquisition:      0–2ms
    Face detection:          2–5ms
    Landmark extraction:     5–9ms
    Eye analysis (parallel): 9–20ms
    Feature assembly:        20–21ms
    Intent recognition:      21–29ms
    Safety filter:           29–30ms
    Command execution:       30ms+

Failure Modes:
    - Camera disconnect: Pipeline pauses, waits for reconnection
    - Face not detected: Continues with last known pose (up to 500ms)
    - Model inference error: Logs error, skips frame, does not crash
    - Safety filter error: BLOCKS command (fail-safe behavior)
    - OS command error: Logs error, notifies UI, continues

References:
    - docs/architecture/SYSTEM_ARCHITECTURE.md
    - docs/architecture/ML_ARCHITECTURE.md
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

from eyenav.camera import CameraManager, Frame
from eyenav.commands import CommandRouter
from eyenav.config import Config
from eyenav.intent import IntentEngine, IntentPrediction
from eyenav.metrics import MetricsCollector
from eyenav.os_integration import OSIntegration
from eyenav.safety import SafetyFilter, VerifiedCommand
from eyenav.temporal import TemporalEngine
from eyenav.vision.blink import BlinkDetector, BlinkEvent
from eyenav.vision.eyebrow import EyebrowDetector, EyebrowState
from eyenav.vision.face_detection import FaceDetection, FaceDetector
from eyenav.vision.gaze import GazeEstimate, GazeEstimator
from eyenav.vision.head_pose import HeadPose, HeadPoseEstimator
from eyenav.vision.landmarks import LandmarkExtractor, Landmarks
from eyenav.vision.pupil import PupilLocalizer, PupilState

logger = logging.getLogger(__name__)


@dataclass
class PipelineState:
    """Immutable snapshot of the pipeline state at a given frame.

    This dataclass accumulates outputs from each pipeline stage.
    It is created fresh each frame and never mutated after assembly.

    Attributes:
        frame: The raw camera frame.
        face_detection: Result of face detection stage.
        landmarks: Extracted facial landmarks (468 points).
        gaze: Gaze estimate for this frame.
        blink: Blink event detected this frame (None if no blink).
        pupil: Pupil state for both eyes.
        eyebrow: Eyebrow state.
        head_pose: 6-DOF head pose.
        intent: Intent prediction from temporal engine.
        command: Verified command (may be None if blocked by safety).
        processing_time_ms: Total pipeline processing time.
    """

    frame: Frame
    face_detection: FaceDetection | None = None
    landmarks: Landmarks | None = None
    gaze: GazeEstimate | None = None
    blink: BlinkEvent | None = None
    pupil: PupilState | None = None
    eyebrow: EyebrowState | None = None
    head_pose: HeadPose | None = None
    intent: IntentPrediction | None = None
    command: VerifiedCommand | None = None
    processing_time_ms: float = 0.0


class EyeNavPipeline:
    """Main EyeNav processing pipeline.

    Orchestrates all pipeline stages from camera acquisition to command execution.
    Designed for edge deployment — all inference runs locally via ONNX Runtime.

    Example:
        Basic usage::

            config = Config.from_file("configs/default.yaml")
            pipeline = EyeNavPipeline(config)

            with pipeline:
                pipeline.calibrate(mode="5_point")
                pipeline.start()
                # Pipeline runs on background thread
                time.sleep(60)

    Args:
        config: EyeNav configuration object.

    Raises:
        CameraError: If the camera cannot be initialized.
        ModelLoadError: If any ONNX model fails to load.

    Notes:
        - Pipeline runs on a dedicated background thread.
        - All public methods are thread-safe.
        - Metrics are exposed via Prometheus if enabled in config.
    """

    def __init__(self, config: Config) -> None:
        self._config = config
        self._running = False
        self._thread: threading.Thread | None = None
        self._state_callbacks: list[Callable[[PipelineState], None]] = []
        self._metrics = MetricsCollector(enabled=config.metrics.enabled)

        # Initialize all pipeline components
        logger.info("Initializing EyeNav pipeline...")
        self._camera = CameraManager(config.camera)
        self._face_detector = FaceDetector(config.models.face_detection)
        self._landmark_extractor = LandmarkExtractor(config.models.landmarks)
        self._gaze_estimator = GazeEstimator(config.models.gaze)
        self._blink_detector = BlinkDetector(config.models.blink)
        self._pupil_localizer = PupilLocalizer(config.models.pupil)
        self._eyebrow_detector = EyebrowDetector(config.models.eyebrow)
        self._head_pose_estimator = HeadPoseEstimator()
        self._temporal_engine = TemporalEngine(config.temporal)
        self._intent_engine = IntentEngine(config.models.intent)
        self._safety_filter = SafetyFilter(config.safety)
        self._command_router = CommandRouter(config.commands)
        self._os_integration = OSIntegration(config.os)

        logger.info("Pipeline initialized successfully.")

    def __enter__(self) -> EyeNavPipeline:
        """Context manager entry — starts pipeline resources."""
        self._camera.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit — safely shuts down pipeline."""
        self.stop()
        self._camera.close()

    def start(self) -> None:
        """Start the pipeline on a background thread.

        The pipeline processes frames continuously until stop() is called.

        Raises:
            RuntimeError: If the pipeline is already running.
            CameraError: If the camera cannot start capturing.
        """
        if self._running:
            raise RuntimeError("Pipeline is already running.")

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, name="eyenav-pipeline", daemon=True)
        self._thread.start()
        logger.info("Pipeline started on background thread.")

    def stop(self) -> None:
        """Stop the pipeline gracefully.

        Waits for the current frame to finish processing before stopping.
        """
        if not self._running:
            return

        logger.info("Stopping pipeline...")
        self._running = False

        if self._thread is not None:
            self._thread.join(timeout=5.0)
            if self._thread.is_alive():
                logger.warning("Pipeline thread did not stop within timeout.")

        logger.info("Pipeline stopped.")

    def calibrate(self, mode: str = "5_point", profile_name: str = "default") -> bool:
        """Run the calibration wizard.

        Args:
            mode: Calibration mode. One of:
                - "uncalibrated": No calibration, immediate use
                - "5_point": Rapid 5-point (<30 seconds)
                - "13_point": Full 13-point (<90 seconds)
            profile_name: Name to save the calibration profile under.

        Returns:
            True if calibration succeeded and meets accuracy threshold.

        Notes:
            This method blocks until calibration is complete.
            The calibration wizard will display points on screen.
        """
        logger.info(f"Starting calibration: mode={mode}")
        # Calibration implementation delegated to CalibrationManager
        # See eyenav/calibration.py
        raise NotImplementedError("Calibration to be implemented in Phase 2")

    def add_state_callback(self, callback: Callable[[PipelineState], None]) -> None:
        """Register a callback to receive pipeline state updates.

        The callback is called after each frame is processed. Use this to:
        - Build custom UI overlays
        - Log pipeline state for research
        - Integrate with external systems

        Args:
            callback: Function accepting a PipelineState. Must not block.

        Notes:
            Callbacks run on the pipeline thread. Keep them fast (<1ms).
            Heavy processing should be done on a separate thread.
        """
        self._state_callbacks.append(callback)

    def _run_loop(self) -> None:
        """Main pipeline processing loop.

        Runs on the pipeline background thread. Processes frames until
        self._running is set to False.

        This method handles all per-frame processing and graceful error recovery.
        """
        logger.info("Pipeline loop starting.")

        while self._running:
            frame_start = time.perf_counter()

            try:
                frame = self._camera.read_frame()
                if frame is None:
                    logger.debug("No frame available — skipping.")
                    continue

                state = self._process_frame(frame)

                # Execute command if verified
                if state.command and not state.command.blocked:
                    self._os_integration.execute(state.command)

                # Notify callbacks
                for callback in self._state_callbacks:
                    try:
                        callback(state)
                    except Exception as e:
                        logger.error(f"State callback raised exception: {e}")

                # Record metrics
                elapsed_ms = (time.perf_counter() - frame_start) * 1000
                self._metrics.record_frame_time(elapsed_ms)

            except Exception as e:
                logger.exception(f"Unexpected pipeline error: {e}")
                # Continue processing — do not crash the pipeline
                time.sleep(0.01)

        logger.info("Pipeline loop ended.")

    def _process_frame(self, frame: Frame) -> PipelineState:
        """Process a single frame through the entire pipeline.

        Args:
            frame: Raw camera frame.

        Returns:
            PipelineState containing all stage outputs for this frame.

        Notes:
            Stages are run sequentially. Eye analysis sub-stages may run
            in parallel threads in a future optimization.
        """
        t0 = time.perf_counter()
        state = PipelineState(frame=frame)

        # Stage 1: Face Detection
        state.face_detection = self._face_detector.detect(frame.data)
        if state.face_detection is None or not state.face_detection.detected:
            return state  # No face — skip remaining stages

        # Stage 2: Landmark Extraction
        state.landmarks = self._landmark_extractor.extract(frame.data, state.face_detection.bbox)
        if state.landmarks is None:
            return state

        # Stage 3: Eye Analysis (sequential — parallelization in v2)
        state.gaze = self._gaze_estimator.estimate(frame.data, state.landmarks)
        state.blink = self._blink_detector.detect(state.landmarks)
        state.pupil = self._pupil_localizer.localize(state.landmarks)
        state.eyebrow = self._eyebrow_detector.detect(state.landmarks)
        state.head_pose = self._head_pose_estimator.estimate(state.landmarks, frame)

        # Stage 4: Temporal Feature Assembly
        feature_vector = self._temporal_engine.assemble_features(state)
        self._temporal_engine.add_frame(feature_vector)

        # Stage 5: Intent Recognition (only when buffer is full)
        if self._temporal_engine.is_ready():
            feature_buffer = self._temporal_engine.get_buffer()
            state.intent = self._intent_engine.predict(feature_buffer)

        # Stage 6: Safety Filter
        if state.intent is not None:
            state.command = self._safety_filter.evaluate(state.intent)

        state.processing_time_ms = (time.perf_counter() - t0) * 1000
        return state
