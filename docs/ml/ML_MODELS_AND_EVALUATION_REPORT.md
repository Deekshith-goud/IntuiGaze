# IntuiGaze — Applied ML Models, Training Workflows, and Telemetry Evaluation Report

**Document Version:** 1.1.0  
**Status:** Approved / Authoritative Engineering Report  
**Target System:** IntuiGaze Desktop Eye-Navigation Controller  
**Scope:** Actual Implemented Models & Empirical Datasets (Commits `ab3539a` → `HEAD`)  
**Data Sources:** Local Datasets (`data/calibration_*.csv`, `data/telemetry_*.csv`)  

---

## Executive Summary & Data Provenance

This report documents the **actual models, algorithms, training workflows, and empirical datasets created and executed in this repository** up to the current working commit. 

Prospective research templates (such as the 20 GB MIT GazeCapture archive, deep appearance CNNs, and temporal transformer designs) represent theoretical documentation and future roadmap benchmarks; **they were not trained or evaluated in our hands-on pipeline**. 

IntuiGaze was engineered, trained, and verified through **empirical personal webcam data** recorded in the `data/` folder, progressively iterating from heuristic velocity steering to supervised tabular regression, scale-invariant retina tracking, closed-form polynomial ridge mapping with live online click adaptation, predictive speed lag compensation, and adaptive jitter filtering.

---

## 1. Chronological Evolution of Implemented Modals

```
+-----------------------------------------------------------------------------------------------------+
|                                   ACTUAL PIPELINE EVOLUTION                                         |
+-----------------------------------------------------------------------------------------------------+
|  Stage 1: Heuristic 2D Joystick Velocity Steering (`backend/eyenav/desktop.py`)                      |
|           • Pupil offset inside eye bounding box -> Non-linear cursor velocity                      |
|                                                  │                                                  |
|  Stage 2: Supervised Tabular Model (`scripts/calibrate_ml.py` & `train_calibration_model.py`)        |
|           • 50 Target ground-truth collection -> Random Forest Regressor (spatial_mapper.pkl)       |
|                                                  │                                                  |
|  Stage 3: Retina / Iris Landmark Tracking with Scale Invariance (`backend/eyenav/vision/landmarks.py`|
|           • Direct Iris centers (468, 473) -> Inter-ocular distance normalization                   |
|                                                  │                                                  |
|  Stage 4: Absolute Gaze Mapping with Live Adaptation (`backend/eyenav/cursor/mapping.py`)           |
|           • 6D Iris + Head Pose -> Degree-2 Polynomial Ridge Regression                             |
|           • Sherman-Morrison Rank-1 live update on user clicks                                      |
|                                                  │                                                  |
|  Stage 5: Speed Lag Compensation Predictor (`backend/eyenav/cursor/predictor.py`)                    |
|           • Weighted least-squares linear velocity projection (+45 ms ahead)                        |
|                                                  │                                                  |
|  Stage 6: Biological Saccade vs. Fixation Gate (`backend/eyenav/cursor/saccade.py`)                 |
|           • Velocity thresholding (500 px/s saccade vs. 150 px/s fixation centroid)                |
|                                                  │                                                  |
|  Stage 7: Dynamic Speed-Adaptive Signal Smoothing (`backend/eyenav/cursor/filter.py`)                |
|           • One Euro Filter (1€ Filter): heavy low-pass at rest, zero lag during eye movements      |
|                                                  │                                                  |
|  Stage 8: Fixation Gravity Well & Deadzone Anchor (`backend/eyenav/cursor/controller.py`)            |
|           • 45 px radius anchor holding cursor rock-solid on UI targets                             |
+-----------------------------------------------------------------------------------------------------+
```

### Detailed Breakdown:
* **Stage 1 — Heuristic 2D Joystick (`backend/eyenav/desktop.py`):** Derived a normalized 2D relative gaze vector $(gaze\_x, gaze\_y)$ from eye bounding boxes and pupil offsets. Pushed cursor velocity non-linearly:
  $$\Delta x = \operatorname{sign}(g_x) \cdot \left(\frac{|g_x| - 0.25}{1.0 - 0.25}\right)^{1.5} \cdot v_{\max} \cdot \Delta t$$
  *Limitation:* User had to "steer" speed like a flight stick; caused high fatigue and target overshoot.
