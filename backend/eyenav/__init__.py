"""EyeNav — Intent-First Eye Navigation Platform.
=============================================

Main package init for the EyeNav library.

EyeNav is an intent-first Human Computer Interaction system that enables
complete hands-free device navigation using eye movements, blink patterns,
pupil tracking, and eyebrow gestures.

Architecture:
    Camera → FaceDetection → Landmarks → EyeAnalysis →
    TemporalContext → IntentRecognition → SafetyFilter →
    CommandRouter → OSIntegration

Usage:
    Basic usage::

        from eyenav import Config, SafetyFilter, IntentEngine

        config = Config()
        safety = SafetyFilter(config.safety)

Attributes:
    __version__ (str): Current version string.
    __author__ (str): EyeNav Research Team.
    __license__ (str): MIT.

References:
    - EyeNav Technical Whitepaper (papers/TECHNICAL_WHITEPAPER.md)
    - System Architecture (docs/architecture/SYSTEM_ARCHITECTURE.md)
"""

from __future__ import annotations

__version__ = "0.1.0-alpha"
__author__ = "EyeNav Research Team"
__license__ = "MIT"
__email__ = "research@eyenav.ai"

# Import stable, implemented modules only.
# Heavy pipeline modules (camera, OS integration) are imported on demand
# to avoid dependency errors when optional dependencies are missing.
from eyenav.config import Config
from eyenav.exceptions import (
    CalibrationError,
    CameraError,
    ConfigurationError,
    EyeNavError,
    ModelLoadError,
    SafetyError,
)
from eyenav.intent import INTENT_CLASSES, IntentEngine, IntentPrediction
from eyenav.safety import BlockReason, SafetyFilter, VerifiedCommand

__all__ = [
    # Configuration
    "Config",
    # Safety
    "SafetyFilter",
    "BlockReason",
    "VerifiedCommand",
    # Intent
    "IntentEngine",
    "IntentPrediction",
    "INTENT_CLASSES",
    # Exceptions
    "EyeNavError",
    "CameraError",
    "ModelLoadError",
    "SafetyError",
    "ConfigurationError",
    "CalibrationError",
]
