"""One Euro Filter for gaze cursor tracking.

Reference:
    Casiez, G., Roussel, N., & Vogel, D. (2012). 1€ Filter: A Simple Speed-based
    Low-pass Filter for Noisy Input in Interactive Systems. CHI 2012.

    https://inria.hal.science/hal-00670496/document

The key insight: most filters trade off lag against jitter. At low speeds
(fixation), we want heavy smoothing. At high speeds (saccade), we want low lag.
One Euro Filter adjusts the cutoff frequency dynamically based on signal speed,
achieving both goals simultaneously.

This is specifically preferred over Kalman or plain EMA for gaze cursor control
because it requires no process model and has only two interpretable parameters.
"""

from __future__ import annotations

import math


class _LowPassFilter:
    """Simple first-order low-pass filter with configurable alpha."""

    def __init__(self, cutoff: float) -> None:
        self._alpha = 1.0  # Start uninitialized — first call returns raw value
        self._value: float | None = None

    def filter(self, x: float, alpha: float) -> float:
        if self._value is None:
            self._value = x
            return x
        result = alpha * x + (1.0 - alpha) * self._value
        self._value = result
        return result

    @property
    def last(self) -> float:
        return self._value if self._value is not None else 0.0


class OneEuroFilter:
    """One Euro Filter for a single scalar signal.

    Parameters:
        min_cutoff: Minimum cutoff frequency in Hz. Lower = more smoothing
                    at rest. For gaze, 0.5–2.0 Hz is typical.
        beta:       Speed coefficient. Higher = less lag during fast movements.
                    For gaze cursor, 0.005–0.05 is typical.
        d_cutoff:   Derivative low-pass cutoff. Keep at 1.0 Hz.

    Example::

        f = OneEuroFilter(min_cutoff=1.2, beta=0.008)
        smoothed_x = f(raw_x, timestamp)
    """

    def __init__(
        self,
        min_cutoff: float = 1.2,
        beta: float = 0.008,
        d_cutoff: float = 1.0,
    ) -> None:
        self._min_cutoff = min_cutoff
        self._beta = beta
        self._d_cutoff = d_cutoff
        self._x_filter = _LowPassFilter(min_cutoff)
        self._dx_filter = _LowPassFilter(d_cutoff)
        self._last_time: float | None = None

    def __call__(self, x: float, timestamp: float) -> float:
        """Filter a scalar value.

        Args:
            x: Raw signal sample.
            timestamp: Current time in seconds (monotonic clock).

        Returns:
            Filtered value.
        """
        if self._last_time is None:
            self._last_time = timestamp
            return self._x_filter.filter(x, 1.0)

        dt = max(timestamp - self._last_time, 1e-6)
        self._last_time = timestamp

        # Estimate signal velocity using derivative low-pass filter
        raw_dx = (x - self._x_filter.last) / dt
        d_alpha = self._compute_alpha(self._d_cutoff, dt)
        edx = self._dx_filter.filter(raw_dx, d_alpha)

        # Compute adaptive cutoff: increases with speed to reduce lag during saccades
        cutoff = self._min_cutoff + self._beta * abs(edx)
        alpha = self._compute_alpha(cutoff, dt)

        return self._x_filter.filter(x, alpha)

    @staticmethod
    def _compute_alpha(cutoff: float, dt: float) -> float:
        """Compute IIR alpha for a given cutoff frequency and sample interval."""
        tau = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def reset(self) -> None:
        """Reset filter state (call when losing/reacquiring face)."""
        self._x_filter = _LowPassFilter(self._min_cutoff)
        self._dx_filter = _LowPassFilter(self._d_cutoff)
        self._last_time = None