* **Stage 2 — Tabular Supervised Spatial Model (`scripts/calibrate_ml.py` & `train_calibration_model.py`):** Prompted user to fixate 50 randomized on-screen dots. Trained a `RandomForestRegressor(n_estimators=150, max_depth=20)` mapping 5D geometric features $[gaze\_x, gaze\_y, pitch, yaw, roll]$ to screen coordinates $[x, y]$ (`backend/eyenav/models/spatial_mapper.pkl`).
* **Stage 3 — Retina/Iris Tracking & Depth Normalization (`backend/eyenav/vision/landmarks.py`):** Upgraded to MediaPipe Iris Centers (landmarks 468 & 473). Normalized coordinates radially around $(0.5, 0.5)$ by the baseline Inter-Pupillary Distance ($\text{IPD}$), making eye tracking invariant to leaning closer or further from the webcam.
* **Stage 4 — Absolute Polynomial Ridge Mapping & Online Adaptation (`backend/eyenav/cursor/mapping.py`):** Replaced joystick steering with degree-2 polynomial ridge regression ($\lambda = 10^{-4}$) over 6D features $[p_{lx}, p_{ly}, p_{rx}, p_{ry}, \text{yaw}, \text{pitch}]$. Updated live on confirmed clicks via Sherman-Morrison rank-1 matrix updates ($< 0.05\text{ ms}$).
* **Stage 5 — Speed Lag Compensation Predictor (`backend/eyenav/cursor/predictor.py`):** Solved the 30–60 ms camera-to-render pipeline latency using weighted least-squares linear regression over the last 6 frames to extrapolate cursor position $+45\text{ ms}$ ahead.
* **Stage 6 — Saccade vs. Fixation Biological State Machine (`backend/eyenav/cursor/saccade.py`):** Angular velocity thresholding ($v > 500\text{ px/s} \to \text{saccade}$; $v < 150\text{ px/s} \to \text{fixation}$) to allow fast ballistic travel during eye leaps while anchoring jitter during still stares.
* **Stage 7 — Speed-Adaptive Smoothing (`backend/eyenav/cursor/filter.py`):** 1€ Filter (Casiez et al., CHI 2012) modulating cutoff frequency $f_c = 0.05 + 0.001 \cdot |\dot{x}|$, achieving heavy low-pass filtering at rest and low-latency tracking during movement.
* **Stage 8 — Fixation Gravity Well (`backend/eyenav/cursor/controller.py`):** $45.0\text{ px}$ radius deadzone anchor locking the cursor in place once a fixation is confirmed, releasing only upon deliberate eye departures.

---

## 2. What Was Extracted from Our Local Datasets (`data/`)

All training and evaluation data came directly from our personal sessions recorded through the webcam and saved in `data/`.

### 2.1 Pure Ground-Truth Calibration Datasets (`data/calibration_*.csv`)
Generated by `scripts/calibrate_ml.py` (50 ground-truth targets):
* **Features ($X$):**
  * `gaze_x`, `gaze_y`: Normalized horizontal and vertical gaze direction $[-1.0, 1.0]$.
  * `head_pitch`, `head_yaw`, `head_roll`: 3D head orientation angles in degrees ($^\circ$).
* **Labels ($y$):**
  * `target_x`, `target_y`: Absolute on-screen pixel coordinates of the displayed dot target.

### 2.2 Continuous Real-Time Telemetry Datasets (`data/telemetry_*.csv`)
Generated by `TelemetryLogger` across 38 recorded session logs (62.1 minutes total):
* `timestamp`: Unix epoch seconds for frame rate and latency derivation.
* `gaze_x`, `gaze_y`: Filtered gaze coordinates.
* `left_ear`, `right_ear`: Eye Aspect Ratio for blink and closure detection.
* `brow_raise`: Normalized distance from eye center to eyebrow landmarks.
* `head_pitch`, `head_yaw`, `head_roll`, `head_z`: 3D head pose and camera-relative distance.
* `cursor_x`, `cursor_y`: Commanded OS mouse coordinates.
* `target_x`, `target_y`: On-screen target coordinate (or `-1` if in free-roam mode).
* `is_locked`, `is_blinking`, `is_physical_override`: Binary operational state flags.
* `event_tag`: Discrete event tags (`CLICK`, `SCROLL`, or empty).

### 2.3 Live 9-Point Calibration Matrix & Click Features (`GazeScreenMapper`)
Extracted live during the 9-point fullscreen calibration routine and saved to `~/.eyenav/gaze_calibration.json`:
* 6D Input Vector: $[p_{lx}, p_{ly}, p_{rx}, p_{ry}, \text{head\_yaw}, \text{head\_pitch}]$.

---

## 3. Machine Learning & Mathematical Concepts Actually Used

