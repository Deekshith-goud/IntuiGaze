"""EyeNav test configuration and shared fixtures.

This conftest.py is at the repo root level and provides:
    - pytest marker registration (avoids PytestUnknownMarkWarning)
    - Shared fixtures available to all test files
    - CLI options for test configuration
"""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register custom CLI options."""
    parser.addoption(
        "--camera-id",
        action="store",
        default="0",
        help="Camera device ID for hardware camera tests (default: 0)",
    )
    parser.addoption(
        "--benchmark-output",
        action="store",
        default="benchmarks/results/",
        help="Directory to write benchmark result JSON files",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "safety_critical: Safety tests — MUST achieve 100% pass for any release"
    )
    config.addinivalue_line(
        "markers",
        "slow: Tests that take > 1 second (excluded from quick CI runs)"
    )
    config.addinivalue_line(
        "markers",
        "requires_camera: Tests that require a physical camera to be attached"
    )
    config.addinivalue_line(
        "markers",
        "requires_gpu: Tests that require a GPU to run"
    )
    config.addinivalue_line(
        "markers",
        "integration: Integration tests — test interaction between modules"
    )
    config.addinivalue_line(
        "markers",
        "benchmark: Performance benchmark tests"
    )
    config.addinivalue_line(
        "markers",
        "accessibility: WCAG 2.2 compliance tests (requires Playwright)"
    )


# ─── Shared Fixtures ───────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def default_config():
    """Return a default Config for use in tests."""
    from eyenav.config import Config
    return Config()


@pytest.fixture
def camera_id(request: pytest.FixtureRequest) -> int:
    """Return the camera ID to use in hardware tests."""
    return int(request.config.getoption("--camera-id", default="0"))
