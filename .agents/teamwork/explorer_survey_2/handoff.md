# Handoff Report: Survey of Test Suite, Linters, Static Checks, and Safety/Cursor Invariants

**Explorer**: Explorer 2 (Test & Linter Explorer)  
**Date**: 2026-10-29  
**Working Directory**: `c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_survey_2`  
**Mission**: Survey repository test suites, linters, static checks, test commands, and safety/cursor invariants.

---

## 1. Observation

Direct code and configuration inspection revealed the following:

### 1.1 Test Configuration & Runners
- **Pytest Configuration** (`pyproject.toml:107-125`):
  ```toml
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  pythonpath = ["backend"]
  python_files = ["test_*.py", "*_test.py"]
  python_classes = ["Test*"]
  python_functions = ["test_*"]
  addopts = [
      "--strict-markers",
      "--tb=short",
      "-ra",
  ]
  markers = [
      "safety_critical: Mark test as safety-critical (must pass 100%)",
      "slow: Tests that take > 1 second",
      "requires_camera: Tests that require a physical camera",
      "requires_gpu: Tests that require GPU",
      "integration: Integration tests",
      "benchmark: Performance benchmark tests",
  ]
  ```
- **Conftest & Shared Fixtures** (`conftest.py:14-75`):
  - Registers options: `--camera-id` (default: `"0"`), `--benchmark-output` (default: `"benchmarks/results/"`).
  - Registers additional marker: `accessibility: WCAG 2.2 compliance tests (requires Playwright)`.
  - Shared fixtures:
    - `default_config` (session-scoped, returns `eyenav.config.Config()`) at `conftest.py:64-68`.
    - `camera_id` (function-scoped, returns integer from `--camera-id`) at `conftest.py:71-74`.

### 1.2 Inventory of Test Files and Suites
The repository contains 8 active test files under `tests/` and 1 performance test file under `benchmarks/`:
1. `tests/test_config.py` (139 lines):
   - 15 unit tests covering `Config`, `CameraConfig`, `SafetyConfig`, YAML deserialization, error handling, validation, and serialization round-trips.
2. `tests/test_safety_filter.py` (301 lines):
   - 17 safety-critical unit tests covering `ConfidenceThresholdGate` (T-SAFE-001 to 005), `CooldownRateLimiter` (T-SAFE-010 to 012), `EmergencyStop` (T-SAFE-020 to 023), `SafetyFilterResilience` (T-SAFE-030 to 032), and `DwellConfirmation` (T-SAFE-040 to 041).
3. `tests/test_intent_engine.py` (185 lines):
   - 13 unit tests covering `IntentEngineInputValidation`, `IntentEngineWithoutModel`, `IntentPredictionFormat`, `ExplanationGeneration`, and `IntentConstants`.
4. `tests/test_audit_dataset_script.py` (73 lines):
   - 3 integration smoke tests calling `scripts/audit_dataset.py` via `subprocess.run([sys.executable, str(SCRIPT), ...])` for CSV and JSONL manifests.
5. `tests/integration/test_pipeline_integration.py` (182 lines, marked `@pytest.mark.integration`):
   - 8 integration tests covering data flow from `IntentPrediction` through `SafetyFilter` (reading suppression, cooldowns, emergency stop trigger and clear, non-raising guarantee).
6. `tests/stress/test_sustained_operation.py` (168 lines, marked `@pytest.mark.slow`):
   - 5 stress tests covering 10,000 evaluations without error, memory stability check via `tracemalloc`, 1,000 emergency stop/clear recovery cycles, 1M temporal buffer shifts, and 4-thread concurrent evaluation safety.
7. `tests/camera/test_camera_compatibility.py` (234 lines):
   - 3 mocked interface tests in `TestCameraInterfaceMocked` (using `unittest.mock.patch("cv2.VideoCapture")`).
   - 4 hardware tests in `TestPhysicalCamera` (marked `@pytest.mark.requires_camera`, guarded by checking if physical camera opens; skipped if absent).
8. `tests/accessibility/test_wcag_compliance.py` (193 lines, marked `@pytest.mark.accessibility`):
   - 8 Playwright test methods in `TestDashboardAccessibility`, explicitly marked `@pytest.mark.skip(reason="Frontend dashboard is not running in CI pipeline yet")` at line 73.
9. `benchmarks/test_performance.py` (154 lines):
   - 4 benchmark tests for safety filter latency (<1ms mean, <5ms p99), intent engine predict latency (<50ms with mock), and temporal buffer shift (<100μs).

### 1.3 Existing Linters, Formatters, and Static Checkers
- **Ruff** (`pyproject.toml:41-76`):
  - Configuration: `target-version = "py311"`, `line-length = 100`, `src = ["backend", "tests"]`.
  - Rule sets enabled: `E, W, F, I, B, C4, UP, N, S, ANN, D`.
  - Ignored rules: `D100-D105, D107, D205, D415`, `ANN101, ANN001, ANN003, ANN201, ANN202, ANN204`, `E501, B017, N806, F821, F841, F401, E701, E722, E402, C408, S311, B007, B905, UP042, S110, W291, W293`.
  - Per-file ignores: `tests/*` and `benchmarks/*` ignore `S101` (assert) and `ANN201`.
  - Standard commands:
    - `ruff check backend/ tests/` (in `.github/workflows/ci.yml:20`)
    - `ruff format --check backend/ tests/` (in `.github/workflows/ci.yml:21`)
    - `ruff check backend/ tests/ scripts/` (in `SETUP_AND_ADOPTION.md:55` and `optional/ci/intuigaze-quality-gates.yml:40`)
