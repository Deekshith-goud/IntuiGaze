# Explorer M2-3 Handoff Report: Test Hardening & Desktop Actuation Isolation

## Executive Summary
This report defines the test hardening strategy for Milestone 2 by analyzing the implementation of an active, autouse safety interceptor fixture (`guard_no_desktop_actuation`) in `conftest.py`. Comprehensive static analysis confirms that zero existing tests in `tests/` invoke `pyautogui` or perform desktop actuation; introducing this fixture introduces zero regressions while guaranteeing complete physical isolation against accidental mouse and keyboard actuation in all test environments.

---

## 1. Observation

### 1.1 Operating Contract & Mandatory Invariant Requirements
- **AGENTS.md**:
  - *"Do not run code that controls the actual mouse or clicks on the desktop during automated tests. Use mock/stub cursor adapters and dry-run mode."*
  - *"Mouse control must be opt-in, visibly active, interruptible, and disabled by default in tests."*
- **ORIGINAL_REQUEST.md (§R2)**:
  - *"Ensure desktop mouse control remains disabled during automated tests."*
- **PROJECT.md**:
  - *"Test Infrastructure (`tests/`): Purely synthetic/mocked tests with zero real desktop actuation."*
- **Explorer M1-3 Recommendation (`.agents/teamwork/explorer_m1_3/handoff.md:192-220`)**:
  - Recommended adding an autouse safety guard fixture `guard_no_desktop_actuation` to `conftest.py` to intercept 19 `pyautogui` actuation entry points.

### 1.2 Current `conftest.py` Implementation
- Located at repository root: `c:\Users\Voriganti\Downloads\INAV\conftest.py` (75 lines, 2,285 bytes).
- Contains:
  - Custom CLI options: `--camera-id`, `--benchmark-output` (lines 14-27).
  - Custom marker registrations: `safety_critical`, `slow`, `requires_camera`, `requires_gpu`, `integration`, `benchmark`, `accessibility` (lines 30-60).
  - Shared fixtures: `default_config` (session-scoped, lines 64-69) and `camera_id` (function-scoped, lines 71-74).
- **Current Deficit**: `conftest.py` does not currently define any desktop actuation safety guard or monkeypatching interceptor. Any unshielded test could invoke `pyautogui` and move the user's cursor or click on their active desktop.

### 1.3 Desktop Actuation Call Sites Across Codebase
A full repository audit for `pyautogui` identified call sites confined strictly to:
1. `backend/eyenav/cursor/controller.py`:
   - Line 36: `import pyautogui`
   - Line 82: `self.screen_width, self.screen_height = pyautogui.size()` (query)
   - Line 113: `self._last_commanded_x, self._last_commanded_y = pyautogui.position()` (query)
   - Line 143: `cx, cy = pyautogui.position()` (query)
   - Line 211: `pyautogui.moveTo(final_x, final_y)` (**actuation**)
   - Line 257: `pyautogui.click()` (**actuation**)
   - Line 260: `cx, cy = pyautogui.position()` (query)
   - Line 283: `pyautogui.scroll(amount)` (**actuation**)
2. `backend/eyenav/desktop.py`:
   - Line 83: `cx, cy = pyautogui.position()` (query in telemetry)
   - Internally instantiates `GazeCursorController(mapper=mapper)` (line 36)
3. `scripts/run_desktop.py` (interactive CLI runner):
   - Lines 73, 122: `pyautogui.size()` (query)
4. `scripts/target_practice.py` (interactive calibration practice):
   - Line 154: `cursor_x, cursor_y = pyautogui.position()` (query)
5. `trash/pending_review/exp.py` (quarantined prototype).

Zero other actuation libraries (`pynput`, `ctypes.windll.user32.SetCursorPos`, `win32api`, `SendInput`) are actively invoked for cursor manipulation.

### 1.4 Test Suite Audit (`tests/`)
All 8 test suites in `tests/` were audited for actuation calls:
- `tests/test_safety_filter.py`: Pure logic and threshold testing; zero OS calls.
- `tests/test_config.py`: Pure dataclass/Pydantic validation; zero OS calls.
- `tests/test_intent_engine.py`: Pure array/ONNX inference validation; zero OS calls.
- `tests/test_audit_dataset_script.py`: Subprocess execution on `scripts/audit_dataset.py`; zero OS calls.
- `tests/integration/test_pipeline_integration.py`: Pure pipeline logic chaining; zero OS calls.
- `tests/stress/test_sustained_operation.py`: Memory and loop stability; zero OS calls.
- `tests/accessibility/test_wcag_compliance.py`: Web dashboard tests (skipped if Playwright absent or server inactive); zero cursor calls.
- `tests/camera/test_camera_compatibility.py`: Mocked OpenCV capture; zero cursor calls.

