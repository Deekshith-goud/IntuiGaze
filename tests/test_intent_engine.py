"""EyeNav Test Suite — Intent Engine Tests.
=========================================

Tests for the Tiny Temporal Transformer intent recognition engine.

Coverage:
    - Input validation
    - Output format verification
    - Idle prediction fallback
    - Explanation generation
    - Model loading fallback behavior
"""

from __future__ import annotations

import numpy as np
import pytest

from eyenav.intent import FEATURE_DIM, INTENT_CLASSES, IntentEngine, IntentPrediction


def make_feature_buffer(n_frames: int = 45) -> np.ndarray:
    """Create a synthetic feature buffer for testing."""
    return np.random.randn(n_frames, FEATURE_DIM).astype(np.float32)


class TestIntentEngineInputValidation:
    """Tests for input validation in IntentEngine."""

    def test_wrong_feature_dim_raises(self):
        """Wrong feature dimension must raise ValueError."""
        engine = IntentEngine.__new__(IntentEngine)
        engine._session = None  # Skip model loading

        wrong_buffer = np.zeros((45, 16))  # Wrong dim (should be 32)

        with pytest.raises(ValueError, match="feature_buffer must be shape"):
            engine.predict(wrong_buffer)

    def test_wrong_ndim_raises(self):
        """Non-2D array must raise ValueError."""
        engine = IntentEngine.__new__(IntentEngine)
        engine._session = None

        wrong_buffer = np.zeros((45, 32, 3))  # 3D array

        with pytest.raises(ValueError):
            engine.predict(wrong_buffer)


class TestIntentEngineWithoutModel:
    """Tests for IntentEngine behavior when model is not loaded."""

    def test_no_model_returns_idle(self):
        """Without model, prediction must default to idle (safe)."""
        engine = IntentEngine.__new__(IntentEngine)
        engine._session = None
        engine._input_name = None
        engine._output_names = None

        buffer = make_feature_buffer()
        result = engine.predict(buffer)

        assert result.intent == "idle"
        assert result.suggested_command is None
        assert result.blocked is False  # IntentPrediction doesn't have blocked field

    def test_idle_prediction_format(self):
        """Idle prediction must have correct format."""
        engine = IntentEngine.__new__(IntentEngine)
        engine._session = None

        make_feature_buffer()
        result = engine._idle_prediction(45)

        assert isinstance(result, IntentPrediction)
        assert result.intent == "idle"
        assert result.intent_confidence == 1.0
        assert result.suggested_command is None
        assert len(result.all_probabilities) == len(INTENT_CLASSES)
        assert abs(result.all_probabilities.sum() - 1.0) < 1e-6


class TestIntentPredictionFormat:
    """Tests for IntentPrediction output format."""

    def test_all_probabilities_sum_to_one(self):
        """Probability distribution must sum to 1."""
        engine = IntentEngine.__new__(IntentEngine)
        engine._session = None

        result = engine._idle_prediction(45)

        assert abs(result.all_probabilities.sum() - 1.0) < 1e-5

    def test_all_probabilities_non_negative(self):
        """All probabilities must be non-negative."""
        engine = IntentEngine.__new__(IntentEngine)
        engine._session = None

        result = engine._idle_prediction(45)

        assert np.all(result.all_probabilities >= 0)

    def test_intent_in_valid_classes(self):
        """Predicted intent must be one of the defined classes."""
        engine = IntentEngine.__new__(IntentEngine)
        engine._session = None

        result = engine._idle_prediction(45)

        assert result.intent in INTENT_CLASSES

    def test_confidence_in_range(self):
        """Confidence must be in [0, 1]."""
        engine = IntentEngine.__new__(IntentEngine)
        engine._session = None

        result = engine._idle_prediction(45)

        assert 0.0 <= result.intent_confidence <= 1.0


class TestExplanationGeneration:
    """Tests for intent explanation generation."""

    def test_explanation_without_attention_weights(self):
        """Explanation must work even without attention weights."""
        engine = IntentEngine.__new__(IntentEngine)
        engine._session = None

        prediction = IntentPrediction(
            intent="reading",
            intent_confidence=0.95,
            all_probabilities=np.array([0.05, 0.95] + [0.0] * (len(INTENT_CLASSES) - 2)),
            suggested_command=None,
            command_confidence=0.0,
            context_window_frames=45,
            attention_weights=None
        )

        explanation = engine.get_explanation(prediction)

        assert "intent" in explanation
        assert "confidence" in explanation
        assert "human_readable" in explanation
        assert explanation["intent"] == "reading"

    def test_explanation_with_attention_weights(self):
        """Explanation with attention weights includes top frames."""
        engine = IntentEngine.__new__(IntentEngine)
        engine._session = None

        attention = np.random.rand(45).astype(np.float32)

        prediction = IntentPrediction(
            intent="selecting",
            intent_confidence=0.95,
            all_probabilities=np.zeros(len(INTENT_CLASSES)),
            suggested_command="select",
            command_confidence=0.95,
            context_window_frames=45,
            attention_weights=attention
        )

        explanation = engine.get_explanation(prediction)

        assert "top_frames" in explanation
        assert len(explanation["top_frames"]) == 5  # Top 5 frames


class TestIntentConstants:
    """Tests for intent constants integrity."""

    def test_all_intent_classes_unique(self):
        """Intent class names must be unique."""
        assert len(INTENT_CLASSES) == len(set(INTENT_CLASSES))

    def test_feature_dim_positive(self):
        """Feature dimension must be positive."""
        assert FEATURE_DIM > 0

    def test_idle_is_first_class(self):
        """Idle must be class index 0 (safe default)."""
        assert INTENT_CLASSES[0] == "idle"
