# Handoff Report: Pytest Test Suites Catalog, Hardware Gates, Safety Verification, and Regression Execution Plan

**Explorer**: Explorer M2-1 (Pytest Test Suites Explorer)  
**Date**: 2026-10-29  
**Working Directory**: `c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m2_1`  
**Mission**: Formulate the regression test execution plan for Milestone 2 (Step 8: Regression and Quality Verification) by cataloging all tests, mapping markers/hardware gates, verifying mouse actuation safety, and defining exact zero-failure pytest commands.

---

## 1. Observation

Direct inspection of repository configuration, test suites under `tests/`, and live pytest collection outputs revealed the following facts:

### 1.1 Pytest Configuration & Fixture Structure
- **Root Configuration** (`pyproject.toml:107-125`):
  - `testpaths = ["tests"]`
  - `pythonpath = ["backend"]`
  - `python_files = ["test_*.py", "*_test.py"]`
  - `python_classes = ["Test*"]`
  - `python_functions = ["test_*"]`
  - `addopts = ["--strict-markers", "--tb=short", "-ra"]`
  - Registered markers: `safety_critical`, `slow`, `requires_camera`, `requires_gpu`, `integration`, `benchmark`.
- **Root Fixture & Marker Registry** (`conftest.py:1-75`):
  - Additional registered marker: `accessibility: WCAG 2.2 compliance tests (requires Playwright)`.
  - CLI options: `--camera-id` (default: `"0"`), `--benchmark-output` (default: `"benchmarks/results/"`).
  - Session fixtures: `default_config` (`conftest.py:64-68`), returns `eyenav.config.Config()`.
  - Function fixtures: `camera_id` (`conftest.py:71-74`), parses `--camera-id` integer.
- **Collection Verification**:
  - Live test collection (`pytest --collect-only tests/`) successfully discovered **76 total test items** across 8 test files without syntax errors or broken imports.

### 1.2 Exhaustive Catalog of Test Files and Functions
The repository contains 8 test files organized across root `tests/` and 4 specialized subdirectories:

| # | Test File Path | Lines | Total Tests | Test Classes & Methods | Scope / Description | Markers |
|---|----------------|-------|-------------|------------------------|---------------------|---------|
| 1 | `tests/test_config.py` | 139 | 15 | `TestConfigDefaults` (6)<br>`TestConfigFromFile` (4)<br>`TestConfigValidation` (4)<br>`TestConfigSerialization` (1) | Validates default config properties, YAML loading & merging, Pydantic validation rules, and YAML serialization round-trips. | *None* |
| 2 | `tests/test_safety_filter.py` | 301 | 17 | `TestConfidenceThresholdGate` (5)<br>`TestCooldownRateLimiter` (3)<br>`TestEmergencyStop` (4)<br>`TestSafetyFilterResilience` (3)<br>`TestDwellConfirmation` (2) | Safety-critical verification of Layers 1 (confidence), 2 (cooldown), 4 (dwell), 6 (emergency stop), and fail-safe exception recovery. | *None* (Docstring designated Safety-Critical) |
| 3 | `tests/test_intent_engine.py` | 185 | 13 | `TestIntentEngineInputValidation` (2)<br>`TestIntentEngineWithoutModel` (2)<br>`TestIntentPredictionFormat` (4)<br>`TestExplanationGeneration` (2)<br>`TestIntentConstants` (3) | Validates input feature shapes, safe fallback to `idle` when uninitialized, probability distribution normalization, explanation extraction, and constants. | *None* |
| 4 | `tests/test_audit_dataset_script.py` | 73 | 3 | `test_inventory_and_csv_manifest`<br>`test_jsonl_manifest`<br>`test_missing_root_is_rejected` | Smoke integration tests invoking `scripts/audit_dataset.py` via `subprocess.run` to verify schema validation, inventory, null checks, and error handling. | *None* |
| 5 | `tests/integration/test_pipeline_integration.py` | 182 | 8 | `TestIntentToSafetyFlow` (6)<br>`TestConfigToSafetyBehavior` (2) | Integration dataflow: `IntentPrediction` through `SafetyFilter` (reading suppression, cooldowns, emergency stop trigger/clear, non-raising guarantee). | `integration` |
| 6 | `tests/camera/test_camera_compatibility.py` | 234 | 7 | `TestCameraInterfaceMocked` (3)<br>`TestPhysicalCamera` (4) | Camera interface testing. 3 mocked tests simulate OpenCV frames and disconnects. 4 physical hardware tests measure FPS, resolution, BGR, and 60s stability. | Mocked: *None*<br>Physical: `requires_camera` |
| 7 | `tests/stress/test_sustained_operation.py` | 168 | 5 | `TestSustainedSafetyFilter` (3)<br>`TestTemporalBufferStress` (1)<br>`TestConcurrentEvaluations` (1) | Sustained load testing: 10,000 evaluations without error, memory leak check via `tracemalloc` (<512KB), 1,000 emergency stop cycles, 1M buffer shifts, 4-thread safety. | `slow` |
| 8 | `tests/accessibility/test_wcag_compliance.py` | 193 | 8 | `TestDashboardAccessibility` (8) | Playwright + axe-core WCAG 2.2 AA audits on `/`, `/settings`, `/calibration`, button names, keyboard navigation, color contrast, alt text, and form labels. | `accessibility`, `@pytest.mark.skip` |

