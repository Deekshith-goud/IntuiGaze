# IntuiGaze — Baseline Test & Lint Results

**Execution Timestamp:** 2026-10-29 21:24:25 UTC+05:30  
**Environment:** Python 3.14.3 (`.venv`), Windows 11  
**Command:** `.venv\Scripts\pytest -v --tb=short`  

---

## 1. Summary

| Check | Tool | Items / Files | Passed | Skipped | Failed | Status |
|---|---|---|---|---|---|---|
| **Unit & Integration Tests** | `pytest` 9.1.1 | 76 collected | 68 | 8 | 0 | **PASS** |
| **Linting & Code Style** | `ruff` 0.16.3 | `backend/`, `tests/` | All checks | 0 | 0 | **PASS** |
| **Type Checking** | `mypy` 2.3.1 | 20 source files (`backend/`) | 20 | 0 | 0 | **PASS** |

---

## 2. Test Suite Breakdown

### 2.1 Safety-Critical Tests (`tests/test_safety_filter.py`)
- `TestConfidenceThresholdGate` (5 tests): **100% PASSED**
- `TestCooldownRateLimiter` (3 tests): **100% PASSED**
- `TestEmergencyStop` (4 tests): **100% PASSED**
- `TestSafetyFilterResilience` (3 tests): **100% PASSED**
- `TestDwellConfirmation` (2 tests): **100% PASSED**
*Total: 17/17 passed (100% safety pass rate).*

### 2.2 Intent Engine Tests (`tests/test_intent_engine.py`)
- `TestIntentEngineInputValidation` (2 tests): **PASSED**
- `TestIntentEngineWithoutModel` (2 tests): **PASSED**
- `TestIntentPredictionFormat` (4 tests): **PASSED**
- `TestExplanationGeneration` (2 tests): **PASSED**
- `TestIntentConstants` (3 tests): **PASSED**
*Total: 13/13 passed.*

### 2.3 Configuration Tests (`tests/test_config.py`)
- `TestConfigDefaults` (6 tests): **PASSED**
- `TestConfigFromFile` (4 tests): **PASSED**
- `TestConfigValidation` (4 tests): **PASSED**
- `TestConfigSerialization` (1 test): **PASSED**
*Total: 15/15 passed.*

### 2.4 Pipeline Integration Tests (`tests/integration/test_pipeline_integration.py`)
- `TestIntentToSafetyFlow` (6 tests): **PASSED**
- `TestConfigToSafetyBehavior` (2 tests): **PASSED**
*Total: 8/8 passed.*

### 2.5 Camera Compatibility Tests (`tests/camera/test_camera_compatibility.py`)
- `TestCameraInterfaceMocked` (3 tests): **PASSED**
- `TestPhysicalCamera` (4 tests): **PASSED** (achieves FPS, resolution, valid BGR, stable for 60 seconds)
*Total: 7/7 passed.*

### 2.6 Stress & Resilience Tests (`tests/stress/test_sustained_operation.py`)
- `TestSustainedSafetyFilter` (3 tests, including 10,000 evaluations and 1,000x emergency stop cycles): **PASSED**
- `TestTemporalBufferStress` (1 test, 1,000,000 frames buffer shift): **PASSED**
- `TestConcurrentEvaluations` (1 test, thread-safe evaluation): **PASSED**
*Total: 5/5 passed.*

### 2.7 Dataset Auditor Script Tests (`tests/test_audit_dataset_script.py`)
- `test_inventory_and_csv_manifest`: **PASSED**
- `test_jsonl_manifest`: **PASSED**
- `test_missing_root_is_rejected`: **PASSED**
*Total: 3/3 passed.*

### 2.8 Accessibility Tests (`tests/accessibility/test_wcag_compliance.py`)
- 8 tests collected: **8 SKIPPED**
- Reason: The Next.js frontend dashboard server was not running during the test session. This is an expected and non-blocking skip in standard headless/offline CI.

---

## 3. Linter Execution Details

Command: `.venv\Scripts\ruff.exe check backend/ tests/`
Output:
```text
warning: The following rules have been removed and ignoring them has no effect:
    - ANN101

All checks passed!
```

---

## 4. Type Checker Execution Details

Command: `.venv\Scripts\mypy.exe backend`
Output:
```text
Success: no issues found in 20 source files
```

