# EyeNav — Testing Documentation (TEST_PLAN.md)

**Document Version:** 1.0  
**Status:** Approved  
**Owner:** QA Engineering  
**Last Updated:** 2024-Q4  

---

## 1. Overview

This document defines the complete testing strategy for EyeNav v1.0. Every feature must be tested. No production release without all P0 tests passing.

**Testing Philosophy:**
- Safety tests MUST achieve 100% pass — not 99%, not 99.9%
- Test the failure cases first, not just the happy paths
- Tests are executable documentation — they communicate behavior
- Every bug fix requires a regression test

---

## 2. Test Coverage Requirements

| Module | Required Coverage | Rationale |
|---|---|---|
| `safety.py` | 100% line coverage | Safety-critical — zero blind spots |
| `intent.py` | ≥ 90% | Core functionality |
| `config.py` | ≥ 85% | Config bugs cause hard-to-diagnose failures |
| `pipeline.py` | ≥ 80% | Integration coverage supplemented by E2E |
| `vision/gaze.py` | ≥ 80% | Model-backed — some coverage from integration |
| `exceptions.py` | ≥ 70% | Simple hierarchy |

---

## 3. Test Types

### 3.1 Unit Tests (`tests/test_*.py`)

**Purpose:** Test individual functions and classes in isolation.  
**Framework:** pytest  
**Mocking:** unittest.mock, pytest-mock  
**Run:** `pytest tests/ -m "not integration and not requires_camera" -v`

**Existing unit test files:**
- `tests/test_safety_filter.py` — Safety filter (15+ tests)
- `tests/test_intent_engine.py` — Intent engine
- `tests/test_config.py` — Configuration management

### 3.2 Integration Tests (`tests/integration/`)

**Purpose:** Verify that pipeline stages interact correctly.  
**Framework:** pytest  
**Run:** `pytest tests/integration/ -m integration -v`

Key integration tests:
- Config → SafetyFilter initialization
- IntentPrediction → SafetyFilter evaluation flow
- Pipeline frame processing end-to-end (mocked camera + models)

### 3.3 Performance Tests (`benchmarks/`)

**Purpose:** Verify performance requirements from SRS-PERF-*.  
**Framework:** pytest-benchmark  
**Run:** `pytest benchmarks/ --benchmark-only -v`

Requirements verified:
- SRS-PERF-001: Pipeline FPS ≥ 30fps
- SRS-PERF-002: Latency p95 ≤ 200ms
- SRS-PERF-003: Gaze estimate ≤ 33ms
- SRS-PERF-004: CPU ≤ 30%
- SRS-PERF-005: RAM ≤ 512MB

### 3.4 Stress Tests (`tests/stress/`)

**Purpose:** Verify system stability under sustained operation.  
**Framework:** Custom stress harness  
**Run:** `pytest tests/stress/ -m slow -v`

Tests:
- 8-hour synthetic operation (SRS-PERF-007: MTBF ≥ 8 hours)
- Memory leak detection over 1-hour operation
- CPU usage stability over 30-minute operation
- Pipeline recovery after camera disconnection

### 3.5 Accessibility Tests (`tests/accessibility/`)

**Purpose:** Verify the dashboard UI meets WCAG 2.2 AA.  
**Framework:** axe-core (via playwright), manual audit  
**Run:** `pytest tests/accessibility/ -v`

Tests:
- All interactive elements have accessible names
- Color contrast meets 4.5:1 minimum
- All functionality keyboard-accessible
- Focus order is logical
- Error messages are text-described

### 3.6 Cross-Platform Tests (CI Matrix)

**Purpose:** Verify EyeNav works on all supported platforms.  
**Implementation:** GitHub Actions matrix (`ubuntu-latest`, `windows-latest`, `macos-latest`)

Platform-specific concerns:
- Windows: SendInput API, DirectShow camera
- macOS: AVFoundation camera, CGEvent permissions
- Linux: V4L2 camera, AT-SPI2 accessibility

### 3.7 Camera Compatibility Tests (`tests/camera/`)

**Purpose:** Verify EyeNav works with diverse camera hardware.  
**Framework:** Real camera required (`@pytest.mark.requires_camera`)

