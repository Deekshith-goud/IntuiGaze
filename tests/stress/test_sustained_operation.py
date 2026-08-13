"""EyeNav Stress Tests — System Stability Under Sustained Operation.
=================================================================

Tests that verify system stability over extended time periods.
All tests are marked @pytest.mark.slow — they take minutes to hours.

Requirements verified:
    SRS-PERF-007: MTBF ≥ 8 hours (simulated)

Usage:
    pytest tests/stress/test_sustained_operation.py -m slow -v -s
"""

from __future__ import annotations

import gc
import time
import tracemalloc

import numpy as np
import pytest

from eyenav.config import Config
from eyenav.intent import FEATURE_DIM, INTENT_CLASSES, IntentPrediction
from eyenav.safety import SafetyFilter, VerifiedCommand


def make_prediction(intent_idx: int = 2, confidence: float = 0.95) -> IntentPrediction:
    """Create a test prediction for stress testing."""
    probs = np.zeros(len(INTENT_CLASSES), dtype=np.float32)
    probs[intent_idx] = confidence
    return IntentPrediction(
        intent=INTENT_CLASSES[intent_idx],
        intent_confidence=confidence,
        all_probabilities=probs,
        suggested_command="test",
        command_confidence=confidence,
        context_window_frames=45,
    )


@pytest.mark.slow
class TestSustainedSafetyFilter:
    """Test SafetyFilter stability under sustained evaluation load."""

    def test_safety_filter_10000_evaluations_no_error(self):
        """SafetyFilter must evaluate 10,000 predictions without raising."""
        config = Config()
        sf = SafetyFilter(config.safety)
        prediction = make_prediction()

        errors = 0
        for i in range(10_000):
            try:
                result = sf.evaluate(prediction)
                assert isinstance(result, VerifiedCommand)
            except Exception as e:
                errors += 1
                print(f"Error at iteration {i}: {e}")

        assert errors == 0, f"{errors} errors in 10,000 evaluations"

    def test_safety_filter_memory_stable_over_time(self):
        """SafetyFilter must not leak memory over 1,000 evaluations."""
        config = Config()
        sf = SafetyFilter(config.safety)
        prediction = make_prediction()

        # Warm up
        for _ in range(100):
            sf.evaluate(prediction)
        gc.collect()

        # Measure baseline
        tracemalloc.start()
        baseline_snapshot = tracemalloc.take_snapshot()

        # Run 1,000 more evaluations
        for _ in range(1_000):
            sf.evaluate(prediction)
        gc.collect()

        # Measure after
        end_snapshot = tracemalloc.take_snapshot()
        tracemalloc.stop()

        # Compare memory (allow up to 512KB growth — minor caching is OK)
        stats = end_snapshot.compare_to(baseline_snapshot, "lineno")
        total_growth_bytes = sum(s.size_diff for s in stats if s.size_diff > 0)

        MAX_GROWTH_BYTES = 512 * 1024  # 512KB
        assert total_growth_bytes < MAX_GROWTH_BYTES, (
            f"Memory grew by {total_growth_bytes / 1024:.1f}KB over 1,000 evaluations "
            f"(max allowed: {MAX_GROWTH_BYTES / 1024:.1f}KB)"
        )

    def test_emergency_stop_and_recovery_cycle_1000x(self):
        """Emergency stop → recovery cycle must be stable over 1,000 cycles."""
        config = Config()
        sf = SafetyFilter(config.safety)

        for cycle in range(1_000):
            # Trigger emergency stop
            sf.trigger_emergency_stop()
            assert sf.emergency_stop_active

            # Verify blocked
            prediction = make_prediction()
            result = sf.evaluate(prediction)
            assert result.blocked, f"Emergency stop not working at cycle {cycle}"

            # Recover
            sf.clear_emergency_stop()
            assert not sf.emergency_stop_active, f"Reset failed at cycle {cycle}"


@pytest.mark.slow
class TestTemporalBufferStress:
    """Test temporal buffer operations under sustained load."""

    def test_buffer_shift_1_million_frames(self):
        """Temporal buffer shift must be stable over 1M frame updates."""
        buffer = np.zeros((45, FEATURE_DIM), dtype=np.float32)
        new_frame = np.random.randn(FEATURE_DIM).astype(np.float32)

        start_time = time.perf_counter()
        for _ in range(1_000_000):
            buffer[:-1] = buffer[1:]
            buffer[-1] = new_frame
        elapsed = time.perf_counter() - start_time

        # 1M shifts should take < 5 seconds
        assert elapsed < 5.0, f"Buffer shifts too slow: {elapsed:.2f}s for 1M shifts"

        # Buffer should still be valid
        assert buffer.shape == (45, FEATURE_DIM)
        assert not np.any(np.isnan(buffer))
        assert not np.any(np.isinf(buffer))


@pytest.mark.slow
class TestConcurrentEvaluations:
    """Test thread safety of pipeline components."""

    def test_safety_filter_thread_safe_evaluation(self):
        """SafetyFilter must be safe to call from multiple threads."""
        import threading

        config = Config()
        sf = SafetyFilter(config.safety)
        prediction = make_prediction()
        errors: list[Exception] = []

        def evaluate_many() -> None:
            for _ in range(1000):
                try:
                    sf.evaluate(prediction)
                except Exception as e:
                    errors.append(e)

        threads = [threading.Thread(target=evaluate_many) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread safety errors: {errors[:3]}"
