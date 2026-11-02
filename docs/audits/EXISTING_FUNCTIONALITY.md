# IntuiGaze — Existing Functionality and Pipeline Analysis

**Document Date:** October 29, 2026  
**Auditor:** Antigravity (AI Coding Assistant)  
**Status:** Verified via Code Inspection and Baseline Execution  

---

## 1. End-to-End System Data Flow

```text
Physical Camera (OpenCV VideoCapture)
            │  RGB frame (e.g. 640x480 or 1280x720)
            ▼
FaceLandmarkExtractor (MediaPipe Tasks API)
            │  Loads face_landmarker.task (478 landmarks)
            │  Extracts: Iris centers (468, 473), EAR (33, 160, 158...), Head Pose (P, Y, R, Z)
            ▼
EyeLandmarks Feature Vector (12-dim)
            │  gaze_x, gaze_y, brow_raise, head_pitch, head_yaw, head_roll, etc.
            ▼
Gaze Mapping (Polynomial Regression / Ridge)
            │  GazeScreenMapper: degree=2 polynomial features mapped to (Screen X, Screen Y)
            │  Calibrated via 9-point or 50-point calibration routines
            ▼
Saccade & Fixation Filtering
            │  SaccadeDetector: Velocity & dispersion classification (FIXATION vs SACCADE)
            │  Fixation Gravity Well: Anchors cursor within 45px deadzone during fixations
            │  OneEuroFilter: Speed-adaptive jitter suppression
            ▼
Intent Recognition & Gesture Detection
            │  Blink Detector: EAR threshold < 0.18, duration 0.1s - 0.4s (Single click / Double blink)
            │  Brow Raise Detector: Relative forehead landmark displacement (Scroll up/down)
            │  Temporal Intent Engine: Sliding window transformer / classifier
            ▼
Multi-Layer Safety System
            │  Layer 1: Confidence threshold gate
            │  Layer 2: Command cooldown rate limiter
            │  Layer 3: Physical mouse movement override (>15px mouse displacement pauses 2s)
            │  Layer 4: PyAutoGUI corner failsafe (kills process immediately)
            ▼
Desktop Actuation (PyAutoGUI)
            Mouse cursor movement, click simulation, scroll events
```

---

## 2. Component Inventory

### 2.1 Vision & Landmarks (`backend/eyenav/vision/`)
- **`landmarks.py`**:
  - Encapsulates `FaceLandmarkExtractor` using Google MediaPipe Tasks FaceLandmarker.
  - Requires `face_landmarker.task` file.
  - Computes Eye Aspect Ratio (EAR) for left and right eyes based on standard 6-point eye contours.
  - Computes normalized iris center positions for left pupil (468) and right pupil (473).
  - Estimates 3D head pose (pitch, yaw, roll) and relative brow position.

### 2.2 Cursor Control & Mapping (`backend/eyenav/cursor/`)
- **`mapping.py` (`GazeScreenMapper`)**:
  - Uses `scikit-learn` `PolynomialFeatures(degree=2)` and `Ridge(alpha=1.0)`.
  - Fits calibration samples `(gaze_features, screen_coordinates)` and persists to `~/.eyenav/gaze_calibration.json`.
- **`saccade.py` (`SaccadeDetector`)**:
  - Tracks spatial velocity of raw eye coordinates. Classifies frames as `GazeState.FIXATION` or `GazeState.SACCADE`.
- **`controller.py` (`GazeCursorController`)**:
  - Orchestrates saccade tracking, fixation locking (anchors within 45px deadzone), and One Euro filtering.
  - Monitors physical mouse position; if mouse moves > 15 pixels externally, pauses eye tracking for 2.0 seconds.
- **`filter.py` (`OneEuroFilter`)**:
  - Dynamic low-pass filter with cutoff frequency tuned by movement velocity. Minimizes jitter at low speeds while eliminating lag during fast saccades.
- **`calibration.py` (`CalibrationSession`)**:
  - Fullscreen 9-point visual target routine for user-specific calibration.

### 2.3 Intent Recognition (`backend/eyenav/intent.py`)
- Defines 13 intent classes (`idle`, `reading`, `selecting`, `scrolling_up`, `scrolling_down`, `searching`, `activation`, `deactivation`, etc.).
- Maintains a 1.5-second temporal feature buffer (45 frames @ 30 FPS).
- Integrates with pre-trained models (`intent_classifier.pkl`).

### 2.4 Safety Filter (`backend/eyenav/safety.py`)
- Safety-critical component with 100% test coverage requirement.
- Risk-tiered confidence gates:
  - Low risk: 0.85
  - Medium risk: 0.92
  - High risk: 0.97
  - Critical risk: 0.99
- Enforces cooldown timers (300ms scroll, 800ms select, 1200ms back, 2000ms delete).
- Immediate emergency stop blocking all command emissions when triggered.

### 2.5 Operational Scripts (`scripts/`)
- `run_desktop.py`: Main interactive desktop controller launcher. Supports `--calibrate` and `--no-record`.
- `calibrate_ml.py`: 50-target pure Tkinter calibration data collection routine.
- `train_calibration_model.py`: Fits Random Forest regressor on calibration CSVs and saves to `spatial_mapper.pkl`.
- `audit_dataset.py`: Bounded-memory dataset auditing tool with unit tests.

---

## 3. Preserved Application Contracts

Any newly trained machine learning models must interface cleanly with:
1. **Input Contract:** MediaPipe landmark coordinates (or raw facial crops) formatted into consistent coordinate systems.
2. **Output Contract:** Calibrated screen coordinates `(x, y)` in pixels, or normalized coordinates `(norm_x, norm_y) \in [0, 1]`, with associated confidence estimates.
3. **Safety Guarantee:** No live desktop mouse manipulation without explicit user opt-in, physical mouse override active, and emergency corner failsafe enabled.