- **MyPy** (`pyproject.toml:81-102`):
  - Configuration: `python_version = "3.14"`, `strict = true`, `warn_return_any = true`, `warn_unused_configs = true`, `ignore_missing_imports = true`, `exclude = ["tests/", "benchmarks/"]`, `explicit_package_bases = true`.
  - Standard command:
    - `mypy backend/eyenav/ --ignore-missing-imports` (in `.github/workflows/ci.yml:22`)
- **Bandit** (`pyproject.toml:150-152`):
  - Skips `B101` (assert statements).
  - Standard command:
    - `bandit -r backend/eyenav/ -c pyproject.toml` (in `.github/workflows/ci.yml:50`)
- **Pip-Audit**:
  - Standard command:
    - `pip-audit -r requirements.txt --ignore-vuln CVE-2024-23342 --ignore-vuln PYSEC-2026-3552` (in `.github/workflows/ci.yml:51`)
- **Code Coverage**:
  - `[tool.coverage.run]` targets `source = ["backend/eyenav"]`.
  - In CI: `pytest tests/ --cov=backend/eyenav --cov-report=xml --cov-fail-under=10 -v --tb=short` (`.github/workflows/ci.yml:35`).

### 1.4 Mouse Control and Desktop Safety Analysis
- **Zero Desktop Control in Automated Tests**:
  - A comprehensive search for `pyautogui`, `mouse`, and `cursor` across `tests/` returned **zero** occurrences.
  - Automated tests run entirely with synthetic feature vectors (`np.ndarray`), synthetic `IntentPrediction` objects, and mocked OpenCV frames.
  - No automated test moves the real mouse cursor or issues real mouse clicks.
- **Actuation Implementation in Source**:
  - Live cursor control is implemented in `backend/eyenav/cursor/controller.py` (`GazeCursorController`) and wrapped in `backend/eyenav/desktop.py` (`DesktopController`).
  - `GazeCursorController` directly imports `pyautogui` and executes `pyautogui.moveTo(final_x, final_y)` (`controller.py:211`), `pyautogui.click()` (`controller.py:257`), and `pyautogui.scroll()` (`controller.py:283`).
  - Built-in safety mechanisms in `controller.py`:
    - `pyautogui.FAILSAFE = True` (`controller.py:45`).
    - Physical mouse override guard: checks distance from last commanded coordinates; if movement exceeds 15px, eye control pauses for 2.0s (`controller.py:143-155`).
    - Fixation gravity deadzone: 45px deadzone prevents jitter (`controller.py:193-196`).
  - **Key Structural Deficiency**: `GazeCursorController` does **not** currently implement a mockable cursor adapter or a `dry_run=True` parameter. Real mouse control is avoided during tests solely because no test exercises `GazeCursorController` directly.
- **Ad-hoc Root Script (`exp.py`)**:
  - `exp.py:3, 23, 30` directly calls unshielded `pyautogui.moveTo(screen_x, screen_y)` and `pyautogui.click()`.
  - It is listed in `trash/cleanup_manifest.csv:3` as Category B ("Ad-hoc 33-line toy prototype with unshielded pyautogui calls; unreferenced") for quarantine to `trash/pending_review/exp.py`. Moving it eliminates root-level rogue actuation risks.

### 1.5 Test Status & Cache Records
- `.pytest_cache/v/cache/lastfailed` contains `{}` (zero failed tests recorded).
- `.pytest_cache/v/cache/nodeids` contains 86 test node IDs corresponding to tests across all 8 test files in `tests/`.
- Notice on environment: Attempted process execution (`python --version`) within the Windows environment resulted in a sandbox error (`CreateProcessSecurityEnvironment: The system cannot find the path specified`). In compliance with `AGENTS.md` ("Never claim tests passed unless you ran them... If no tests were run, say so plainly"), no live pytest run was executed in this agent turn. Test validity is derived from static inspection and existing pytest cache records.

---

## 2. Logic Chain

1. **Test Runner Identification**:
   - `pyproject.toml` defines `[tool.pytest.ini_options]` with `testpaths = ["tests"]` and `pythonpath = ["backend"]`.
   - `conftest.py` adds CLI options and markers.
   - Therefore, `pytest` is the standard and sole test runner configured for this repository.

2. **Linter & Static Analysis Identification**:
   - `.github/workflows/ci.yml` defines the CI gate using `ruff check`, `ruff format --check`, and `mypy backend/eyenav/ --ignore-missing-imports`.
   - `pyproject.toml` defines rule sets and ignores specifically for `ruff`, `mypy`, and `bandit`.
   - Therefore, `ruff` (lint/format) and `mypy` (types) represent the repository's standard quality toolchain.

