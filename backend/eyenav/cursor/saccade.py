"""Saccade and fixation classification for gaze cursor control.

Saccades are rapid ballistic eye movements (100–700°/s).
Fixations are stable gaze periods (100–600ms) where the eye is relatively still.

The cursor behaves differently in each state:
- During a saccade: allow fast cursor movement toward predicted landing zone.
- During a fixation: converge cursor to a robust centroid (suppress jitter).
- In-between: hold last known state.

Detection approach: angular velocity thresholding.
    - velocity > SACCADE_THRESHOLD → saccade
    - velocity < FIXATION_THRESHOLD for > MIN_FIXATION_MS → fixation

Reference:
    Rayner, K. (1998). Eye movements in reading and information processing.
    Psychological Bulletin, 124(3), 372–422.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from enum import Enum


class GazeState(Enum):
    """Current gaze classification state."""
    FIXATION = "fixation"
    SACCADE = "saccade"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class GazeSample:
    x: float          # Screen pixels
    y: float
    timestamp: float  # Seconds


class SaccadeFixationDetector:
    """Classifies gaze samples as saccades or fixations.

    Args:
        saccade_vel_px: Velocity above which we declare a saccade (px/s).
                        200 px/s ≈ 6°/s at 60cm, 24" 1080p.
        fixation_vel_px: Velocity below which we consider the eye still (px/s).
        min_fixation_ms: Minimum duration to confirm a fixation (ms).
        window_size: Number of recent samples used for centroid estimation.
    """

    def __init__(
        self,
        saccade_vel_px: float = 200.0,
        fixation_vel_px: float = 40.0,
        min_fixation_ms: float = 80.0,
        window_size: int = 15,
    ) -> None:
        self._saccade_vel = saccade_vel_px
        self._fixation_vel = fixation_vel_px
        self._min_fixation_ms = min_fixation_ms
        self._window: deque[GazeSample] = deque(maxlen=window_size)
        self._state = GazeState.UNKNOWN
        self._fixation_start: float | None = None
        self._last: GazeSample | None = None

    def update(
        self, x: float, y: float, timestamp: float
    ) -> tuple[GazeState, tuple[float, float]]:
        """Update with a new screen-space gaze sample.

        Args:
            x, y: Screen coordinates (pixels) of current gaze.
            timestamp: Current monotonic time (seconds).

        Returns:
            Tuple of (GazeState, (centroid_x, centroid_y)).
            During saccades, the centroid is the raw current position.
            During fixations, the centroid is a robust outlier-rejected average.
        """
        sample = GazeSample(x, y, timestamp)
        self._window.append(sample)

        if self._last is None:
            self._last = sample
            return GazeState.UNKNOWN, (x, y)

        dt = max(timestamp - self._last.timestamp, 1e-6)
        dist = math.hypot(x - self._last.x, y - self._last.y)
        velocity_px_s = dist / dt
        self._last = sample

        if velocity_px_s > self._saccade_vel:
            self._state = GazeState.SACCADE
            self._fixation_start = None
            return GazeState.SACCADE, (x, y)

        if velocity_px_s < self._fixation_vel:
            if self._fixation_start is None:
                self._fixation_start = timestamp
            elapsed_ms = (timestamp - self._fixation_start) * 1000.0
            if elapsed_ms >= self._min_fixation_ms:
                self._state = GazeState.FIXATION
                return GazeState.FIXATION, self._robust_centroid()

        return self._state, (x, y)

    def _robust_centroid(self) -> tuple[float, float]:
        """Compute outlier-rejected mean of the current fixation window.

        Rejects samples further than 2σ from the mean on each axis.
        Falls back to plain mean if σ is near-zero (tight fixation).
        """
        if not self._window:
            return 0.0, 0.0

        xs = [s.x for s in self._window]
        ys = [s.y for s in self._window]

        def filtered_mean(vals: list[float]) -> float:
            mean = sum(vals) / len(vals)
            std = math.sqrt(sum((v - mean) ** 2 for v in vals) / len(vals))
            if std < 1e-6:
                return mean
            inliers = [v for v in vals if abs(v - mean) <= 2.0 * std]
            return sum(inliers) / len(inliers) if inliers else mean

        return filtered_mean(xs), filtered_mean(ys)

    def reset(self) -> None:
        """Reset state (call on face loss)."""
        self._state = GazeState.UNKNOWN
        self._fixation_start = None
        self._last = None
        self._window.clear()

    @property
    def state(self) -> GazeState:
        return self._state
