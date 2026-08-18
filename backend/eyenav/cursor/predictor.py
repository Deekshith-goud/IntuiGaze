"""Latency compensation predictor for gaze cursor control.

The camera-to-cursor pipeline has ~30–60ms end-to-end latency. Without
compensation, the cursor always feels like it is lagging behind the eye —
which is noticeable and breaks the "it follows my gaze" illusion.

This module estimates the current gaze velocity and extrapolates the
position forward by a configurable horizon (typically 40–50ms) to
counteract perceived lag.

Method: Weighted linear regression over a short rolling window.
    - Recent samples receive higher weight.
    - Uses least-squares line fit to estimate velocity.
    - Extrapolates ahead by horizon_ms.

Limitation: Linear prediction works well during smooth pursuits and
fixations. During rapid saccades (which are ballistic, not linear),
the prediction can overshoot. The SaccadeFixationDetector should be
used in conjunction to gate prediction aggressiveness.
"""

from __future__ import annotations

from collections import deque

import numpy as np


class LagCompensationPredictor:
    """Predicts gaze position ahead by a fixed time horizon.

    Args:
        prediction_horizon_ms: How far ahead to predict in milliseconds.
                               Typically 35–60ms for a 30fps webcam pipeline.
        velocity_window: Number of recent samples used for velocity estimate.
                         Larger = smoother velocity but more lag in estimation.
    """

    def __init__(
        self,
        prediction_horizon_ms: float = 45.0,
        velocity_window: int = 6,
    ) -> None:
        self._horizon_s = prediction_horizon_ms / 1000.0
        self._history: deque[tuple[float, float, float]] = deque(maxlen=velocity_window)

    def update_and_predict(
        self, x: float, y: float, timestamp: float
    ) -> tuple[float, float]:
        """Add a sample and return a position predicted ahead by horizon_ms.

        Args:
            x, y: Current screen coordinates (pixels).
            timestamp: Current monotonic time (seconds).

        Returns:
            (predicted_x, predicted_y) extrapolated ahead by horizon_ms.
            Returns (x, y) unchanged if insufficient history.
        """
        self._history.append((x, y, timestamp))

        if len(self._history) < 3:
            return x, y

        xs = np.array([s[0] for s in self._history], dtype=np.float64)
        ys = np.array([s[1] for s in self._history], dtype=np.float64)
        ts = np.array([s[2] for s in self._history], dtype=np.float64)
        ts_norm = ts - ts[0]

        if ts_norm[-1] < 1e-6:
            return x, y

        # Linearly increasing weights: [0.5, 0.625, 0.75, 0.875, 1.0, ...]
        n = len(ts_norm)
        weights = np.linspace(0.5, 1.0, n)

        # Weighted least-squares fit: position = a*t + b
        vx = float(np.polyfit(ts_norm, xs, 1, w=weights)[0])
        vy = float(np.polyfit(ts_norm, ys, 1, w=weights)[0])

        predicted_x = x + vx * self._horizon_s
        predicted_y = y + vy * self._horizon_s

        return predicted_x, predicted_y

    def reset(self) -> None:
        """Clear history (call on face loss)."""
        self._history.clear()
