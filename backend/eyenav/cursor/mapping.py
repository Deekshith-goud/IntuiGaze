"""Polynomial gaze-to-screen coordinate mapper with online adaptation.

Translates raw gaze features (iris positions + head pose) into screen
pixel coordinates using a personalized polynomial regression model.

Why polynomial (degree-2) regression?
    The gaze-to-screen relationship is non-linear: the eye's angular range
    compresses near the edges of the visual field, and head-gaze coupling
    varies per person. A degree-2 polynomial with 6 input features captures
    these curvatures without overfitting.

Input feature vector (6 dims):
    [left_iris_x, left_iris_y, right_iris_x, right_iris_y,
     head_yaw_deg, head_pitch_deg]

    All values in their natural units (iris: normalized 0–1 by MediaPipe,
    head pose: degrees from the facial transformation matrix).

Output: (screen_x, screen_y) in pixels.

Calibration approach:
    1. 9-point initial calibration: user fixates 9 known targets.
       Fits the polynomial via ridge regression (avoids overfitting on
       9 points).
    2. Online adaptation: each confirmed fixation incrementally updates
       the model via a rank-1 matrix update (no full refitting needed).

Persistence:
    Calibration is saved to ~/.eyenav/gaze_calibration.json and
    automatically loaded on next launch.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

_N_RAW_FEATURES = 4
# Linear features: [1, lx, ly, rx, ry] = 5 features
_N_POLY_FEATURES = 1 + _N_RAW_FEATURES
_PROFILE_FILENAME = "gaze_calibration.json"
_RIDGE_LAMBDA = 1e-4  # Near-zero to allow large weights for tiny pupil variance


class GazeScreenMapper:
    """Maps raw gaze feature vectors to screen pixel coordinates.

    A new instance starts un-fitted. Either call `fit()` after a calibration
    session, or call `load()` to restore a previous session from disk.

    Example::

        mapper = GazeScreenMapper(1920, 1080)
        if not mapper.load():
            data = CalibrationSession(extractor, cap).run()
            mapper.fit(data.gaze_samples, data.screen_samples)
            mapper.save()

        screen_x, screen_y = mapper.map(features)

    Args:
        screen_width: Monitor width in pixels.
        screen_height: Monitor height in pixels.
        profile_dir: Directory to save/load calibration. Defaults to ~/.eyenav.
    """

    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        profile_dir: Path | None = None,
    ) -> None:
        self._sw = screen_width
        self._sh = screen_height
        self._profile_dir = profile_dir or (Path.home() / ".eyenav")
        self._profile_dir.mkdir(parents=True, exist_ok=True)

        # Regression coefficients: shape (_N_POLY_FEATURES,) each
        self._coeff_x: np.ndarray | None = None
        self._coeff_y: np.ndarray | None = None
        self._is_fitted = False

        # State for incremental online updates
        self._XtX: np.ndarray | None = None
        self._Xty_x: np.ndarray | None = None
        self._Xty_y: np.ndarray | None = None

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def fit(self, gaze_samples: np.ndarray, screen_samples: np.ndarray) -> None:
        """Fit mapper from calibration data.

        Args:
            gaze_samples: Shape (N, 6). One row per calibration point.
            screen_samples: Shape (N, 2). Corresponding screen pixel coords.

        Raises:
            ValueError: If fewer than 6 samples are provided.
        """
        if len(gaze_samples) < 6:
            raise ValueError(
                f"Need ≥ 6 calibration samples, got {len(gaze_samples)}."
            )
        X = self._poly_features(gaze_samples)   # (N, 13)
        y_x = screen_samples[:, 0]
        y_y = screen_samples[:, 1]

        ridge = _RIDGE_LAMBDA * np.eye(X.shape[1])
        XtX = X.T @ X + ridge
        self._coeff_x = np.linalg.solve(XtX, X.T @ y_x)
        self._coeff_y = np.linalg.solve(XtX, X.T @ y_y)

        # Cache for online updates
        self._XtX = XtX.copy()
        self._Xty_x = (X.T @ y_x).copy()
        self._Xty_y = (X.T @ y_y).copy()

        self._is_fitted = True

        # Report training residuals for diagnostics
        pred_x = X @ self._coeff_x
        pred_y = X @ self._coeff_y
        rmse_x = float(np.sqrt(np.mean((pred_x - y_x) ** 2)))
        rmse_y = float(np.sqrt(np.mean((pred_y - y_y) ** 2)))
        logger.info(
            "GazeScreenMapper fitted: N=%d  RMSE=(%.1fpx, %.1fpx)",
            len(gaze_samples), rmse_x, rmse_y,
        )

    def map(self, gaze_features: np.ndarray) -> tuple[float, float]:
        """Map a gaze feature vector to screen coordinates.

        Args:
            gaze_features: Shape (6,) — [lx, ly, rx, ry, head_yaw, head_pitch].

        Returns:
            (screen_x, screen_y) clamped to screen bounds.
        """
        if not self._is_fitted:
            logger.debug("Mapper not fitted — returning screen center.")
            return self._sw / 2.0, self._sh / 2.0

        x_feat = self._poly_features(gaze_features[np.newaxis])   # (1, 13)
        sx = float((x_feat @ self._coeff_x)[0])
        sy = float((x_feat @ self._coeff_y)[0])
        return (
            float(np.clip(sx, 0, self._sw - 1)),
            float(np.clip(sy, 0, self._sh - 1)),
        )

    def update_online(
        self,
        gaze_features: np.ndarray,
        confirmed_screen_xy: np.ndarray,
        weight: float = 0.4,
    ) -> None:
        """Incrementally refine the mapper from a new confirmed sample.

        Called automatically when the user performs a blink-click (giving us
        a ground-truth gaze ↔ screen coordinate pair).

        Args:
            gaze_features: Shape (6,) raw features at time of click.
            confirmed_screen_xy: Shape (2,) screen pixel position of click.
            weight: Influence of this sample vs calibration history (0–1).
        """
        if not self._is_fitted:
            return
        if self._XtX is None:
            logger.debug("Cannot update online: model was loaded from disk without training state.")
            return

        x_feat = self._poly_features(gaze_features[np.newaxis])[0]  # (5,)

        # Weighted rank-1 update (avoids full matrix solve)
        self._XtX += weight * np.outer(x_feat, x_feat)
        self._Xty_x += weight * x_feat * confirmed_screen_xy[0]
        self._Xty_y += weight * x_feat * confirmed_screen_xy[1]

        self._coeff_x = np.linalg.solve(self._XtX, self._Xty_x)
        self._coeff_y = np.linalg.solve(self._XtX, self._Xty_y)

        logger.debug(
            "Online adaptation applied (weight=%.2f, screen=(%.0f, %.0f)).",
            weight, confirmed_screen_xy[0], confirmed_screen_xy[1],
        )

    def save(self) -> None:
        """Persist calibration profile to disk."""
        if not self._is_fitted:
            logger.warning("Cannot save: mapper is not fitted.")
            return

        profile = {
            "version": 1,
            "screen_width": self._sw,
            "screen_height": self._sh,
            "coeff_x": self._coeff_x.tolist(),
            "coeff_y": self._coeff_y.tolist(),
        }
        path = self._profile_dir / _PROFILE_FILENAME
        path.write_text(json.dumps(profile, indent=2))
        logger.info("Calibration saved → %s", path)

    def load(self) -> bool:
        """Load calibration profile from disk.

        Returns:
            True if successfully loaded, False otherwise.
        """
        path = self._profile_dir / _PROFILE_FILENAME
        if not path.exists():
            logger.info("No saved calibration found at %s.", path)
            return False

        try:
            data = json.loads(path.read_text())
            if data.get("screen_width") != self._sw or data.get("screen_height") != self._sh:
                logger.warning(
                    "Saved calibration is for %dx%d, current screen is %dx%d. Ignoring.",
                    data.get("screen_width"), data.get("screen_height"), self._sw, self._sh,
                )
                return False

            self._coeff_x = np.array(data["coeff_x"], dtype=np.float64)
            self._coeff_y = np.array(data["coeff_y"], dtype=np.float64)
            self._is_fitted = True
            logger.info("Calibration loaded from %s", path)
            return True
        except Exception as e:
            logger.error("Failed to load calibration from %s: %s", path, e)
            return False

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _poly_features(X: np.ndarray) -> np.ndarray:
        """Compute linear features from pupil coordinates only.

        Args:
            X: Shape (N, 6) or (N, 4). We only use the first 4 (lx, ly, rx, ry).

        Returns:
            Shape (N, 5): [1, lx, ly, rx, ry].
        """
        n = X.shape[0]
        bias = np.ones((n, 1), dtype=np.float64)
        return np.hstack([bias, X[:, :4].astype(np.float64)])