Test matrix (requires physical devices):
- Logitech C920 (reference camera)
- Logitech C270 (budget, 720p)
- Microsoft LifeCam (Windows reference)
- MacBook built-in FaceTime camera
- Phone camera via USB (Android DroidCam)
- IR camera (Windows Hello class)

Metrics per camera:
- Face detection rate at 1m, 0.5m, 1.5m
- Gaze estimation accuracy (5-point grid)
- FPS sustained over 60 seconds

### 3.8 User Acceptance Tests (`tests/uat/`)

**Purpose:** Verify real users can complete navigation tasks.  
**Framework:** Manual protocol (researchers observe, measure)  
**Participants:** Min. 50 users (accessibility users + able-bodied)

UAT tasks:
1. Setup from scratch (measure: time to first command)
2. 5-point calibration (measure: time, MAE result)
3. Scroll task: find target content by scrolling
4. Select task: click a specific link
5. Navigation task: back, forward, home
6. Emergency stop: trigger and recover
7. Reading task: read text without triggering commands

Success metrics:
- ≥ 80% task completion rate
- ≤ 3 false positives per task session
- ≥ 80/100 SUS score
- ≤ 5 minutes setup time

---

## 4. Test Markers

```python
# All tests should use appropriate markers:
@pytest.mark.safety_critical    # Safety tests — must always pass
@pytest.mark.slow               # > 1 second run time
@pytest.mark.requires_camera    # Needs physical camera
@pytest.mark.requires_gpu       # Needs GPU
@pytest.mark.integration        # Integration test
@pytest.mark.benchmark          # Performance benchmark
```

---

## 5. CI/CD Test Gates

Tests that block merging to `main`:

| Test Suite | Must Pass |
|---|---|
| Safety tests (`-m safety_critical`) | 100% — zero failures |
| Unit tests | 100% |
| Integration tests | 100% |
| Coverage check | ≥ 80% overall |
| Type checking (mypy) | Clean |
| Linting (ruff) | Clean |

Tests that run in nightly CI only:

| Test Suite | Schedule |
|---|---|
| Stress tests (8-hour) | Nightly 2:00 AM |
| Performance benchmarks | Nightly 3:00 AM |
| Camera compatibility | Weekly (requires hardware) |

---

## 6. Test Data

### 6.1 Synthetic Test Data

Most unit tests use synthetic data:
- Random feature buffers of shape (45, 32)
- Mock IntentPrediction objects with controlled fields
- Deterministic random seeds for reproducibility

### 6.2 Recorded Test Data

For gaze estimation tests, small clips of face video are stored in `tests/fixtures/video/`:
- `face_frontal_30fps.mp4` — Frontal face, standard lighting
- `face_glasses_30fps.mp4` — Thick-framed glasses
- `face_low_light_30fps.mp4` — Low lighting conditions
- `face_blinks_30fps.mp4` — Deliberate blink sequences

These are synthetic/consented recordings, not real user data.

---

## 7. Test Writing Guidelines

```python
class TestMyModule:
    """Group related tests in a class."""
    
    @pytest.fixture
    def subject(self) -> MyModule:
        """Return a fresh instance for each test."""
        return MyModule(config=Config())
    
    def test_happy_path(self, subject):
        """Test the expected normal behavior — explicit name."""
        result = subject.process(valid_input)
        assert result.status == "success"
    
    def test_invalid_input_raises_valueerror(self, subject):
        """Test error cases — name says what raises."""
        with pytest.raises(ValueError, match="expected pattern"):
            subject.process(None)
    
    @pytest.mark.safety_critical
    def test_failure_defaults_to_safe(self, subject):
        """Safety test — exceptions must produce safe outcome."""
        with patch.object(subject, '_internal', side_effect=RuntimeError):
            result = subject.process(valid_input)
        assert result.blocked  # Failure → blocked, not permitted
```

---

## 8. Regression Test Policy

For every production bug:

1. Write a test that **fails** on the buggy code
2. Fix the bug
3. Verify the test now **passes**
4. Commit test and fix together in the same PR
5. Add `# Regression: GH-{issue_number}` comment to the test