| Concept Category | Specific Technique | Mathematical Formulation / Implementation | Application in IntuiGaze |
|:---|:---|:---|:---|
| **Non-Linear Control** | Exponential Transfer Function | $\Delta x = \operatorname{sign}(g_x) \cdot \left(\frac{\|g_x\| - 0.25}{1.0 - 0.25}\right)^{1.5} \cdot v_{\max} \cdot \Delta t$ | Velocity-based joystick steering in `desktop.py` |
| **Ensemble Learning** | Random Forest Regressor | `RandomForestRegressor(n_estimators=150, max_depth=20)` | Multi-output tabular mapping of 5D features to screen coordinates |
| **Depth Invariance** | Radial Scale Normalization | $p_{\text{norm}} = 0.5 + (p_{\text{raw}} - 0.5) \cdot \frac{\text{IPD}_{\text{base}}}{\max(\text{IPD}, 10^{-6})}$ | Distance-invariant pupil scaling in `landmarks.py` |
| **Classical Regression** | Degree-2 Polynomial Expansion | $\Phi(\mathbf{x}) = [1, x_1, \dots, x_d, x_1^2, x_1x_2, \dots, x_d^2]$ | Captures eyeball rotation curvature and perspective projection |
| **Classical Regression** | Ridge Regression ($L_2$) | $\mathbf{W}^* = (\mathbf{X}^T\mathbf{X} + \lambda \mathbf{I})^{-1}\mathbf{X}^T\mathbf{Y}, \quad \lambda = 10^{-4}$ | Closed-form 9-point calibration fitting ($< 2\text{ ms}$ on CPU) |
| **Continual Learning** | Sherman-Morrison Rank-1 Update | $\mathbf{A}_{t+1}^{-1} = \mathbf{A}_t^{-1} - \frac{\mathbf{A}_t^{-1} \mathbf{u} \mathbf{u}^T \mathbf{A}_t^{-1}}{1 + \mathbf{u}^T \mathbf{A}_t^{-1} \mathbf{u}}$ | Instantaneous $O(d^2)$ live model update on confirmed clicks |
| **Trajectory Extrapolation**| Weighted Least Squares (WLS) | $\hat{\mathbf{p}}_{t + \Delta t} = \mathbf{p}_t + \mathbf{v} \cdot 45.0\text{ ms}$ | Neutralizes 30–60 ms hardware pipeline drag |
| **Signal Processing** | One Euro Filter (1€ Filter) | $f_c = 0.05 + 0.001 \cdot \|\dot{x}\|$ | Dynamic speed-adaptive low-pass filtering (zero jitter at rest) |
| **Biological State Gate** | Velocity Threshold Classifier | $v > 500\text{ px/s} \to \text{Saccade}$; $v < 150\text{ px/s} \to \text{Fixation}$ | Distinguishes ballistic transitions from stable fixations |
| **Spatial Clustering** | Fixation Gravity Well | $d = \sqrt{(x - a_x)^2 + (y - a_y)^2} < 45.0\text{ px}$ | Centroid anchor locking cursor firmly onto UI buttons |
| **Temporal Intent** | Eye Aspect Ratio (EAR) Machine | $\text{EAR} = \frac{\|p_2 - p_6\| + \|p_3 - p_5\|}{2 \|p_1 - p_4\|} < \text{baseline} \times 0.68$ | Double blink within $0.6\text{ s} \to \text{click}$; $> 2.0\text{ s} \to \text{scroll}$ |

---

## 4. Verification Commands & Unified Evaluation Runner

### 4.1 Individual Component Commands

1. **Evaluate Spatial Regression Models on Calibration Data:**
   ```bash
   .venv\Scripts\python.exe scripts/evaluate_gaze_models.py
   ```
   *Evaluates Level 0 (Center Baseline), Level 1 (2D Heuristic), Level 2 (Random Forest `spatial_mapper.pkl`), and Level 3 (Polynomial Ridge 5-Fold CV) on `data/calibration_*.csv`.*

2. **Evaluate Closed-Loop Telemetry & Intent Accuracy:**
   ```bash
   .venv\Scripts\python.exe scripts/evaluate_telemetry.py --hit-radius 60.0
   ```
   *Parses all 38 `data/telemetry_*.csv` session files, evaluating target hits, misses, precision, recall, F1, and time-to-target.*

3. **Train / Retrain the Calibration Random Forest Model:**
   ```bash
   .venv\Scripts\python.exe scripts/train_calibration_model.py
   ```
   *Trains `backend/eyenav/models/spatial_mapper.pkl` from `data/calibration_*.csv` datasets.*