**Result**: Exactly 0 occurrences of `pyautogui`, `controller`, `cursor`, or desktop actuation exist across all 8 existing test files.

---

## 2. Logic Chain

1. **Safety Risk**: While existing tests do not currently invoke `pyautogui`, any new unit or integration test written for `GazeCursorController`, `DesktopController`, or downstream pipeline stages could inadvertently execute `controller.update(landmarks)`, triggering real `pyautogui.moveTo()`, `pyautogui.click()`, or `pyautogui.scroll()`.
2. **Deficiency of Static Analysis Alone**: Static pattern checks (such as grep or `--check-mouse-isolation`) only check for literal calls like `pyautogui.moveTo` in test files. They cannot detect dynamic execution paths where a test invokes a class or function that internally calls `pyautogui`.
3. **Defense-in-Depth Solution**: An autouse pytest fixture (`guard_no_desktop_actuation`) using `pytest.MonkeyPatch` dynamically intercepts all actuation entry points at the module level before each test runs.
4. **Scope & Compatibility**:
   - `monkeypatch` in pytest is function-scoped. Setting `@pytest.fixture(autouse=True)` ensures the guard runs for every test and rolls back completely between tests.
   - Non-actuating queries (`pyautogui.size()`, `pyautogui.position()`) remain unblocked, allowing components to read screen resolution or initial coordinates without raising errors.
   - Tests that intentionally test cursor logic can explicitly override the mock (e.g., via `monkeypatch.setattr(pyautogui, "moveTo", mock_fn)`), enabling full unit testability without physical actuation.
5. **Zero Regression Proof**: Because zero existing tests call `pyautogui` actuation methods, activating this safety guard introduces zero test failures or regressions.

---

## 3. Caveats

1. **Subprocess Boundary**: `monkeypatch` operates in-memory within the active Python interpreter process. If a test spawns an external Python subprocess (e.g. `subprocess.run([sys.executable, "scripts/run_desktop.py"])`), the child process will not inherit the pytest monkeypatch. Currently, only `tests/test_audit_dataset_script.py` invokes subprocesses (specifically targeting `scripts/audit_dataset.py`, which contains zero GUI or actuation code). Any future tests executing subprocesses must explicitly pass dummy display/mock environment variables.
2. **Headless Environment Resilience**: In headless CI environments (e.g. Linux without an X server), importing `pyautogui` can raise `KeyError: 'DISPLAY'` or `ImportError`. The fixture must catch `(ImportError, Exception)` during `import pyautogui` so headless runners do not crash during test collection.
3. **Preservation Invariant**: `backend/eyenav/cursor/controller.py` contains uncommitted changes (`_FIXATION_DEADZONE_PX = 45.0`). This file MUST NOT be modified or formatted during Milestone 2. All safety isolation must be implemented exclusively in `conftest.py` and `tests/`.

---

## 4. Conclusion & Actionable Implementation Plan

Worker M2 should implement the following hardening package:

### 4.1 Update to `conftest.py`
Add the `guard_no_desktop_actuation` fixture to `conftest.py` directly under `# ─── Shared Fixtures ───`.

```python
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
```

### 4.2 Add Positive Verification Test Suite (`tests/test_safety_guard.py`)
To ensure continuous verification of this safety guard, Worker M2 should create `tests/test_safety_guard.py`:

```python
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
```

---

## 5. Verification Method

To independently verify the test hardening strategy:

### 5.1 Verification Commands
```powershell
# 1. Verify safety guard blocks actuation and passes all 6 guard checks
pytest tests/test_safety_guard.py -v

# 2. Verify all existing repository tests pass with zero regressions
pytest tests/ -v

# 3. Verify static code quality on modified / new files
ruff check conftest.py tests/test_safety_guard.py
ruff format --check conftest.py tests/test_safety_guard.py
mypy conftest.py

# 4. Verify safety invariants remain 100% intact
git status --porcelain
# Expected output: M backend/eyenav/cursor/controller.py and M docs/business/ETHICS.md (unchanged since start)
```

### 5.2 Invalidation Conditions
- Any test in `tests/` fails with an unexpected `RuntimeError` originating from `guard_no_desktop_actuation` (would indicate an unshielded actuation call in existing tests).
- Any test calling `pyautogui.moveTo`, `click`, `press`, or `scroll` succeeds without raising `RuntimeError` or using an explicit mock (would indicate a leak in the safety guard).
- Modifications are made to `backend/eyenav/cursor/controller.py` or `docs/business/ETHICS.md` (violating R2 safety invariants).
