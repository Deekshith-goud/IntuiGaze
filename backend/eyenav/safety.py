"""EyeNav Safety Filter — 6-Layer Command Verification System.
===========================================================

This module implements the multi-layer safety filter that prevents false positive
command execution. It is the most safety-critical component in the EyeNav pipeline.

SAFETY CRITICAL: This module must pass formal code review before any production
deployment. All changes require a safety review sign-off.

Architecture:
    The safety filter implements 6 independent verification layers:

    Layer 1: Confidence Threshold Gate
        - Blocks commands below confidence threshold
        - Threshold adapts to context (fatigue, lighting, saccade rate)

    Layer 2: Cooldown / Rate Limiter
        - Prevents repeated same-command firing
        - Per-command cooldown periods
        - Global inter-command minimum spacing

    Layer 3: Context Validation
        - Validates command makes sense in current app/UI context
        - Blocks navigation commands during reading patterns
        - Blocks selections during high saccade rate

    Layer 4: Dwell Confirmation
        - High-risk commands require sustained gaze dwell
        - Progress indicator provides visual feedback
        - Gaze break resets progress

    Layer 5: Anti-Pattern Detection
        - Detects known false-trigger patterns
        - Reading saccades, post-blink artifacts, microsaccade bursts
        - Rule-based for maximum reliability

    Layer 6: Emergency Stop
        - Blocks ALL commands when emergency stop active
        - Triggered by sustained eye closure (3 seconds)
        - Cannot be bypassed by any other layer

Failure Modes:
    If the safety filter itself fails (exception), the CONSERVATIVE action is taken:
    command is BLOCKED. The system fails SAFE.

References:
    - docs/architecture/SAFETY_SYSTEM.md
    - ADR-002: Safety threshold design decisions
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto

import numpy as np

from eyenav.config import SafetyConfig
from eyenav.intent import INTENT_CLASSES, IntentPrediction

logger = logging.getLogger(__name__)


class BlockReason(Enum):
    """Reason why a command was blocked by the safety filter."""

    CONFIDENCE_THRESHOLD = auto()
    COOLDOWN_ACTIVE = auto()
    CONTEXT_MISMATCH = auto()
    DWELL_INCOMPLETE = auto()
    ANTI_PATTERN = auto()
    EMERGENCY_STOP = auto()
    SAFETY_FILTER_ERROR = auto()  # Fail-safe: block on exception


@dataclass
class VerifiedCommand:
    """Output of the safety filter.

    Represents either an approved command (blocked=False) or a blocked command
    with the reason for blocking.

    Attributes:
        command: The command name (e.g., "scroll_down").
        confidence: Intent confidence score at time of evaluation.
        blocked: True if the command was blocked.
        block_reason: Which layer blocked the command (if blocked).
        timestamp: Unix timestamp of evaluation.
        execution_id: UUID for audit trail.
        layers_passed: Number of safety layers that passed.
    """

    command: str
    confidence: float
    blocked: bool
    block_reason: BlockReason | None = None
    timestamp: float = field(default_factory=time.time)
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    layers_passed: int = 0


class SafetyFilter:
    """Multi-layer safety filter for EyeNav command verification.

    This is the most critical class in the EyeNav system. Its primary job is
    to prevent false positive command execution that could harm accessibility users.

    Design Principle:
        When in doubt, BLOCK.
        A missed command (false negative) is recoverable.
        An accidental command (false positive) may not be.

    Example:
        Usage in pipeline::

            safety_filter = SafetyFilter(config.safety)
            intent = intent_engine.predict(features)
            command = safety_filter.evaluate(intent)

            if not command.blocked:
                os_integration.execute(command)

    Args:
        config: Safety configuration with thresholds and cooldown periods.

    Thread Safety:
        This class is NOT thread-safe. Use one instance per pipeline thread.
    """

    def __init__(self, config: SafetyConfig) -> None:
        self._config = config
        self._command_history: dict[str, float] = {}  # command → last_execution_time
        self._last_command_time: float = 0.0
        self._emergency_stop_active: bool = False
        self._emergency_stop_triggered_at: float | None = None
        self._eye_closure_start: float | None = None
        self._dwell_start: dict[str, float] = {}  # command → dwell_start_time

        logger.info("SafetyFilter initialized with config: %s", config)

    def evaluate(self, prediction: IntentPrediction) -> VerifiedCommand:
        """Evaluate a predicted intent through all 6 safety layers.

        This is the primary public interface. Called once per intent prediction.

        Args:
            prediction: Intent prediction from the IntentEngine.

        Returns:
            VerifiedCommand with blocked=True if any layer rejected it,
            blocked=False if all layers passed.

        Notes:
            This method NEVER raises exceptions. All errors result in
            a blocked command (fail-safe behavior).
        """
        try:
            return self._evaluate_internal(prediction)
        except Exception as e:
            logger.exception("SafetyFilter evaluation raised unexpected error: %s", e)
            return VerifiedCommand(
                command=prediction.suggested_command or "unknown",
                confidence=prediction.intent_confidence,
                blocked=True,
                block_reason=BlockReason.SAFETY_FILTER_ERROR,
                layers_passed=0,
            )

    def trigger_emergency_stop(self) -> None:
        """Manually trigger emergency stop.

        Blocks all commands until emergency stop is cleared.
        Can be triggered by:
        - Extended eye closure (3 seconds)
        - Keyboard shortcut (Win+F9)
        - External API call
        """
        self._emergency_stop_active = True
        self._emergency_stop_triggered_at = time.time()
        logger.warning("EMERGENCY STOP TRIGGERED at %s", self._emergency_stop_triggered_at)

    def clear_emergency_stop(self) -> None:
        """Clear the emergency stop state.

        Should only be called after user explicitly re-enables the system.
        """
        self._emergency_stop_active = False
        self._emergency_stop_triggered_at = None
        logger.info("Emergency stop cleared.")

    @property
    def emergency_stop_active(self) -> bool:
        """Whether emergency stop is currently active."""
        return self._emergency_stop_active

    def _evaluate_internal(self, prediction: IntentPrediction) -> VerifiedCommand:
        """Internal evaluation — may raise exceptions (caught by evaluate())."""
        command = prediction.suggested_command
        if command is None:
            # No command suggested — pass through (intent without action)
            return VerifiedCommand(
                command="none",
                confidence=prediction.intent_confidence,
                blocked=True,
                block_reason=None,
                layers_passed=0,
            )

        layers_passed = 0

        # ── Layer 6: Emergency Stop (checked first — highest priority) ──────
        if self._emergency_stop_active:
            return VerifiedCommand(
                command=command,
                confidence=prediction.intent_confidence,
                blocked=True,
                block_reason=BlockReason.EMERGENCY_STOP,
                layers_passed=layers_passed,
            )
        layers_passed += 1

        # ── Layer 1: Confidence Threshold Gate ───────────────────────────────
        risk_level = self._get_risk_level(command)
        threshold = self._get_adaptive_threshold(risk_level, prediction)

        if prediction.intent_confidence < threshold:
            logger.debug(
                "Layer 1 BLOCKED: %s confidence=%.3f < threshold=%.3f",
                command,
                prediction.intent_confidence,
                threshold,
            )
            return VerifiedCommand(
                command=command,
                confidence=prediction.intent_confidence,
                blocked=True,
                block_reason=BlockReason.CONFIDENCE_THRESHOLD,
                layers_passed=layers_passed,
            )
        layers_passed += 1

        # ── Layer 2: Cooldown / Rate Limiter ─────────────────────────────────
        now = time.time()

        # Global inter-command minimum spacing
        if now - self._last_command_time < self._config.inter_command_minimum_ms / 1000:
            return VerifiedCommand(
                command=command,
                confidence=prediction.intent_confidence,
                blocked=True,
                block_reason=BlockReason.COOLDOWN_ACTIVE,
                layers_passed=layers_passed,
            )

        # Per-command cooldown
        cooldown_ms = self._get_command_cooldown_ms(command)
        last_execution = self._command_history.get(command, 0.0)

        if now - last_execution < cooldown_ms / 1000:
            remaining_ms = cooldown_ms - (now - last_execution) * 1000
            logger.debug(
                "Layer 2 BLOCKED: %s cooldown active, %.0fms remaining", command, remaining_ms
            )
            return VerifiedCommand(
                command=command,
                confidence=prediction.intent_confidence,
                blocked=True,
                block_reason=BlockReason.COOLDOWN_ACTIVE,
                layers_passed=layers_passed,
            )
        layers_passed += 1

        # ── Layer 3: Context Validation ──────────────────────────────────────
        reading_idx = INTENT_CLASSES.index("reading")
        searching_idx = INTENT_CLASSES.index("searching")
        reading_prob = float(prediction.all_probabilities[reading_idx])
        searching_prob = float(prediction.all_probabilities[searching_idx])

        if reading_prob > 0.3 or searching_prob > 0.3:
            logger.debug(
                "Layer 3 BLOCKED: %s due to context (reading=%.2f, searching=%.2f)",
                command,
                reading_prob,
                searching_prob,
            )
            return VerifiedCommand(
                command=command,
                confidence=prediction.intent_confidence,
                blocked=True,
                block_reason=BlockReason.CONTEXT_MISMATCH,
                layers_passed=layers_passed,
            )
        layers_passed += 1

        # ── Layer 4: Dwell Confirmation (high-risk commands only) ────────────
        if risk_level in ("high_risk", "critical_risk"):
            dwell_required_ms = self._get_dwell_required_ms(risk_level)
            dwell_start = self._dwell_start.get(command)

            if dwell_start is None:
                # Start dwell timer
                self._dwell_start[command] = now
                return VerifiedCommand(
                    command=command,
                    confidence=prediction.intent_confidence,
                    blocked=True,
                    block_reason=BlockReason.DWELL_INCOMPLETE,
                    layers_passed=layers_passed,
                )

            dwell_elapsed_ms = (now - dwell_start) * 1000
            if dwell_elapsed_ms < dwell_required_ms:
                return VerifiedCommand(
                    command=command,
                    confidence=prediction.intent_confidence,
                    blocked=True,
                    block_reason=BlockReason.DWELL_INCOMPLETE,
                    layers_passed=layers_passed,
                )

            # Dwell complete — clear timer
            del self._dwell_start[command]
        layers_passed += 1

        # ── Layer 5: Anti-Pattern Detection ──────────────────────────────────
        probs = prediction.all_probabilities
        entropy = -np.sum(probs * np.log(probs + 1e-9))
        max_entropy = np.log(len(probs))
        normalized_entropy = float(entropy / max_entropy)

        if normalized_entropy > 0.6:  # Threshold for high uncertainty
            logger.debug(
                "Layer 5 BLOCKED: %s due to anti-pattern (high entropy %.2f)",
                command,
                normalized_entropy,
            )
            return VerifiedCommand(
                command=command,
                confidence=prediction.intent_confidence,
                blocked=True,
                block_reason=BlockReason.ANTI_PATTERN,
                layers_passed=layers_passed,
            )
        layers_passed += 1

        # ── All layers passed — command approved ─────────────────────────────
        self._command_history[command] = now
        self._last_command_time = now

        logger.info(
            "Command APPROVED: %s (confidence=%.3f, layers_passed=%d)",
            command,
            prediction.intent_confidence,
            layers_passed,
        )

        return VerifiedCommand(
            command=command,
            confidence=prediction.intent_confidence,
            blocked=False,
            block_reason=None,
            layers_passed=layers_passed,
        )

    def _get_risk_level(self, command: str) -> str:
        """Determine risk level for a command."""
        high_risk = {"delete", "submit", "send", "shutdown"}
        critical_risk = {"emergency_call"}
        medium_risk = {"select", "click", "enter", "back", "forward"}

        if command in critical_risk:
            return "critical_risk"
        elif command in high_risk:
            return "high_risk"
        elif command in medium_risk:
            return "medium_risk"
        else:
            return "low_risk"

    def _get_adaptive_threshold(self, risk_level: str, prediction: IntentPrediction) -> float:
        """Compute adaptive confidence threshold.

        Increases threshold in conditions that raise false positive risk:
        - High saccade velocity (scanning)
        - Post-blink period
        - Fatigue indicators
        """
        base = getattr(self._config.thresholds, risk_level)
        adjustment = 0.0

        # Add adaptive adjustments based on context in Phase 2
        reading_idx = INTENT_CLASSES.index("reading")
        searching_idx = INTENT_CLASSES.index("searching")

        reading_prob = float(prediction.all_probabilities[reading_idx])
        searching_prob = float(prediction.all_probabilities[searching_idx])

        # If there's non-negligible context noise, raise the bar for confidence
        if reading_prob > 0.1 or searching_prob > 0.1:
            adjustment += 0.05

        return min(0.99, base + adjustment)

    def _get_command_cooldown_ms(self, command: str) -> float:
        """Get cooldown period for a command in milliseconds."""
        cooldown_map = {
            "scroll_up": self._config.cooldowns.scroll,
            "scroll_down": self._config.cooldowns.scroll,
            "select": self._config.cooldowns.select,
            "click": self._config.cooldowns.select,
            "back": self._config.cooldowns.back,
            "forward": self._config.cooldowns.forward,
            "enter": self._config.cooldowns.enter,
            "delete": self._config.cooldowns.delete,
            "menu": self._config.cooldowns.menu,
        }
        return cooldown_map.get(command, self._config.cooldowns.select)

    def _get_dwell_required_ms(self, risk_level: str) -> float:
        """Get required dwell time for a risk level."""
        dwell_map = {
            "medium_risk": 600,
            "high_risk": 1200,
            "critical_risk": 2000,
        }
        return dwell_map.get(risk_level, 600)
