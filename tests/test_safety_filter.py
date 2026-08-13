"""EyeNav Test Suite — Safety Filter Tests.
=========================================

Tests for the multi-layer safety filter system.

These tests are SAFETY CRITICAL and must pass 100% before any production deployment.
A failure in any safety test constitutes a production blocker.

Test Coverage:
    - Layer 1: Confidence threshold gate
    - Layer 2: Cooldown / rate limiter
    - Layer 3: Context validation (when implemented)
    - Layer 4: Dwell confirmation
    - Layer 5: Anti-pattern detection (when implemented)
    - Layer 6: Emergency stop
    - Edge cases and failure modes
    - Fatigue adaptation
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import numpy as np

from eyenav.config import CooldownConfig, SafetyConfig, SafetyThresholds
from eyenav.intent import INTENT_CLASSES, IntentPrediction
from eyenav.safety import BlockReason, SafetyFilter, VerifiedCommand


def make_config(**overrides) -> SafetyConfig:
    """Create a SafetyConfig with optional parameter overrides for testing."""
    threshold_defaults = {
        "low_risk": 0.85, "medium_risk": 0.92, "high_risk": 0.97, "critical_risk": 0.99
    }
    threshold_defaults.update(overrides.pop("thresholds", {}))

    cooldown_defaults = {"scroll": 300, "select": 800, "back": 1200, "delete": 2000}
    cooldown_defaults.update(overrides.pop("cooldowns", {}))

    return SafetyConfig(
        thresholds=SafetyThresholds(**threshold_defaults),
        cooldowns=CooldownConfig(**cooldown_defaults),
        emergency_stop_duration_ms=overrides.pop("emergency_stop_duration_ms", 3000),
        inter_command_minimum_ms=overrides.pop("inter_command_minimum_ms", 200),
        fatigue_monitoring_enabled=overrides.pop("fatigue_monitoring_enabled", True),
        reading_detection_suppression=overrides.pop("reading_detection_suppression", True),
        anti_pattern_detection=overrides.pop("anti_pattern_detection", True),
        **overrides
    )


def make_prediction(
    intent: str = "selecting",
    confidence: float = 0.95,
    command: str = "select"
) -> IntentPrediction:
    """Create a mock IntentPrediction for testing."""
    probs = np.zeros(len(INTENT_CLASSES), dtype=np.float32)
    idx = INTENT_CLASSES.index(intent) if intent in INTENT_CLASSES else 0
    probs[idx] = confidence

    return IntentPrediction(
        intent=intent,
        intent_confidence=confidence,
        all_probabilities=probs,
        suggested_command=command,
        command_confidence=confidence,
        context_window_frames=45
    )


class TestConfidenceThresholdGate:
    """Tests for Safety Layer 1: Confidence Threshold Gate."""

    def test_high_confidence_passes(self):
        """T-SAFE-001: Command with confidence above threshold must pass Layer 1."""
        safety = SafetyFilter(make_config())
        prediction = make_prediction(confidence=0.95)

        result = safety.evaluate(prediction)

        # Should not be blocked by confidence gate (may be blocked by other layers in future)
        assert result.block_reason != BlockReason.CONFIDENCE_THRESHOLD

    def test_low_confidence_blocked(self):
        """T-SAFE-002: Command below threshold must be blocked."""
        safety = SafetyFilter(make_config())
        prediction = make_prediction(confidence=0.80)  # Below 0.92 medium_risk threshold

        result = safety.evaluate(prediction)

        assert result.blocked is True
        assert result.block_reason == BlockReason.CONFIDENCE_THRESHOLD

    def test_exactly_at_threshold_passes(self):
        """T-SAFE-003: Command exactly at threshold must pass."""
        safety = SafetyFilter(make_config())
        prediction = make_prediction(confidence=0.92)  # Exactly at medium_risk threshold

        result = safety.evaluate(prediction)

        assert result.block_reason != BlockReason.CONFIDENCE_THRESHOLD

    def test_high_risk_command_requires_higher_threshold(self):
        """T-SAFE-004: Delete command (high risk) requires 0.97 confidence."""
        safety = SafetyFilter(make_config())
        # 0.94 passes medium_risk (0.92) but not high_risk (0.97)
        prediction = make_prediction(intent="selecting", confidence=0.94, command="delete")

        result = safety.evaluate(prediction)

        assert result.blocked is True
        assert result.block_reason == BlockReason.CONFIDENCE_THRESHOLD

    def test_custom_threshold_respected(self):
        """T-SAFE-005: Custom threshold configuration is respected."""
        config = make_config(thresholds={"medium_risk": 0.98})
        safety = SafetyFilter(config)
        prediction = make_prediction(confidence=0.95)  # Below custom 0.98

        result = safety.evaluate(prediction)

        assert result.blocked is True
        assert result.block_reason == BlockReason.CONFIDENCE_THRESHOLD


class TestCooldownRateLimiter:
    """Tests for Safety Layer 2: Cooldown / Rate Limiter."""

    def test_second_command_within_cooldown_blocked(self):
        """T-SAFE-010: Same command within cooldown period must be blocked."""
        safety = SafetyFilter(make_config())
        prediction = make_prediction(confidence=0.99, command="scroll_up")

        # Execute first command
        safety.evaluate(prediction)

        # Immediately try again
        result = safety.evaluate(prediction)

        assert result.blocked is True
        assert result.block_reason == BlockReason.COOLDOWN_ACTIVE

    def test_command_after_cooldown_passes(self):
        """T-SAFE-011: Command after cooldown period expires must pass."""
        config = make_config(cooldowns={"scroll": 100}, inter_command_minimum_ms=50)  # Short cooldown for testing
        safety = SafetyFilter(config)
        prediction = make_prediction(confidence=0.99, command="scroll_up")

        # Execute first command
        safety.evaluate(prediction)

        # Wait for cooldown + buffer
        time.sleep(0.15)  # 150ms > 100ms cooldown

        result = safety.evaluate(prediction)

        assert result.block_reason != BlockReason.COOLDOWN_ACTIVE

    def test_different_commands_no_cross_cooldown(self):
        """T-SAFE-012: Cooldown for one command does not block a different command."""
        safety = SafetyFilter(make_config())

        # Execute scroll
        safety.evaluate(make_prediction(confidence=0.99, command="scroll_up"))

        # Wait inter-command minimum but not scroll cooldown
        time.sleep(0.25)  # 250ms > 200ms inter-command minimum

        # Try a different command
        result = safety.evaluate(make_prediction(confidence=0.99, command="back", intent="nav_back"))

        assert result.block_reason != BlockReason.COOLDOWN_ACTIVE


class TestEmergencyStop:
    """Tests for Safety Layer 6: Emergency Stop."""

    def test_emergency_stop_blocks_all_commands(self):
        """T-SAFE-020: Emergency stop must block all commands."""
        safety = SafetyFilter(make_config())
        safety.trigger_emergency_stop()

        prediction = make_prediction(confidence=0.999)
        result = safety.evaluate(prediction)

        assert result.blocked is True
        assert result.block_reason == BlockReason.EMERGENCY_STOP

    def test_emergency_stop_clears(self):
        """T-SAFE-021: Clearing emergency stop re-enables commands."""
        safety = SafetyFilter(make_config())
        safety.trigger_emergency_stop()
        safety.clear_emergency_stop()

        assert safety.emergency_stop_active is False

    def test_emergency_stop_blocks_high_confidence(self):
        """T-SAFE-022: Emergency stop blocks even 99.9% confidence commands."""
        safety = SafetyFilter(make_config())
        safety.trigger_emergency_stop()

        result = safety.evaluate(make_prediction(confidence=0.999))

        assert result.blocked is True
        assert result.block_reason == BlockReason.EMERGENCY_STOP
        assert result.layers_passed == 0  # Emergency stop is checked first

    def test_emergency_stop_property(self):
        """T-SAFE-023: emergency_stop_active property reflects state."""
        safety = SafetyFilter(make_config())

        assert safety.emergency_stop_active is False
        safety.trigger_emergency_stop()
        assert safety.emergency_stop_active is True
        safety.clear_emergency_stop()
        assert safety.emergency_stop_active is False


class TestSafetyFilterResilience:
    """Tests for safety filter resilience and fail-safe behavior."""

    def test_none_command_does_not_crash(self):
        """T-SAFE-030: Prediction with no suggested command must not crash."""
        safety = SafetyFilter(make_config())
        prediction = make_prediction(intent="reading", confidence=0.95, command=None)
        prediction.suggested_command = None

        result = safety.evaluate(prediction)

        # Should not raise, should return a blocked result
        assert isinstance(result, VerifiedCommand)

    def test_exception_in_evaluation_fails_safe(self):
        """T-SAFE-031: Exception in safety filter must result in blocked command."""
        safety = SafetyFilter(make_config())

        # Create a prediction that will cause an error internally
        prediction = MagicMock()
        prediction.suggested_command = "select"
        prediction.intent_confidence = "NOT_A_FLOAT"  # Will cause type error

        result = safety.evaluate(prediction)

        assert result.blocked is True
        assert result.block_reason == BlockReason.SAFETY_FILTER_ERROR

    def test_verified_command_has_execution_id(self):
        """T-SAFE-032: Every verified command must have a unique execution ID."""
        safety = SafetyFilter(make_config())

        prediction1 = make_prediction(confidence=0.99)
        prediction2 = make_prediction(confidence=0.99)

        result1 = safety.evaluate(prediction1)
        time.sleep(0.25)  # Wait for inter-command minimum
        result2 = safety.evaluate(prediction2)

        assert result1.execution_id != result2.execution_id


class TestDwellConfirmation:
    """Tests for Safety Layer 4: Dwell Confirmation."""

    def test_high_risk_command_requires_dwell(self):
        """T-SAFE-040: High-risk command (delete) must not execute on first evaluation."""
        safety = SafetyFilter(make_config())
        prediction = make_prediction(confidence=0.999, command="delete")

        result = safety.evaluate(prediction)

        assert result.blocked is True
        assert result.block_reason == BlockReason.DWELL_INCOMPLETE

    def test_dwell_completion_allows_command(self):
        """T-SAFE-041: Command approved after dwell time elapses."""
        # Use extremely short dwell for testing
        config = make_config()
        safety = SafetyFilter(config)

        prediction = make_prediction(confidence=0.999, command="delete")

        # First call — starts dwell timer
        result1 = safety.evaluate(prediction)
        assert result1.block_reason == BlockReason.DWELL_INCOMPLETE

        # Manually set dwell start to past
        safety._dwell_start["delete"] = time.time() - 5.0  # 5 seconds ago

        # Second call — dwell complete
        result2 = safety.evaluate(prediction)
        # Should no longer be blocked by dwell
        assert result2.block_reason != BlockReason.DWELL_INCOMPLETE