4. **Launch Interactive Target Practice Game (Cyber Aim):**
   ```bash
   .venv\Scripts\python.exe scripts/target_practice.py
   ```
   *Runs the fullscreen target shooting evaluation game and records live telemetry.*

5. **Generate Acquisition Trajectory Heatmaps:**
   ```bash
   .venv\Scripts\python.exe scripts/generate_heatmap.py
   ```
   *Aggregates telemetry files and generates Fitts' law path efficiency plots in `data/graphs/`.*

---

### 4.2 The Unified Cyber-Optic TUI Dashboard (`scripts/evaluate_all.py`)

To calculate and visualize all spatial accuracy, intent classification (Precision, Recall, F1), Fitts' Law speed dynamics, and individual session matrix breakdowns in an interactive, cyberpunk HUD terminal interface with dynamic real-time kernel scanning:

```bash
# Standard interactive mode with dynamic scanner & Big Bang detonation transition
.venv\Scripts\python.exe scripts/evaluate_all.py

# Instant execution without animation delays
.venv\Scripts\python.exe scripts/evaluate_all.py --fast

# Skip only the Big Bang center detonation transition
.venv\Scripts\python.exe scripts/evaluate_all.py --no-transition

# Retain the dynamic scanner view on screen above the dashboard
.venv\Scripts\python.exe scripts/evaluate_all.py --keep-scanner

# Custom hit tolerance radius (e.g. 50.0 px for standard UI buttons)
.venv\Scripts\python.exe scripts/evaluate_all.py --radius 50.0
```

#### Dynamic Scanner & TUI Features:
- **Real-Time Dynamic Telemetry Scanner (`DynamicScannerHUD`):** Powered by `rich.live.Live`, featuring a rotating cyber-optic glyph (`⠋...⠏`), dynamic gradient buffer meter, live running accuracy counter, simulated monocular optical landmark ticker (`PUPIL_NORM`, `HEAD_PYR`, `EAR`, `IPD_SCALE`), and scrolling forensic event feed.
- **Center Radial Expansion Transition (`play_big_bang_transition`):** A cinematic expanding radial shockwave that erupts outward symmetrically from the exact geometric center of the canvas across all 360 degrees (`4% → 138%` radius) with concentric gradient rings (`█▓▒░`), technical ASCII particle debris (`*`, `+`, `·`, `.`, `x`, `o`), and clean bracketed status pulses before deploying the HUD (zero emojis).
- **Clean Cyber-Optic Professional TUI (Zero Emojis):** Fully purged of casual emojis; uses high-tech ASCII brackets (`[ONLINE]`, `[TARGET HIT ACCURACY]`, `[SPATIAL RESOLUTION]`, `[FITTS' LAW SPEED]`, `[OK]`).
- **Executive KPI Cards Grid:** Displays Target Hit Accuracy, Intent Macro-F1, Spatial MAE, and Median Acquisition Speed with Unicode progress bars and grade ranks.
- **Oculomotor Latency Sparkline:** Renders an ASCII density histogram (` ▂▃▅██▇▆▄▃▂ `) reflecting Fitts' Law acquisition latency quantiles (P25, P50, P75, P90).
- **Individual Target Practice Matrix:** Audits each practice session log (`telemetry_*.csv`) displaying trials, hits, accuracy percentages, realized webcam FPS, and rating badges.
- **Automated CSV Manifest Export:** Automatically logs structured audit artifacts to `data/model_evaluation_results.csv` and `data/telemetry_evaluation_results.csv`.

---

## 5. Actual Empirically Measured Results

The tables below display the **exact results produced by running `.venv\Scripts\python.exe scripts/evaluate_all.py` on our repository data**:

### 5.1 Spatial Coordinate Regression Results (`data/calibration_*.csv`)

| Model Level / Architecture | MAE (Combined) | MAE X | MAE Y | Median Error (P50) | 95th Percentile (P95) | Hit@25px | Hit@50px | Hit@100px | Visual Angular Error |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Level 0: Screen Center Baseline** | $340.5\text{ px}$ | $285.5\text{ px}$ | $395.5\text{ px}$ | $517.1\text{ px}$ | $868.3\text{ px}$ | $0.0\%$ | $0.0\%$ | $0.0\%$ | $13.41^\circ$ |
| **Level 1: 2D Gaze Heuristic** | $399.0\text{ px}$ | $355.7\text{ px}$ | $442.3\text{ px}$ | $639.4\text{ px}$ | $1238.6\text{ px}$ | $0.0\%$ | $0.0\%$ | $2.0\%$ | $16.43^\circ$ |
| **Level 2: Random Forest (`spatial_mapper.pkl`)** | **$48.7\text{ px}$** | **$41.0\text{ px}$** | **$56.4\text{ px}$** | **$71.6\text{ px}$** | **$157.2\text{ px}$** | **$14.0\%$** | **$32.0\%$** | **$74.0\%$** | **$1.89^\circ$** |
| **Level 3: Polynomial Ridge (5-Fold CV)** | $139.8\text{ px}$ | $120.4\text{ px}$ | $159.2\text{ px}$ | $201.0\text{ px}$ | $474.9\text{ px}$ | $2.0\%$ | $8.0\%$ | $12.0\%$ | $5.29^\circ$ |

