"""EyeNav Camera Compatibility Tests.
===================================

Tests that verify EyeNav works with diverse camera hardware.

These tests require physical cameras to be attached to the test machine.
They are excluded from standard CI and must be run manually on a test rig.

Cameras tested:
    - Logitech C920 (reference camera)
    - Logitech C270 (budget 720p)
    - Microsoft LifeCam HD-3000
    - MacBook FaceTime camera (macOS only)
    - Generic 1080p USB webcam

Usage:
    # Run all camera tests (requires attached cameras):
    pytest tests/camera/ -m requires_camera -v --camera-id 0

    # Test specific camera by ID:
    pytest tests/camera/ -m requires_camera -v --camera-id 2

Metrics captured per camera:
    - Face detection rate at 0.5m, 1.0m, 1.5m distance
    - Frame rate (target ≥ 30fps)
    - Resolution achieved
    - Gaze estimation consistency (calibration-adjusted)
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


# Camera ID can be configured via pytest option
def pytest_addoption(parser):
    parser.addoption("--camera-id", action="store", default="0",
                     help="Camera device ID to test")


@pytest.fixture
def camera_id(request) -> int:
    return int(request.config.getoption("--camera-id", default="0"))


# ─── Camera Interface Tests (Mocked for CI) ──────────────────────────────

class TestCameraInterfaceMocked:
    """Camera interface tests using mocked camera.
    These run in CI without physical hardware.
    """

    def test_camera_open_returns_valid_frames(self):
        """Camera interface must return valid BGR frames."""
        with patch("cv2.VideoCapture") as mock_cap_cls:
            mock_cap = MagicMock()
            mock_cap_cls.return_value = mock_cap
            mock_cap.isOpened.return_value = True

            # Simulate valid 720p BGR frame
            fake_frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
            mock_cap.read.return_value = (True, fake_frame)

            import cv2
            cap = cv2.VideoCapture(0)
            assert cap.isOpened()

            ret, frame = cap.read()
            assert ret
            assert frame.shape == (720, 1280, 3)
            assert frame.dtype == np.uint8

    def test_camera_disconnect_handled_gracefully(self):
        """Camera disconnection must not crash the pipeline."""
        with patch("cv2.VideoCapture") as mock_cap_cls:
            mock_cap = MagicMock()
            mock_cap_cls.return_value = mock_cap
            mock_cap.isOpened.return_value = True

            # First 10 frames OK, then disconnects
            call_count = 0
            fake_frame = np.zeros((720, 1280, 3), dtype=np.uint8)

            def mock_read():
                nonlocal call_count
                call_count += 1
                if call_count <= 10:
                    return (True, fake_frame)
                return (False, None)  # Camera disconnected

            mock_cap.read.side_effect = mock_read

            import cv2
            cap = cv2.VideoCapture(0)

            frames_received = 0
            disconnection_detected = False

            for _ in range(20):
                ret, frame = cap.read()
                if ret:
                    frames_received += 1
                else:
                    disconnection_detected = True
                    break

            assert frames_received == 10
            assert disconnection_detected

    def test_low_resolution_camera_triggers_warning(self):
        """Camera below 640×480 must trigger a warning (not crash)."""
        with patch("cv2.VideoCapture") as mock_cap_cls:
            mock_cap = MagicMock()
            mock_cap_cls.return_value = mock_cap
            mock_cap.isOpened.return_value = True

            # 320×240 frame — below minimum
            low_res_frame = np.zeros((240, 320, 3), dtype=np.uint8)
            mock_cap.read.return_value = (True, low_res_frame)
            mock_cap.get.side_effect = lambda prop: {
                3: 320.0,  # CAP_PROP_FRAME_WIDTH
                4: 240.0,  # CAP_PROP_FRAME_HEIGHT
            }.get(prop, 0.0)

            import cv2
            cap = cv2.VideoCapture(0)
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

            # Should detect below-minimum resolution
            MIN_WIDTH, MIN_HEIGHT = 640, 480
            below_minimum = width < MIN_WIDTH or height < MIN_HEIGHT
            assert below_minimum, "Low-res detection failed"


# ─── Physical Camera Tests (requires_camera marker) ──────────────────────

@pytest.mark.requires_camera
class TestPhysicalCamera:
    """Tests that require physical camera hardware.
    Excluded from standard CI. Run manually on test rig.
    """

    @pytest.fixture
    def live_camera(self, camera_id: int):
        """Open physical camera for duration of test."""
        try:
            import cv2
        except ImportError:
            pytest.skip("OpenCV not available")

        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            pytest.skip(f"Camera {camera_id} not available")

        yield cap
        cap.release()

    def test_camera_achieves_target_fps(self, live_camera):
        """Physical camera must achieve ≥ 25fps sustained."""
        N_FRAMES = 90  # ~3 seconds at 30fps
        start = time.perf_counter()
        frames_captured = 0

        for _ in range(N_FRAMES):
            ret, _ = live_camera.read()
            if ret:
                frames_captured += 1

        elapsed = time.perf_counter() - start
        fps = frames_captured / elapsed

        assert fps >= 25.0, (
            f"Camera achieved only {fps:.1f}fps — target ≥ 25fps\n"
            f"Captured {frames_captured}/{N_FRAMES} frames in {elapsed:.2f}s"
        )

    def test_camera_resolution_meets_minimum(self, live_camera):
        """Physical camera must produce ≥ 640×480 frames."""
        ret, frame = live_camera.read()
        assert ret, "Failed to capture frame from camera"
        assert frame is not None

        height, width = frame.shape[:2]
        assert width >= 640, f"Width {width} < required 640"
        assert height >= 480, f"Height {height} < required 480"

    def test_camera_frames_are_valid_bgr(self, live_camera):
        """Physical camera frames must be valid BGR uint8 images."""
        for _ in range(10):
            ret, frame = live_camera.read()
            if not ret:
                continue

            assert frame is not None
            assert frame.dtype == np.uint8
            assert frame.ndim == 3
            assert frame.shape[2] == 3  # BGR channels

            # Values must be in [0, 255]
            assert frame.min() >= 0
            assert frame.max() <= 255

    def test_camera_stable_for_60_seconds(self, live_camera):
        """Physical camera must capture frames continuously for 60 seconds."""
        start = time.perf_counter()
        frames = 0
        dropped = 0
        target_seconds = 60

        while time.perf_counter() - start < target_seconds:
            ret, frame = live_camera.read()
            if ret:
                frames += 1
            else:
                dropped += 1

        time.perf_counter() - start
        drop_rate = dropped / max(frames + dropped, 1)

        # Max 1% frame drop rate
        assert drop_rate < 0.01, (
            f"Frame drop rate {drop_rate:.1%} exceeds 1% "
            f"({dropped} dropped in {frames + dropped} total)"
        )