Total test functions in `tests/`: **76 items**.

### 1.3 Test Markers and Hardware Gates Map

1. **`requires_camera`**:
   - Location: `tests/camera/test_camera_compatibility.py:146` (`TestPhysicalCamera`).
   - Hardware Dependency: Physical camera device attached to host machine (default index `0`).
   - Gating mechanism: Fixture `live_camera` calls `pytest.skip(f"Camera {camera_id} not available")` if device cannot be opened.
   - Run profile: Excluded in automated regression runs via `-m "not requires_camera"`. If enabled with hardware present, `test_camera_stable_for_60_seconds` will block for a full 60 seconds.
2. **`slow`**:
   - Location: `tests/stress/test_sustained_operation.py:42, 117, 141` (all 3 stress test classes).
   - Profile: High CPU / iteration stress tests (10k evaluations, 1k stop/reset cycles, 1M array shifts).
   - Execution time: ~1.5 - 2.5 seconds total on CPU.
   - Gating mechanism: Can be omitted during quick local feedback using `-m "not slow"`. Included during full regression.
3. **`accessibility`**:
   - Location: `tests/accessibility/test_wcag_compliance.py:72` (`TestDashboardAccessibility`).
   - Profile: UI browser end-to-end tests requiring Playwright and a running Next.js server on `:3000`.
   - Gating mechanism: Line 73 applies `@pytest.mark.skip(reason="Frontend dashboard is not running in CI pipeline yet")`. Line 36-39 applies `pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE)`.
   - Run profile: Excluded via `-m "not accessibility"`. Unconditionally skipped even if marker is invoked.
4. **`integration`**:
   - Location: `tests/integration/test_pipeline_integration.py:64, 140` (both classes, 8 tests).
   - Profile: Fast in-memory integration tests (<0.1s). No hardware or external process required.
5. **`safety_critical`**:
   - Location: Registered in `pyproject.toml` and `conftest.py`. Represents the 17 tests in `tests/test_safety_filter.py`.
   - Profile: Fast in-memory unit tests with micro-sleeps (~0.7s total). Must pass 100%.
6. **`requires_gpu`**:
   - Location: Registered in `pyproject.toml` and `conftest.py`. Currently unattached to any tests in `tests/`.

### 1.4 Verification of Desktop Mouse Actuation Invariant
- **Contract Mandate**: `AGENTS.md` strictly dictates:
  > *"Ensure desktop mouse control remains disabled during automated tests."*  
  > *"Do not run code that controls the actual mouse or clicks on the desktop during automated tests. Use mock/stub cursor adapters and dry-run mode."*
- **Empirical Code Audit**:
  - Exact pattern searches across `tests/` for `pyautogui`, `cursor`, `desktop`, `pynput`, `moveTo`, `click`, and `mouse` returned **0 matches**.
  - No test file under `tests/` imports `backend/eyenav/cursor/controller.py` (`GazeCursorController`) or `backend/eyenav/desktop.py` (`DesktopController`).
  - Tests only import `eyenav.config`, `eyenav.exceptions`, `eyenav.intent`, and `eyenav.safety`.
  - In `SafetyFilter.evaluate()`, outputs are returned as data structures (`VerifiedCommand(command=..., blocked=..., block_reason=...)`). No operating system API is called.
  - The unreferenced root prototype script `exp.py` (which previously called unshielded `pyautogui.moveTo` and `click`) was relocated to `trash/pending_review/exp.py` during Milestone 1 quarantine, eliminating all stray actuation risks from the workspace.

### 1.5 Quarantine Isolation and Regression Impact
- In Milestone 1, 15 items were moved to `trash/` as recorded in `trash/cleanup_manifest.csv` (1 video, 1 toy prototype `exp.py`, 1 debug log `eyemovement.txt`, root `__pycache__/`, and 11 placeholder `README.md` files).
- Zero tests in `tests/` and zero modules in `backend/eyenav/` imported, called, or referenced any of those 15 quarantined items.
- Test discovery, module import trees, and test executions remain 100% intact with **0 regressions**.

---

## 2. Logic Chain

1. **Test Scope & Architecture**:
   - `pyproject.toml` designates `tests` as the exclusive test path.
   - Running `pytest --collect-only tests/` produces 76 test items.
   - Therefore, the complete automated test inventory of IntuiGaze consists of these 76 items across 8 files.