3. **Desktop Safety & Actuation Invariant**:
   - `AGENTS.md` and `.agents/rules/40-cursor-safety-and-privacy.md` require: *"Do not run code that controls the actual mouse or clicks on the desktop during automated tests. Use mock/stub cursor adapters and dry-run mode."*
   - Direct inspection of all files under `tests/` confirms that no test imports `pyautogui` or calls cursor actuation methods.
   - All tests in `tests/test_safety_filter.py` and `tests/integration/test_pipeline_integration.py` test decision logic (`SafetyFilter.evaluate(...)`), resulting in a `VerifiedCommand` object without invoking OS cursor drivers.
   - However, `GazeCursorController` has direct coupling to `pyautogui`. If tests are ever created for `GazeCursorController`, mock adapters or dry-run flags will be mandatory to maintain the safety invariant.

4. **Quarantine Safety Impact**:
   - `exp.py` contains direct, unshielded `pyautogui` calls.
   - Removing `exp.py` to `trash/pending_review/exp.py` as specified in `trash/cleanup_manifest.csv` does not impact any test in `tests/` (which never imports or references `exp.py`), while permanently removing an unshielded desktop control hazard from the root.

---

## 3. Caveats

1. **No Live Test Execution in This Turn**:
   - In accordance with the strictly read-only role and OS sandbox subprocess restrictions, tests were not executed live during this survey turn. Current passing status is documented based on the `.pytest_cache/v/cache/lastfailed` state (`{}`), test code assertions, and CI workflow specifications.
2. **Missing Controller Unit Tests**:
   - Neither `GazeCursorController` nor `DesktopController` has dedicated unit test coverage in `tests/`. Adding tests for these classes in the future will require mocking `pyautogui`.
3. **Frontend Dashboard Test Exclusion**:
   - Accessibility tests in `tests/accessibility/test_wcag_compliance.py` are explicitly marked `@pytest.mark.skip` and require a running Next.js instance on `:3000`. They are not currently active in standard CI runs.
4. **Physical Camera Hardware Exclusion**:
   - Tests in `tests/camera/test_camera_compatibility.py` marked `@pytest.mark.requires_camera` require physical hardware and will be skipped in environments without an attached webcam.
5. **MyPy Version Setting**:
   - `pyproject.toml` specifies `python_version = "3.14"` under `[tool.mypy]`, whereas `requires-python = ">=3.11"` and CI runs Python 3.11.

---

## 4. Conclusion

- **Test Suite Health**: The repository has a comprehensive, well-structured test suite under `tests/` using `pytest`. The suite covers configuration (`test_config.py`), multi-layer safety policies (`test_safety_filter.py`), intent recognition fallbacks (`test_intent_engine.py`), dataset audit utilities (`test_audit_dataset_script.py`), pipeline integration (`test_pipeline_integration.py`), and sustained stress/concurrency (`test_sustained_operation.py`).
- **Linter & Type Toolchain**: The official quality gate consists of `ruff check`, `ruff format --check`, and `mypy backend/eyenav/ --ignore-missing-imports`.
- **Desktop Safety Invariant**: The repository's automated tests strictly adhere to the safety contract: **zero automated tests control the physical mouse or click the desktop**. Mouse actuation logic is confined to `backend/eyenav/cursor/controller.py`, which is protected by failsafes and physical overrides. Quarantining `exp.py` to `trash/pending_review/` eliminates an unreferenced, unshielded prototype script without risking any test regression.

---

## 5. Verification Method

To independently verify these findings on a development machine with an active Python environment:

1. **Inspect Pytest Configuration & Test Files**:
   ```powershell
   # View pytest configuration
   Get-Content pyproject.toml | Select-String -Pattern "pytest" -Context 0,20
   # List test files
   Get-ChildItem -Path tests -Recurse -Filter *.py
   ```
2. **Inspect Pytest Cache Status**:
   ```powershell
   Get-Content .pytest_cache\v\cache\lastfailed
   Get-Content .pytest_cache\v\cache\nodeids
   ```
3. **Verify Absence of Desktop Control in Tests**:
   ```powershell
   # Search for pyautogui calls inside tests directory (should return 0 matches)
   git grep "pyautogui" tests/
   ```
4. **Run Standard Test Suite (Dry-Run / No-Actuation)**:
   ```powershell
   # Run all non-hardware, non-slow unit and integration tests
   pytest tests/ -m "not slow and not requires_camera and not accessibility" -v --tb=short
   ```
5. **Run Linting and Static Checks**:
   ```powershell
   ruff check backend/ tests/ scripts/
   ruff format --check backend/ tests/
   mypy backend/eyenav/ --ignore-missing-imports
   ```
6. **Invalidation Conditions**:
   - If any test file inside `tests/` is found importing `pyautogui` without a mock.
   - If running `pytest tests/` initiates mouse cursor movement or desktop clicks.
   - If `.pytest_cache/v/cache/lastfailed` is populated with active failures after environment setup.