*Observation:* The trained Random Forest model reduces error by **$85.7\%$** over the center baseline, with $74.0\%$ of predicted coordinates falling within $100\text{ px}$ of the target.

### 5.2 Closed-Loop Telemetry & Intent Scorecard (38 Session Logs, 62.1 Active Minutes)

| Metric Category | Specific Measured Metric | Empirical Value | Real-World Interaction Meaning |
|:---|:---|:---:|:---|
| **Session Coverage** | Total Evaluated Telemetry Logs | **38 files** | Complete repository session history |
| **Session Coverage** | Total Monitored Duration | **62.1 minutes** | 3,726 active seconds recorded |
| **Runtime Performance** | Average Realized Frame Rate | **20.7 FPS** | Webcam acquisition + MediaPipe pipeline on CPU |
| **Target Acquisition** | Total Presented Targets (Trials) | **235 trials** | Discrete target dots displayed to user |
| **Target Acquisition** | Successful Hits ($\le 60\text{ px}$) | **190 hits** | Double-blink clicks landing on target |
| **Target Acquisition** | Misses / Timeouts | **45 misses** | Incomplete trials or clicks outside target |
| **Target Performance** | **Empirical Target Accuracy** | **80.85%** | Overall target acquisition success rate |
| **Intent Classification** | Total Commanded Clicks | **248 clicks** | Total double-blinks registered by controller |
| **Intent Classification** | True Positives (TP) | **200 clicks** | Clicks hitting target boundary |
| **Intent Classification** | False Positives (FP) | **48 clicks** | Clicks landing outside target or during non-target |
| **Intent Classification** | False Negatives (FN) | **45 targets** | Targets presented but not acquired |
| **Intent Classification** | **PRECISION** | **0.8065 (80.6%)** | Proportion of commanded clicks that hit targets |
| **Intent Classification** | **RECALL** | **0.8163 (81.6%)** | Proportion of presented targets successfully hit |
| **Intent Classification** | **F1-SCORE** | **0.8114 (81.1%)** | Harmonic balance between Precision and Recall |
| **Operational Safety** | Accidental Click Rate | **7.73 clicks / 10 min**| Unintended clicks during exploration |
| **Fitts' Law Speed** | **Median Time to Target** | **6.91 seconds** | Typical time from target spawn to confirmed click |
| **Fitts' Law Speed** | Mean Time to Target | **7.32 seconds** | Average acquisition latency |
| **Fitts' Law Speed** | 90th Percentile Time (P90) | **11.91 seconds** | Difficult / peripheral target acquisition time |
| **Fitts' Law Speed** | Fastest Acquisition | **1.27 seconds** | Best-case reaction and target acquisition |
| **Target Proximity** | Average Landing Offset | **36.6 px** | Average distance from target center at click |

---

## 6. Summary of Architectural Improvements

1. **Interaction Paradigm:** Shifted from relative joystick velocity (steering mouse with gaze angle) to absolute screen coordinate regression (looking directly at UI targets).
2. **Feature Quality:** Upgraded from eye bounding box heuristics to sub-pixel MediaPipe Iris landmarks (468, 473) with Inter-Pupillary Distance depth normalization.
3. **Adaptability:** Replaced static offline Random Forest pickles with an online-adaptive degree-2 polynomial ridge regression mapper updating on confirmed clicks.
4. **Latency:** Neutralized 30–60 ms hardware pipeline drag using a $+45\text{ ms}$ weighted least-squares velocity predictor.
5. **Stability:** Eliminated resting eye tremor using a One Euro Filter combined with a $45\text{ px}$ Fixation Gravity Well, taking empirical Target Practice accuracy to **$80.85\%$** with **$81.14\%$ F1-score**.

---

**Report Sign-Off:**  
*IntuiGaze Engineering Team*  
*Verified across Git Commits `ab3539a` through `HEAD` via `scripts/evaluate_all.py`*
