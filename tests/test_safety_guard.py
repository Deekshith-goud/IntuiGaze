"""Tests for automated test desktop actuation safety guard."""
from __future__ import annotations

import pytest


def test_guard_blocks_mouse_move() -> None:
    """Verify that pyautogui.moveTo raises RuntimeError under test guard."""
    try:
        import pyautogui
    except (ImportError, Exception):
        pytest.skip("pyautogui not available in this environment")

    with pytest.raises(RuntimeError, match="CRITICAL SAFETY VIOLATION"):
        pyautogui.moveTo(100, 100)


def test_guard_blocks_mouse_click() -> None:
    """Verify that pyautogui.click raises RuntimeError under test guard."""
    try:
        import pyautogui
    except (ImportError, Exception):
        pytest.skip("pyautogui not available in this environment")

    with pytest.raises(RuntimeError, match="CRITICAL SAFETY VIOLATION"):
        pyautogui.click()


def test_guard_blocks_mouse_scroll() -> None:
    """Verify that pyautogui.scroll raises RuntimeError under test guard."""
    try:
        import pyautogui
    except (ImportError, Exception):
        pytest.skip("pyautogui not available in this environment")

    with pytest.raises(RuntimeError, match="CRITICAL SAFETY VIOLATION"):
        pyautogui.scroll(10)


def test_guard_blocks_keyboard_input() -> None:
    """Verify that pyautogui.press raises RuntimeError under test guard."""
    try:
        import pyautogui
    except (ImportError, Exception):
        pytest.skip("pyautogui not available in this environment")

    with pytest.raises(RuntimeError, match="CRITICAL SAFETY VIOLATION"):
        pyautogui.press("enter")


def test_guard_allows_query_functions() -> None:
    """Verify that non-actuating queries (size, position) remain callable."""
    try:
        import pyautogui
    except (ImportError, Exception):
        pytest.skip("pyautogui not available in this environment")

    # These query calls must not raise RuntimeError
    try:
        pos = pyautogui.position()
        assert len(pos) == 2
        sz = pyautogui.size()
        assert len(sz) == 2
    except pyautogui.FailSafeException:
        pass


def test_guard_allows_explicit_test_mocking(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that individual tests can explicitly mock actuation methods."""
    try:
        import pyautogui
    except (ImportError, Exception):
        pytest.skip("pyautogui not available in this environment")

    recorded_positions = []

    def mock_move(x: int, y: int) -> None:
        recorded_positions.append((x, y))

    monkeypatch.setattr(pyautogui, "moveTo", mock_move)
    pyautogui.moveTo(42, 84)

    assert recorded_positions == [(42, 84)]
