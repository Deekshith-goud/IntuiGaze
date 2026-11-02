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


# ─── Desktop Actuation Safety Fixtures ─────────────────────────────────────

@pytest.fixture(autouse=True)
def guard_no_desktop_actuation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Safety guard: Intercept and fail any physical OS desktop actuation during tests.

    Complies with AGENTS.md:
        "Do not run code that controls the actual mouse or clicks on the desktop
        during automated tests. Use mock/stub cursor adapters and dry-run mode."
    """
    def forbidden_actuation(*args, **kwargs):
        raise RuntimeError(
            "CRITICAL SAFETY VIOLATION: Automated test attempted physical desktop mouse/keyboard actuation! "
            "Tests must use mock cursor adapters or dry-run mode per AGENTS.md."
        )

    try:
        import pyautogui

        actuation_methods = [
            # Mouse movement
            "moveTo", "moveRel", "move",
            # Mouse click & button events
            "click", "doubleClick", "tripleClick",
            "mouseDown", "mouseUp", "rightClick", "middleClick",
            # Mouse drag
            "dragTo", "dragRel", "drag",
            # Mouse scroll
            "scroll", "hscroll", "vscroll",
            # Keyboard events
            "write", "typewrite", "press", "keyDown", "keyUp", "hotkey",
        ]
        for fn_name in actuation_methods:
            if hasattr(pyautogui, fn_name):
                monkeypatch.setattr(pyautogui, fn_name, forbidden_actuation)
    except (ImportError, Exception):
        pass

