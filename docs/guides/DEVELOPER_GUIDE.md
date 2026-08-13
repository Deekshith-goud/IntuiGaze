# EyeNav — Developer Guide

**Version:** 1.0  
**Audience:** Software engineers contributing to or integrating with EyeNav  

---

## 1. Architecture Overview

Before writing any code, read these documents in order:

1. [VISION.md](../product/VISION.md) — Why EyeNav exists
2. [SYSTEM_ARCHITECTURE.md](../architecture/SYSTEM_ARCHITECTURE.md) — How the system is structured
3. [ML_ARCHITECTURE.md](../architecture/ML_ARCHITECTURE.md) — How each model works
4. [SAFETY_SYSTEM.md](../architecture/SAFETY_SYSTEM.md) — Safety-critical design

---

## 2. Development Setup

### 2.1 Prerequisites

- Python 3.11+
- Git
- Docker (for server mode development)
- Node.js 18+ (for frontend development)

### 2.2 Environment Setup

```bash
# Clone repository
git clone https://github.com/eyenav/eyenav.git
cd eyenav

# Create virtual environment
python -m venv .venv

# Activate
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Download models via DVC
dvc pull
```

### 2.3 Verify Setup

```bash
# Run the test suite
pytest tests/ -v

# Run linting
ruff check backend/

# Run type checking
mypy backend/eyenav/

# Start the server (requires model files)
python -m uvicorn backend.eyenav.server:app --reload --port 8765
```

---

## 3. Adding a New Module

Follow this checklist when adding a new pipeline module:

### Step 1: Research (Required)
- Document the problem in `research/<module_name>/README.md`
- Survey existing approaches
- Compare alternatives
- Select approach with justification

### Step 2: Design
- Create a design document in `docs/architecture/`
- Create an ADR for key decisions
- Define the module's interface (inputs, outputs, types)

### Step 3: Implement
- Create module in `backend/eyenav/<module_name>.py`
- Follow naming conventions (see below)
- Add full docstrings (Google style)
- Add type annotations to all public methods
- Add logging (see Logging Guidelines)

### Step 4: Test
- Create `tests/test_<module_name>.py`
- Minimum: unit tests for all public methods
- Safety-critical modules: also add integration tests
- Target: ≥ 80% coverage

### Step 5: Document
- Add module to README of its containing directory
- Add to API documentation if it exposes API surface
- Update CHANGELOG.md

---

## 4. Code Style

### 4.1 Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Module names | snake_case | `blink_detector.py` |
| Class names | PascalCase | `BlinkDetector` |
| Method names | snake_case | `detect_blink()` |
| Constants | UPPER_SNAKE_CASE | `EAR_THRESHOLD` |
| Private methods | `_` prefix | `_compute_ear()` |
| Type aliases | PascalCase | `FeatureBuffer` |

### 4.2 Docstring Format (Google Style)

```python
def estimate(
    self,
    face_image: np.ndarray,
    landmarks: Landmarks
) -> Optional[GazeEstimate]:
    """
    Estimate gaze direction from a face image.
    
    Brief description on first line. Longer description if needed,
    explaining the approach and any important implementation notes.
    
    Args:
        face_image: Full face image (H×W×3, uint8, BGR).
        landmarks: Facial landmarks from FaceMesh (468 points).
        
    Returns:
        GazeEstimate or None if estimation fails.
        
    Raises:
        ModelInferenceError: If ONNX inference raises an exception.
        
    Notes:
        - Input image is internally normalized.
        - Returns None rather than raising for soft failures.
        
    Example:
        >>> estimate = estimator.estimate(frame, landmarks)
        >>> print(estimate.gaze_screen)
        [0.52, 0.34]
    """
```

### 4.3 Logging Guidelines

```python
import logging
logger = logging.getLogger(__name__)

# Use module logger — NEVER use print()
logger.debug("Frame %d processed", frame_id)          # Verbose detail
logger.info("Calibration complete: MAE=%.2f°", mae)   # Normal operations
logger.warning("Low confidence: %.2f < %.2f", c, t)   # Potential issues
logger.error("Gaze model failed: %s", error)           # Failures
logger.exception("Unexpected error in pipeline", exc_info=True)  # With traceback

# NEVER log raw gaze data (privacy)
# NEVER log personal identifiers
```

---

## 5. Safety-Critical Development

The following modules are safety-critical and require elevated review:

- `backend/eyenav/safety.py` — SafetyFilter
- `backend/eyenav/vision/blink.py` — BlinkDetector  
- Any OS integration code

**Rules for safety-critical code:**

1. Every public method must have complete docstring
2. All error paths must be explicitly handled (no bare `except Exception: pass`)
3. Failures must default to the SAFE (blocking) behavior
4. Require sign-off from safety review lead before merging
5. Tests must cover all failure modes, not just happy paths

---

## 6. Testing

### 6.1 Test Structure

```
tests/
├── test_config.py              # Configuration tests
├── test_safety_filter.py       # Safety filter tests (safety-critical)
├── test_intent_engine.py       # Intent engine tests
├── test_gaze_estimator.py      # Gaze estimation tests
├── test_blink_detector.py      # Blink detection tests
├── test_pipeline.py            # End-to-end pipeline tests
└── fixtures/                   # Shared test fixtures
    ├── synthetic_frames.py     # Synthetic camera frames
    └── mock_models.py          # Mock ONNX models
```

### 6.2 Running Tests

```bash
# All tests
pytest tests/ -v

# Safety-critical tests only
pytest tests/ -m safety_critical -v

# With coverage
pytest tests/ --cov=backend/eyenav --cov-report=html

# Specific test file
pytest tests/test_safety_filter.py -v

# Benchmarks
pytest benchmarks/ --benchmark-only -v
```

### 6.3 Marking Tests

```python
import pytest

@pytest.mark.safety_critical
def test_emergency_stop_blocks_all():
    """Safety critical — must never fail."""
    ...

@pytest.mark.slow
def test_long_session_stability():
    """Slow test — runs 8-hour session simulation."""
    ...

@pytest.mark.requires_camera
def test_live_camera_pipeline():
    """Requires physical camera attached."""
    ...
```

---

## 7. Contributing a Model

To contribute a new or improved ML model:

1. **Benchmark existing baseline** — establish current performance numbers
2. **Research** — document your proposed approach with citations
3. **Train** — use EyeNav training scripts or your own setup
4. **Evaluate** — run full evaluation suite (accuracy + latency + bias)
5. **Export** — validate ONNX export matches PyTorch within 1e-5
6. **Submit PR** with:
   - Model implementation (PyTorch, `.py`)
   - ONNX export (linked via DVC)
   - Evaluation results (JSON + plots)
   - Comparison to baseline
   - ADR update (if architecture changes)

---

## 8. API Development

When adding API endpoints:

1. Add to `docs/api/API_REFERENCE.md` first (design before code)
2. Define request/response schemas as Pydantic models
3. Add to FastAPI router with full docstring
4. Add integration test
5. Ensure endpoint appears in OpenAPI docs at `/docs`

---

## 9. Getting Help

- GitHub Discussions: Design questions, architecture proposals
- GitHub Issues: Bug reports, feature requests
- Email: research@eyenav.ai (research collaboration)
- Discord: Developer community (link in README)
