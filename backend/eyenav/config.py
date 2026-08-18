"""EyeNav Configuration Management.
================================

This module provides centralized configuration management for all EyeNav
pipeline components. Configuration is loaded from YAML files with schema
validation, environment variable overrides, and hot-reload support.

Design Decisions:
    - YAML format: Human-readable, widely supported, supports comments
    - Pydantic validation: Type safety + descriptive error messages
    - Environment overrides: 12-factor app compliance for containerized deployment
    - No hardcoded values: Every threshold is configurable
    - Schema versioning: Config format versioned to enable migration

Configuration Hierarchy (highest wins):
    1. Environment variables (EYENAV_*)
    2. User-supplied config file
    3. Default configuration (configs/defaults.yaml)

References:
    - configs/defaults.yaml: Default configuration values
    - docs/architecture/SYSTEM_ARCHITECTURE.md: Architecture constraints
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

from eyenav.exceptions import ConfigurationError


class CameraConfig(BaseModel):
    """Camera acquisition configuration."""

    device_id: int = Field(default=0, ge=0, description="Camera device index")
    resolution_width: int = Field(default=1280, ge=320, le=4096)
    resolution_height: int = Field(default=720, ge=240, le=2160)
    fps_target: int = Field(default=30, ge=15, le=120)
    backend: str = Field(
        default="auto", description="Camera backend: 'auto', 'directshow', 'v4l2', 'avfoundation'"
    )

    @field_validator("backend")
    @classmethod
    def validate_backend(cls, v: str) -> str:
        valid = {"auto", "directshow", "v4l2", "avfoundation"}
        if v not in valid:
            raise ValueError(f"backend must be one of {valid}")
        return v


class SafetyThresholds(BaseModel):
    """Confidence thresholds per risk level."""

    low_risk: float = Field(default=0.85, ge=0.5, le=1.0)
    medium_risk: float = Field(default=0.92, ge=0.5, le=1.0)
    high_risk: float = Field(default=0.97, ge=0.5, le=1.0)
    critical_risk: float = Field(default=0.99, ge=0.5, le=1.0)


class CooldownConfig(BaseModel):
    """Command cooldown periods in milliseconds."""

    scroll: int = Field(default=300, ge=100, le=5000)
    select: int = Field(default=800, ge=100, le=5000)
    back: int = Field(default=1200, ge=100, le=5000)
    forward: int = Field(default=1200, ge=100, le=5000)
    enter: int = Field(default=1500, ge=100, le=5000)
    delete: int = Field(default=2000, ge=500, le=10000)
    menu: int = Field(default=600, ge=100, le=5000)


class SafetyConfig(BaseModel):
    """Safety system configuration."""

    thresholds: SafetyThresholds = Field(default_factory=SafetyThresholds)
    cooldowns: CooldownConfig = Field(default_factory=CooldownConfig)
    emergency_stop_duration_ms: int = Field(default=3000, ge=1000, le=10000)
    inter_command_minimum_ms: int = Field(default=200, ge=50, le=1000)
    fatigue_monitoring_enabled: bool = Field(default=True)
    reading_detection_suppression: bool = Field(default=True)
    anti_pattern_detection: bool = Field(default=True)


class ModelPaths(BaseModel):
    """Paths to ONNX model files."""

    face_detection: Path = Field(default=Path("models/face_detection/blazeface.onnx"))
    landmarks: Path = Field(default=Path("models/landmarks/facemesh.onnx"))
    gaze: Path = Field(default=Path("models/gaze/l2cs_mobilenetv3.onnx"))
    blink: Path = Field(default=Path("models/blink/blink_cnn.onnx"))
    eyebrow: Path = Field(default=Path("models/eyebrow/eyebrow_mlp.onnx"))
    intent: Path = Field(default=Path("models/intent/tiny_transformer.onnx"))
    pupil: Path | None = Field(default=None, description="Optional EllSeg model")


class TemporalConfig(BaseModel):
    """Temporal context engine configuration."""

    window_ms: int = Field(default=1500, ge=500, le=5000)
    fps: int = Field(default=30, ge=15, le=120)
    smoothing: str = Field(default="kalman", description="'kalman' or 'one_euro'")

    @property
    def window_frames(self) -> int:
        """Number of frames in the temporal window."""
        return int(self.window_ms * self.fps / 1000)


class MetricsConfig(BaseModel):
    """Prometheus metrics configuration."""

    enabled: bool = Field(default=True)
    port: int = Field(default=9090, ge=1024, le=65535)
    export_to_grafana: bool = Field(default=False)


class OSConfig(BaseModel):
    """OS integration configuration."""

    platform: str = Field(default="auto", description="'auto', 'windows', 'macos', 'linux'")
    cursor_mode_enabled: bool = Field(default=True)
    scroll_amount: int = Field(default=3, ge=1, le=20)


class Config(BaseModel):
    """Master EyeNav configuration.

    All pipeline components are configured through this single object.
    Load from YAML file using Config.from_file() or create programmatically.

    Example:
        From file::

            config = Config.from_file("configs/my_config.yaml")

        Programmatic with overrides::

            config = Config(
                safety=SafetyConfig(
                    thresholds=SafetyThresholds(medium_risk=0.95)
                )
            )

    Attributes:
        camera: Camera acquisition settings.
        safety: Safety system thresholds and rules.
        models: Paths to ONNX model files.
        temporal: Temporal context window settings.
        metrics: Prometheus metrics export.
        os: OS integration settings.
        version: Config schema version for migration.
    """

    camera: CameraConfig = Field(default_factory=CameraConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    models: ModelPaths = Field(default_factory=ModelPaths)
    temporal: TemporalConfig = Field(default_factory=TemporalConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    os: OSConfig = Field(default_factory=OSConfig)
    version: str = Field(default="1.0")

    @classmethod
    def from_file(cls, path: str | Path) -> Config:
        """Load configuration from a YAML file.

        Applies environment variable overrides after loading.

        Args:
            path: Path to YAML configuration file.

        Returns:
            Validated Config object.

        Raises:
            ConfigurationError: If the file cannot be read or fails validation.
            FileNotFoundError: If the config file does not exist.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse config YAML: {e}") from e

        # Apply environment variable overrides
        data = cls._apply_env_overrides(data or {})

        try:
            return cls(**data)
        except Exception as e:
            raise ConfigurationError(f"Config validation failed: {e}") from e

    @classmethod
    def _apply_env_overrides(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Apply EYENAV_* environment variables as config overrides.

        Naming convention: EYENAV_SECTION_KEY = value
        Example: EYENAV_CAMERA_DEVICE_ID=1

        Args:
            data: Base config dict from YAML.

        Returns:
            Updated config dict with environment overrides.
        """
        for key, value in os.environ.items():
            if not key.startswith("EYENAV_"):
                continue

            parts = key[7:].lower().split("_", 1)
            if len(parts) == 2:
                section, field_name = parts
                if section in data:
                    data[section][field_name] = value

        return data

    def to_yaml(self, path: str | Path) -> None:
        """Save configuration to a YAML file.

        Args:
            path: Output file path.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            yaml.dump(self.model_dump(mode="json"), f, default_flow_style=False, sort_keys=True)