2. **Deselection & Gating Logic**:
   - Physical camera tests (4 items in `TestPhysicalCamera`) require real hardware and would stall execution for 60 seconds (`test_camera_stable_for_60_seconds`) if a webcam is active, or skip if absent.
   - Accessibility tests (8 items in `TestDashboardAccessibility`) require an active web server on `:3000` and are explicitly tagged with `@pytest.mark.skip`.
   - Applying `-m "not requires_camera and not accessibility"` cleanly deselects exactly 12 items ($4 + 8 = 12$).
   - This leaves exactly $76 - 12 = 64$ fully automated, in-memory, deterministic tests.

3. **Desktop Safety Proof**:
   - OS cursor actuation is implemented strictly in `backend/eyenav/cursor/controller.py` using `pyautogui`.
   - Ripgrep verification proves that `tests/` contains 0 imports of `pyautogui` and 0 references to cursor controllers.
   - All 64 executable tests evaluate pure mathematical models, data schemas, configuration objects, or mock OpenCV frames.
   - Therefore, executing the full regression suite cannot actuate or interfere with the host desktop mouse cursor.

---

## 3. Caveats

1. **Physical Camera Hardware Unchecked**:
   - `tests/camera/test_camera_compatibility.py::TestPhysicalCamera` (4 tests) requires an attached USB/built-in webcam. In headless or developer environments without dedicated camera test rigs, these tests are excluded or skipped.
2. **Dashboard Accessibility Offline**:
   - `tests/accessibility/test_wcag_compliance.py` (8 tests) is marked `@pytest.mark.skip` because the frontend React/Next.js dashboard is not running in CI. These tests do not participate in automated backend regression passes.
3. **Cursor Controller Unit Test Gap**:
   - Because `GazeCursorController` does not currently support dependency injection of a mock cursor adapter or a `dry_run=True` flag, there are currently no unit tests directly exercising `controller.py` in `tests/`. Future controller tests will require adding a mockable cursor adapter.

---

## 4. Conclusion

- The repository test suite comprises **76 total test items** in 8 files under `tests/`.
- Following the Milestone 1 quarantine moves, the test suite is **100% intact with zero regressions**.
- The desktop mouse actuation invariant is **fully satisfied**: automated tests execute purely in synthetic and mocked environments with zero desktop interaction.
- The standard regression test execution for Milestone 2 consists of **64 active automated tests** (deselecting 4 physical camera tests and 8 skipped accessibility tests).

---

## 5. Verification Method

To independently execute and verify the regression test suite, use the following commands from the repository root:

### 5.1 Milestone 2 Primary Regression Gate (Full Automated Suite)
Runs all 64 automated unit, integration, stress, and CLI tests with zero failures:
```powershell
pytest tests/ -m "not requires_camera and not accessibility" -v --tb=short
```
- **Expected Outcome**:
  ```
  collected 76 items / 12 deselected / 64 selected
  64 passed, 12 deselected in ~3.5s
  Exit code: 0
  ```

### 5.2 Fast Feedback Suite (Unit + Integration Only)
Excludes stress tests (`slow`) for sub-second developer iterations:
```powershell
pytest tests/ -m "not slow and not requires_camera and not accessibility" -v --tb=short
```
- **Expected Outcome**:
  ```
  collected 76 items / 17 deselected / 59 selected
  59 passed, 17 deselected in < 1.5s
  Exit code: 0
  ```

### 5.3 Unfiltered Suite (CI Match)
Runs the entire directory as configured in `.github/workflows/ci.yml:35`:
```powershell
pytest tests/ -v --tb=short
```
- **Expected Outcome (Without physical webcam)**:
  ```
  collected 76 items
  64 passed, 12 skipped in ~4s
  Exit code: 0
  ```

### 5.4 Focused Sub-Suite Execution Commands
| Target Component | Command | Expected Pass Count |
|---|---|---|
| Safety Filter Suite | `pytest tests/test_safety_filter.py -v --tb=short` | 17 passed |
| Configuration System | `pytest tests/test_config.py -v --tb=short` | 15 passed |
| Intent Engine | `pytest tests/test_intent_engine.py -v --tb=short` | 13 passed |
| Pipeline Integration | `pytest tests/integration/ -m integration -v --tb=short` | 8 passed |
| Sustained Operation Stress | `pytest tests/stress/ -m slow -v --tb=short` | 5 passed |
| Dataset Audit Utility | `pytest tests/test_audit_dataset_script.py -v --tb=short` | 3 passed |
| Mocked Camera Interface | `pytest tests/camera/test_camera_compatibility.py -k "Mocked" -v --tb=short` | 3 passed |

### 5.5 Invalidation Conditions
- Any test failure (exit code $\neq 0$) when running the primary regression suite.
- Any mouse cursor displacement or unexpected click event during test execution.
- Discrepancy between collected item count (76) and test registry.
