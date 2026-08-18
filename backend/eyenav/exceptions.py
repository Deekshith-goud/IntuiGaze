"""EyeNav Exception Hierarchy.
============================

All EyeNav-specific exceptions. Using a dedicated exception hierarchy:
1. Makes error handling explicit and typed
2. Allows catch-by-category (catch EyeNavError for all EyeNav errors)
3. Provides meaningful error messages for debugging

Exception Hierarchy:
    EyeNavError (base)
    ├── ConfigurationError
    ├── CameraError
    │   ├── CameraNotFoundError
    │   ├── CameraPermissionError
    │   └── CameraDisconnectedError
    ├── ModelError
    │   ├── ModelLoadError
    │   ├── ModelInferenceError
    │   └── ModelValidationError
    ├── CalibrationError
    │   ├── CalibrationDataError
    │   └── CalibrationAccuracyError
    ├── SafetyError (should never escape — fail-safe behavior)
    └── OSIntegrationError
"""

from __future__ import annotations


class EyeNavError(Exception):
    """Base class for all EyeNav exceptions."""


class ConfigurationError(EyeNavError):
    """Raised when configuration is invalid or cannot be loaded."""


class CameraError(EyeNavError):
    """Base class for camera-related errors."""


class CameraNotFoundError(CameraError):
    """Raised when the requested camera device is not found."""


class CameraPermissionError(CameraError):
    """Raised when the system lacks permission to access the camera."""


class CameraDisconnectedError(CameraError):
    """Raised when the camera disconnects during operation."""


class ModelError(EyeNavError):
    """Base class for ML model errors."""


class ModelLoadError(ModelError):
    """Raised when an ONNX model cannot be loaded."""


class ModelInferenceError(ModelError):
    """Raised when model inference fails unexpectedly."""


class ModelValidationError(ModelError):
    """Raised when model output fails validation (ONNX vs PyTorch mismatch)."""


class CalibrationError(EyeNavError):
    """Base class for calibration errors."""


class CalibrationDataError(CalibrationError):
    """Raised when calibration data is corrupted or invalid."""


class CalibrationAccuracyError(CalibrationError):
    """Raised when calibration cannot achieve required accuracy."""

    def __init__(self, achieved_error: float, required_error: float) -> None:
        self.achieved_error = achieved_error
        self.required_error = required_error
        super().__init__(
            f"Calibration accuracy {achieved_error:.2f}° > required {required_error:.2f}°"
        )


class SafetyError(EyeNavError):
    """Raised when the safety system itself encounters an unexpected error.

    IMPORTANT: This exception should NEVER propagate to users.
    The safety filter's evaluate() method catches all exceptions and
    returns a blocked command as fail-safe behavior.

    If this exception is seen in logs, it indicates a safety system bug
    that must be investigated immediately.
    """


class OSIntegrationError(EyeNavError):
    """Raised when OS command execution fails."""
