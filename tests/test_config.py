"""EyeNav Test Suite — Config Tests.
==================================

Tests for the configuration management system.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from eyenav.config import CameraConfig, Config, SafetyConfig, SafetyThresholds
from eyenav.exceptions import ConfigurationError


class TestConfigDefaults:
    """Test that default configuration is valid."""

    def test_default_config_creates(self):
        """Default Config must be creatable without arguments."""
        config = Config()
        assert config is not None

    def test_default_camera_fps(self):
        """Default camera FPS must be 30."""
        config = Config()
        assert config.camera.fps_target == 30

    def test_default_medium_risk_threshold(self):
        """Default medium risk threshold must be 0.92."""
        config = Config()
        assert config.safety.thresholds.medium_risk == 0.92

    def test_default_emergency_stop_ms(self):
        """Default emergency stop duration must be 3000ms."""
        config = Config()
        assert config.safety.emergency_stop_duration_ms == 3000

    def test_default_temporal_window(self):
        """Default temporal window must be 1500ms."""
        config = Config()
        assert config.temporal.window_ms == 1500

    def test_temporal_window_frames_computed(self):
        """window_frames property must compute correctly."""
        config = Config()
        # 1500ms * 30fps / 1000 = 45 frames
        assert config.temporal.window_frames == 45


class TestConfigFromFile:
    """Test loading config from YAML files."""

    def test_load_default_config(self):
        """Default config file must load without errors."""
        default_path = Path("configs/defaults.yaml")
        if default_path.exists():
            config = Config.from_file(default_path)
            assert config is not None

    def test_load_partial_config(self):
        """Partial YAML (only some fields) must load with defaults for missing."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
            yaml.dump({"camera": {"fps_target": 60}}, f)
            tmp_path = f.name

        try:
            config = Config.from_file(tmp_path)
            assert config.camera.fps_target == 60
            # Other values should be defaults
            assert config.safety.thresholds.medium_risk == 0.92
        finally:
            os.unlink(tmp_path)

    def test_file_not_found_raises(self):
        """Non-existent config file must raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            Config.from_file("does_not_exist.yaml")

    def test_invalid_yaml_raises_config_error(self):
        """Invalid YAML must raise ConfigurationError."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
            f.write("invalid: yaml: content: ][")
            tmp_path = f.name

        try:
            with pytest.raises(ConfigurationError):
                Config.from_file(tmp_path)
        finally:
            os.unlink(tmp_path)


class TestConfigValidation:
    """Test Pydantic validation in config."""

    def test_invalid_fps_raises(self):
        """Camera FPS below minimum (15) must raise."""
        with pytest.raises(Exception):
            Config(camera=CameraConfig(fps_target=5))

    def test_threshold_above_1_raises(self):
        """Confidence threshold > 1.0 must raise."""
        with pytest.raises(Exception):
            Config(safety=SafetyConfig(
                thresholds=SafetyThresholds(medium_risk=1.5)
            ))

    def test_threshold_below_0_raises(self):
        """Confidence threshold < 0 must raise."""
        with pytest.raises(Exception):
            Config(safety=SafetyConfig(
                thresholds=SafetyThresholds(medium_risk=-0.1)
            ))

    def test_invalid_camera_backend_raises(self):
        """Invalid camera backend string must raise."""
        with pytest.raises(Exception):
            Config(camera=CameraConfig(backend="invalid_backend"))


class TestConfigSerialization:
    """Test config round-trip serialization."""

    def test_to_yaml_roundtrip(self):
        """Config saved to YAML must load back identically."""
        original = Config()
        original.camera.fps_target = 60

        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            tmp_path = f.name

        try:
            original.to_yaml(tmp_path)
            loaded = Config.from_file(tmp_path)
            assert loaded.camera.fps_target == 60
            assert loaded.safety.thresholds.medium_risk == original.safety.thresholds.medium_risk
        finally:
            os.unlink(tmp_path)
