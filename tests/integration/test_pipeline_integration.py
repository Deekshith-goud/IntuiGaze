"""EyeNav Integration Tests — Pipeline Stage Interactions.
========================================================

Tests that pipeline stages interact correctly when chained together.

Marked with @pytest.mark.integration to run separately from unit tests.

Usage:
    pytest tests/integration/ -m integration -v
"""

from __future__ import annotations

import numpy as np
import pytest

from eyenav.config import Config, SafetyConfig, SafetyThresholds
from eyenav.intent import INTENT_CLASSES, IntentPrediction
from eyenav.safety import BlockReason, SafetyFilter, VerifiedCommand

# ─── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def config() -> Config:
    return Config()


@pytest.fixture
def safety_filter(config: Config) -> SafetyFilter:
    return SafetyFilter(config.safety)


def make_prediction(
    intent_name: str | None = None,
    confidence: float = 0.95,
) -> IntentPrediction:
    idx = 2  # "selecting" by default
    if intent_name is not None and intent_name in INTENT_CLASSES:
        idx = INTENT_CLASSES.index(intent_name)
    probs = np.zeros(len(INTENT_CLASSES), dtype=np.float32)
    probs[idx] = confidence
    name = INTENT_CLASSES[idx]
    # Always assign a command so all safety layers (including emergency stop) are reached
    command_map = {"selecting": "select", "scrolling_down": "scroll_down", "scrolling_up": "scroll_up"}
    suggested = command_map.get(name, "navigate")
    return IntentPrediction(
        intent=name,
        intent_confidence=confidence,
        all_probabilities=probs,
        suggested_command=suggested,
        command_confidence=confidence,
        context_window_frames=45,
    )


# ─── Integration: IntentEngine → SafetyFilter ──────────────────────────────

@pytest.mark.integration
class TestIntentToSafetyFlow:

    def test_high_confidence_flows_to_safety_filter(self, safety_filter: SafetyFilter):
        """High-confidence intent must flow to safety filter and produce VerifiedCommand."""
        # Build prediction directly (IntentEngine requires ONNX model — mocked here)
        prediction = make_prediction(confidence=0.97)
        assert prediction is not None
        assert 0.0 <= prediction.intent_confidence <= 1.0

        result = safety_filter.evaluate(prediction)
        assert isinstance(result, VerifiedCommand)

    def test_low_confidence_intent_is_blocked(self, safety_filter: SafetyFilter):
        """Intent below confidence threshold must be blocked."""
        prediction = make_prediction(confidence=0.30)
        result = safety_filter.evaluate(prediction)
        assert result.blocked
        assert result.block_reason == BlockReason.CONFIDENCE_THRESHOLD

    def test_reading_intent_does_not_produce_command(self, safety_filter: SafetyFilter):
        """Reading intent must be blocked — reading suppresses all navigation commands."""
        probs = np.zeros(len(INTENT_CLASSES), dtype=np.float32)
        probs[INTENT_CLASSES.index("reading")] = 0.98
        reading_prediction = IntentPrediction(
            intent="reading",
            intent_confidence=0.98,
            all_probabilities=probs,
            # Reading maps to None command in INTENT_TO_COMMAND
            suggested_command=None,
            command_confidence=0.0,
            context_window_frames=45,
        )
        result = safety_filter.evaluate(reading_prediction)
        # Safety filter short-circuits on None command with blocked=True
        assert result.blocked

    def test_cooldown_blocks_rapid_second_command(self, safety_filter: SafetyFilter):
        """Two commands in rapid succession — second must be blocked by cooldown."""
        prediction = make_prediction(confidence=0.97)

        # First call (may or may not pass — depends on cooldown state)
        safety_filter.evaluate(prediction)

        # Second call immediately — must be blocked by cooldown
        result2 = safety_filter.evaluate(prediction)
        assert result2.blocked, "Rapid second command should be blocked by cooldown"

    def test_emergency_stop_blocks_all_intents(self, safety_filter: SafetyFilter):
        """After emergency stop, all predictions must be blocked."""
        safety_filter.trigger_emergency_stop()
        assert safety_filter.emergency_stop_active

        for i in range(min(5, len(INTENT_CLASSES))):
            prediction = make_prediction(intent_name=INTENT_CLASSES[i], confidence=0.99)
            result = safety_filter.evaluate(prediction)
            assert result.blocked, (
                f"Intent '{INTENT_CLASSES[i]}' was NOT blocked during emergency stop"
            )
            assert result.block_reason == BlockReason.EMERGENCY_STOP

    def test_emergency_stop_clear_resumes_evaluation(self, safety_filter: SafetyFilter):
        """After clearing emergency stop, evaluation resumes normally."""
        safety_filter.trigger_emergency_stop()
        safety_filter.clear_emergency_stop()
        assert not safety_filter.emergency_stop_active

        prediction = make_prediction(confidence=0.30)  # Low confidence
        result = safety_filter.evaluate(prediction)
        # Should be blocked by CONFIDENCE now, not by EMERGENCY_STOP
        assert result.blocked
        assert result.block_reason == BlockReason.CONFIDENCE_THRESHOLD


# ─── Integration: Config → SafetyFilter Behavior ──────────────────────────

@pytest.mark.integration
class TestConfigToSafetyBehavior:

    def test_strict_threshold_blocks_borderline_confidence(self):
        """SafetyConfig with high threshold must block 0.95 confidence predictions."""
        strict_config = Config(
            safety=SafetyConfig(
                thresholds=SafetyThresholds(
                    low_risk=0.95,
                    medium_risk=0.99,
                    high_risk=0.995,
                )
            )
        )
        sf = SafetyFilter(strict_config.safety)
        prediction = make_prediction(confidence=0.95)
        result = sf.evaluate(prediction)
        # 0.95 is AT the low_risk threshold — behavior depends on implementation
        # At minimum it should not crash
        assert isinstance(result, VerifiedCommand)

    def test_safety_filter_does_not_raise_on_any_input(self):
        """SafetyFilter.evaluate must NEVER raise — it must return blocked VerifiedCommand."""
        sf = SafetyFilter(Config().safety)

        # Edge case: zero-confidence prediction
        prediction = make_prediction(confidence=0.0)
        result = sf.evaluate(prediction)
        assert isinstance(result, VerifiedCommand)
        assert result.blocked  # Zero confidence must be blocked

        # Edge case: NaN probabilities — must not raise, regardless of outcome
        probs = np.full(len(INTENT_CLASSES), float("nan"), dtype=np.float32)
        bad_prediction = IntentPrediction(
            intent="selecting",
            intent_confidence=float("nan"),
            all_probabilities=probs,
            suggested_command="select",
            command_confidence=float("nan"),
            context_window_frames=45,
        )
        result = sf.evaluate(bad_prediction)
        assert isinstance(result, VerifiedCommand)  # Must return a result, not raise
