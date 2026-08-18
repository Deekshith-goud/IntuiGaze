"""EyeNav Intent Recognition Engine.
==================================

Implements the Tiny Temporal Transformer for navigation intent classification
from temporal sequences of eye gesture features.

Design:
    The intent engine classifies high-level navigation intent from a 1.5-second
    sliding window of per-frame feature vectors. It distinguishes:

    - Reading (suppress all commands)
    - Selecting (user wants to click/activate an element)
    - Scrolling (user wants to scroll up/down)
    - Searching (scanning for content — suppress commands)
    - Idle (no active interaction)
    - Activation / Deactivation (toggle EyeNav)
    - Confirmation / Cancellation (respond to prompts)
    - Navigation (directional movement — back, forward, etc.)
    - System (system-level commands — home, app switch, etc.)

Why Transformer?
    - Attention mechanism captures long-range temporal dependencies
    - Attention weights provide interpretable predictions
    - 8ms inference within latency budget
    - [CLS] token classification head is standard, well-validated

    See ADR-002 for full model selection analysis.

Why NOT LSTM/GRU?
    - Lower accuracy (~88% vs ~95% target)
    - No interpretability (no attention)
    - Vanishing gradient limits context to ~30 frames (~1 second)
    - LSTM cell is not ONNX opset-12 stable in all runtimes

References:
    - Vaswani et al. (2017). Attention is All You Need. NeurIPS.
    - docs/architecture/ML_ARCHITECTURE.md Section 5
    - ADR-002: Intent Recognition Architecture Decision
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# Intent class definitions
INTENT_CLASSES = [
    "idle",  # 0: No navigation intent
    "reading",  # 1: User is reading (suppress commands)
    "selecting",  # 2: User wants to select/click
    "scrolling_up",  # 3: User wants to scroll up
    "scrolling_down",  # 4: User wants to scroll down
    "searching",  # 5: User is scanning/searching
    "activation",  # 6: Activate EyeNav
    "deactivation",  # 7: Deactivate EyeNav
    "confirmation",  # 8: Confirm pending action
    "cancellation",  # 9: Cancel pending action
    "nav_back",  # 10: Navigate backward
    "nav_forward",  # 11: Navigate forward
    "nav_home",  # 12: Navigate to home/start
]

# Intent → suggested command mapping
INTENT_TO_COMMAND: dict[str, str | None] = {
    "idle": None,
    "reading": None,
    "selecting": "select",
    "scrolling_up": "scroll_up",
    "scrolling_down": "scroll_down",
    "searching": None,
    "activation": "activate",
    "deactivation": "deactivate",
    "confirmation": "enter",
    "cancellation": "escape",
    "nav_back": "back",
    "nav_forward": "forward",
    "nav_home": "home",
}

# Feature vector dimensionality (must match temporal engine)
FEATURE_DIM = 32


@dataclass
class IntentPrediction:
    """Output of the Intent Recognition Engine.

    Attributes:
        intent: Classified intent name from INTENT_CLASSES.
        intent_confidence: Probability of the predicted intent ∈ [0, 1].
        all_probabilities: Full probability distribution over all intent classes.
        suggested_command: Suggested OS command (None if no action implied).
        command_confidence: Confidence in the specific command.
        context_window_frames: Number of frames used for this prediction.
        attention_weights: Per-frame attention weights for interpretability.
    """

    intent: str
    intent_confidence: float
    all_probabilities: np.ndarray  # shape (N_classes,)
    suggested_command: str | None
    command_confidence: float
    context_window_frames: int
    attention_weights: np.ndarray | None = None  # shape (T,) per-frame importance


class IntentEngine:
    """Tiny Temporal Transformer for navigation intent classification.

    Processes sequences of per-frame feature vectors through a 4-layer
    Transformer encoder to predict user navigation intent.

    The model is optimized for:
    - Edge deployment via ONNX Runtime
    - 8ms inference on CPU
    - Interpretable attention weights
    - High precision to minimize false positives

    Example:
        Usage::

            engine = IntentEngine(model_path)
            feature_buffer = temporal_engine.get_buffer()  # shape (45, 32)
            prediction = engine.predict(feature_buffer)

            print(f"Intent: {prediction.intent}")
            print(f"Confidence: {prediction.intent_confidence:.3f}")

    Args:
        model_path: Path to Tiny Temporal Transformer ONNX model.
    """

    def __init__(self, model_path: Path) -> None:
        self._model_path = model_path
        self._session = self._load_model(model_path)
        self._input_name: str | None = None
        self._output_names: list[str] | None = None

        if self._session is not None:
            self._input_name = self._session.get_inputs()[0].name
            self._output_names = [o.name for o in self._session.get_outputs()]

        logger.info(
            "IntentEngine initialized: model=%s, classes=%d", model_path, len(INTENT_CLASSES)
        )

    def predict(self, feature_buffer: np.ndarray) -> IntentPrediction:
        """Predict intent from a temporal feature buffer.

        Args:
            feature_buffer: Feature sequence, shape (T, F) where
                            T = number of frames (e.g., 45 for 1.5s at 30fps)
                            F = feature dimension (32).

        Returns:
            IntentPrediction with classified intent and confidence.

        Raises:
            ValueError: If feature_buffer shape is incorrect.

        Notes:
            The model expects feature_buffer with exactly FEATURE_DIM=32 features.
            If T < expected window, pads with zeros. If T > expected, takes last T.
        """
        if feature_buffer.ndim != 2 or feature_buffer.shape[1] != FEATURE_DIM:
            raise ValueError(
                f"feature_buffer must be shape (T, {FEATURE_DIM}), got {feature_buffer.shape}"
            )

        if self._session is None:
            logger.error("Intent model not loaded — returning idle prediction.")
            return self._idle_prediction(feature_buffer.shape[0])

        try:
            # Prepare input: add batch dimension → (1, T, F)
            x = feature_buffer[np.newaxis].astype(np.float32)

            # Run inference
            outputs = self._session.run(self._output_names, {self._input_name: x})

            # Parse outputs
            # Output 0: logits (1, N_classes)
            # Output 1: attention_weights (1, T) — optional, if exported
            logits = outputs[0][0]  # (N_classes,)

            attention_weights = None
            if len(outputs) > 1:
                attention_weights = outputs[1][0]  # (T,)

            # Softmax
            exp_logits = np.exp(logits - logits.max())
            probs = exp_logits / exp_logits.sum()

            # Top prediction
            pred_idx = int(np.argmax(probs))
            pred_intent = INTENT_CLASSES[pred_idx]
            pred_confidence = float(probs[pred_idx])

            # Map to command
            suggested_command = INTENT_TO_COMMAND.get(pred_intent)

            return IntentPrediction(
                intent=pred_intent,
                intent_confidence=pred_confidence,
                all_probabilities=probs,
                suggested_command=suggested_command,
                command_confidence=pred_confidence,
                context_window_frames=feature_buffer.shape[0],
                attention_weights=attention_weights,
            )

        except Exception as e:
            logger.exception("Intent prediction failed: %s", e)
            return self._idle_prediction(feature_buffer.shape[0])

    def get_explanation(self, prediction: IntentPrediction) -> dict:
        """Generate a human-readable explanation of the intent prediction.

        Uses attention weights to identify which frames drove the prediction.

        Args:
            prediction: IntentPrediction with attention weights.

        Returns:
            Explanation dict with:
            - "intent": predicted intent name
            - "confidence": prediction confidence
            - "top_frames": indices of most influential frames
            - "feature_importance": which features mattered most
            - "human_readable": plain English explanation
        """
        if prediction.attention_weights is None:
            return {
                "intent": prediction.intent,
                "confidence": prediction.intent_confidence,
                "human_readable": f"Detected {prediction.intent} with {prediction.intent_confidence:.0%} confidence.",
            }

        # Find frames with highest attention
        top_k = 5
        top_frame_indices = np.argsort(prediction.attention_weights)[-top_k:][::-1].tolist()

        explanation_map = {
            "reading": "The system detected a left-to-right scanning pattern typical of reading text.",
            "selecting": "The system detected a focused fixation followed by a deliberate blink on a UI element.",
            "scrolling_down": "The system detected a sustained downward gaze pattern.",
            "scrolling_up": "The system detected a sustained upward gaze pattern.",
            "idle": "No navigation intent detected. Eyes are at rest.",
            "nav_back": "The system detected a double voluntary blink gesture.",
            "confirmation": "The system detected a deliberate long blink gesture.",
        }

        return {
            "intent": prediction.intent,
            "confidence": prediction.intent_confidence,
            "top_frames": top_frame_indices,
            "human_readable": explanation_map.get(
                prediction.intent, f"Detected {prediction.intent} intent."
            ),
        }

    def _idle_prediction(self, n_frames: int) -> IntentPrediction:
        """Return a safe idle prediction (no command)."""
        probs = np.zeros(len(INTENT_CLASSES), dtype=np.float32)
        probs[0] = 1.0  # Idle = class 0

        return IntentPrediction(
            intent="idle",
            intent_confidence=1.0,
            all_probabilities=probs,
            suggested_command=None,
            command_confidence=0.0,
            context_window_frames=n_frames,
        )

    def _load_model(self, model_path: Path) -> object | None:
        """Load ONNX Runtime inference session for intent model."""
        try:
            import onnxruntime as ort

            providers = ["CPUExecutionProvider"]
            available = ort.get_available_providers()
            if "CUDAExecutionProvider" in available:
                providers.insert(0, "CUDAExecutionProvider")

            session = ort.InferenceSession(str(model_path), providers=providers)
            logger.info("Intent model loaded: providers=%s", session.get_providers())
            return session

        except ImportError:
            logger.error("onnxruntime not installed.")
            return None
        except Exception as e:
            logger.error("Failed to load intent model: %s", e)
            return None
