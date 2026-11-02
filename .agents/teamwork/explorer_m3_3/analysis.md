# Technical Specification & Analysis: Baseline Hierarchy, Partitioning Invariants, and Safety Compliance

**Agent:** `explorer_m3_3`  
**Milestone:** M3 (ML Problem Definition Specification — Step 9)  
**Date:** October 29, 2026  
**Document Target:** `docs/ml/ML_PROBLEM_DEFINITION.md`  
**Working Directory:** `c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_3\`  
**Operating Contract:** `c:\Users\Voriganti\Downloads\INAV\AGENTS.md`  
**Skills Applied:** `experiment-management`, `dataset-auditing`, `cursor-safety-review`, `gaze-model-evaluation`

---

## 1. Executive Summary & Objective Alignment

The primary goal of Milestone 3 is to establish the formal problem definition, evaluation protocols, and operational constraints for IntuiGaze's machine learning pipelines in `docs/ml/ML_PROBLEM_DEFINITION.md`. 

While `explorer_m3_1` formulates the mathematical regression/classification task and loss functions, and `explorer_m3_2` defines the metric suites and error distribution reporting, this report (`explorer_m3_3`) specifies the **four structural and architectural pillars** required for scientific validity and safety:

1. **Baseline Model Hierarchy (Levels 0–3)**: Establishes a strict progression from trivial dumb baselines through closed-form linear mappers, non-linear tree ensembles, up to deep appearance neural networks.
2. **Dataset Partitioning & Leakage Prevention**: Enforces zero-participant overlap across train, validation, and test splits based on native MIT GazeCapture partitions (230 train / 7 val / 26 test) and cryptographically seals the final test set.
3. **Data Pipeline & Archive Constraints**: Preserves the 20.13 GB `archive.zip` intact on disk, specifies bounded-memory in-memory extraction for metadata JSONs, and defines strict multi-level quality filtering.
4. **Privacy, Safety & Ethical Invariants**: Enforces 100% on-device inference, zero video transmission, opt-in computer control, physical mouse override priority, 6-layer safety filtering, and compliance with `docs/business/ETHICS.md`.

---

## 2. Pillar 1: Baseline Model Hierarchy Specification

Per `AGENTS.md` and the `experiment-management` skill, complex deep learning models must never be evaluated in isolation. An honest, reproducible benchmark requires a disciplined baseline hierarchy where each successive model justifies its added latency, parameter count, and compute overhead by demonstrating measurable error reductions on identical evaluation partitions.

```
+-----------------------------------------------------------------------------------+
|                           BASELINE MODEL HIERARCHY                                |
+-----------------------------------------------------------------------------------+
|  Level 3: Deep Neural Network / Appearance CNN (L2CS-Net / iTracker)              |
|           Inputs: Face/Eye RGB Patches (224x224) + FaceGrid (25x25)               |
|           Latency: ~6-15 ms CPU | SOTA uncalibrated gaze tracking                 |
+-----------------------------------------------------------------------------------+
                                         ^
|  Level 2: Non-Linear Tabular Regressor (Random Forest / GBDT)                     |
|           Inputs: 6D-32D engineered facial/pupil landmarks + 3D head pose         |
|           Latency: ~1-2 ms CPU | Robust non-linear interaction modeling           |
+-----------------------------------------------------------------------------------+
                                         ^
|  Level 1: Polynomial Ridge Regression / Linear Mapper (GazeScreenMapper)          |
|           Inputs: Degree-2 polynomial expansion of 6D iris/pose features          |
|           Latency: <0.1 ms CPU | Closed-form O(1) online adaptation               |
+-----------------------------------------------------------------------------------+
                                         ^
|  Level 0: Trivial Center Dummy Baseline                                           |
|           Outputs: Static Screen Center (0.5, 0.5) or Empirical Training Mean     |
|           Latency: 0 ms CPU | Theoretical error floor and sanity gate             |
+-----------------------------------------------------------------------------------+
```

### 2.1 Level 0: Trivial Center Dummy Baseline

#### 2.1.1 Formulation & Objective
The Level 0 baseline establishes the theoretical performance floor. Any candidate ML model that fails to decisively outperform Level 0 on identical partitions has failed to extract meaningful gaze features.

Two distinct dummy modes must be reported:
1. **Static Screen Center Mode**:
   $$\hat{y}_{\text{center}} = (0.5, 0.5) \in [0, 1]^2$$
   or in pixel coordinates:
   $$\hat{y}_{\text{center, px}} = \left( \frac{W_{\text{screen}}}{2}, \frac{H_{\text{screen}}}{2} \right)$$
2. **Empirical Training Mean Mode**:
   $$\hat{y}_{\text{mean}} = \frac{1}{N_{\text{train}}} \sum_{i=1}^{N_{\text{train}}} y_i$$
   where $y_i$ are ground truth target coordinates on $S_{\text{train}}$.

#### 2.1.2 Scientific Purpose
Because human eye movements during computer navigation exhibit a pronounced **central fixation bias** (users fixate on central UI viewports more frequently than extreme screen corners), predicting the screen center often achieves a misleadingly low MAE (~0.22–0.28 normalized screen diagonal). Evaluating Level 0 prevents false claims of model efficacy and establishes the absolute minimum baseline that Level 1–3 models must beat by a mandatory margin ($\ge 30\%$ error reduction).

#### 2.1.3 Complexity
- **Trainable Parameters**: 0 (Static Center) or 2 scalars (Empirical Mean).
- **Runtime Compute**: $O(1)$ operations, $<0.001$ ms latency.
- **Memory**: $0$ KB.

---

### 2.2 Level 1: Polynomial Ridge Regression / Linear Mapper

#### 2.2.1 Formulation & Architecture
Directly builds upon `backend/eyenav/cursor/mapping.py` (`GazeScreenMapper`). Maps geometric facial and ocular landmarks to screen coordinates using regularized polynomial least squares.

1. **Raw Feature Vector** ($d = 6$):
   $$x = [p_{lx}, p_{ly}, p_{rx}, p_{ry}, \theta_{\text{yaw}}, \theta_{\text{pitch}}]^T \in \mathbb{R}^6$$
   where $(p_{lx}, p_{ly})$ and $(p_{rx}, p_{ry})$ are normalized pupil/iris center landmarks from MediaPipe (indices 468, 473) or GazeCapture eye bounding boxes, and $(\theta_{\text{yaw}}, \theta_{\text{pitch}})$ are 3D head pose angles in degrees.

2. **Polynomial Feature Expansion** $\Phi(x)$:
   - **Degree 1 (Linear)**:
     $$\Phi_1(x) = [1, x_1, x_2, x_3, x_4, x_5, x_6]^T \in \mathbb{R}^7$$
   - **Degree 2 (Quadratic without cross-terms)**:
     $$\Phi_{2,\text{diag}}(x) = [1, x_1, \dots, x_6, x_1^2, \dots, x_6^2]^T \in \mathbb{R}^{13}$$
   - **Degree 2 (Full Quadratic with pairwise interactions)**:
     $$\Phi_{2,\text{full}}(x) = \left[1, \{x_i\}_{i=1}^6, \{x_i x_j\}_{1 \le i \le j \le 6}\right]^T \in \mathbb{R}^{28}$$
   Degree 2 polynomial expansion captures the physical curvature of the eyeball and the non-linear perspective projection of gaze onto planar screens without overfitting.

3. **Ridge Regression Optimization**:
   Given training design matrix $\Phi(X) \in \mathbb{R}^{N \times P}$ and screen target matrix $Y \in \mathbb{R}^{N \times 2}$:
   $$\mathcal{L}(W) = \|\Phi(X)W - Y\|_F^2 + \lambda \|W\|_F^2$$
   Analytic closed-form solution:
   $$W^* = (\Phi(X)^T \Phi(X) + \lambda I)^{-1} \Phi(X)^T Y$$
   where $\lambda = 10^{-4}$ (matching `_RIDGE_LAMBDA` in `mapping.py`) to allow appropriate scale adaptation while ensuring non-singular inversion.

4. **Online Personal Adaptation (Rank-1 Update)**:
   When user fixation points are confirmed via intentional blink clicks, the model updates incrementally via the Sherman-Morrison rank-1 update without recomputing full matrix inversions:
   $$A_{t+1}^{-1} = A_t^{-1} - \frac{A_t^{-1} u_t u_t^T A_t^{-1}}{1 + u_t^T A_t^{-1} u_t}$$
   where $u_t = \sqrt{w_t} \Phi(x_t)$ and $w_t \in [0.2, 0.5]$ is the update learning weight.

#### 2.2.2 Strengths & Weaknesses
- **Strengths**: Deterministic, convex global optimum, ultra-fast inference ($<0.05$ ms on CPU), tiny storage footprint ($<2$ KB profile), fully explainable coefficients.
- **Weaknesses**: Assumes accurate upstream landmark localization; cannot correct for complex non-linear lighting artifacts, squinting, or asymmetric pupil deformations.

---

### 2.3 Level 2: Random Forest / Gradient Boosted Decision Trees Regressor

#### 2.3.1 Formulation & Architecture
Aligns with `scripts/train_calibration_model.py`. Operates as an intermediate non-linear tabular regressor on engineered landmark features, geometry vectors, and head pose.

1. **Expanded Tabular Feature Representation** ($z \in \mathbb{R}^{24}$):
   - Normalized pupil coordinates relative to inner/outer eye corners:
     $$u_L = \frac{p_{lx} - c_{l,\text{inner},x}}{c_{l,\text{outer},x} - c_{l,\text{inner},x}}, \quad v_L = \frac{p_{ly} - c_{l,\text{top},y}}{c_{l,\text{bottom},y} - c_{l,\text{top},y}}$$
   - Eye Aspect Ratio (EAR) for left and right eyes:
     $$\text{EAR} = \frac{\|p_2 - p_6\| + \|p_3 - p_5\|}{2 \|p_1 - p_4\|}$$
   - 3D Head Pose: pitch $\theta$, yaw $\psi$, roll $\phi$.
   - Inter-pupillary distance (IPD) normalized by face width.
   - Bounding box geometry: $(X_{\text{face}}/W, Y_{\text{face}}/H, W_{\text{face}}/W, H_{\text{face}}/H)$.
   - 25×25 FaceGrid spatial centroid $(\mu_{gx}, \mu_{gy})$ and grid occupancy ratio.

2. **Tree Ensemble Formulation**:
   Prediction is the ensemble mean of $M$ decision trees:
   $$\hat{y}(z) = \frac{1}{M} \sum_{m=1}^M T_m(z; \Theta_m)$$
   - **Random Forest Regressor**:
     - `n_estimators = 150`, `max_depth = 20`, `min_samples_split = 5`, `max_features = 'sqrt'`, `random_state = 42`.
   - **Gradient Boosted Trees (LightGBM/XGBoost candidate)**:
     - Objective: Huber loss / L2 loss, `learning_rate = 0.05`, `num_leaves = 31`, `n_estimators = 300`, `early_stopping_rounds = 20`.

#### 2.3.2 Strengths & Weaknesses
- **Strengths**: Handles non-monotonic feature relationships, invariant to feature scaling, robust to missing or noisy landmark dimensions, fast multi-threaded CPU inference (~1.0–2.5 ms).
- **Weaknesses**: High memory footprint for serialized tree forests (~25–60 MB), cannot backpropagate into upstream visual feature extractors.

---

### 2.4 Level 3: Deep Neural Network / Appearance CNN (L2CS-Net / iTracker)

#### 2.4.1 Formulation & Architecture
Direct appearance-based gaze estimation learning end-to-end visual representations from eye and face image patches.

1. **Input Streams**:
   - Left Eye Image Crop: $I_L \in \mathbb{R}^{224 \times 224 \times 3}$.
   - Right Eye Image Crop: $I_R \in \mathbb{R}^{224 \times 224 \times 3}$.
   - Face Image Crop: $I_F \in \mathbb{R}^{224 \times 224 \times 3}$.
   - Face Grid Tensor: $G \in \{0, 1\}^{25 \times 25}$.

2. **Candidate Architectures**:
   - **Candidate A: iTracker (MIT GazeCapture Native, Krafka et al. CVPR 2016)**:
     - Convolutional towers for $I_L$ and $I_R$ (shared or independent weights) $\to \text{FC}(128)$.
     - Convolutional tower for $I_F \to \text{FC}(64)$.
     - Fully connected network for $G \to \text{FC}(128) \to \text{FC}(16)$.
     - Fusion Layer: Concatenate $[f(I_L), f(I_R), f(I_F), f(G)] \in \mathbb{R}^{336} \to \text{FC}(128) \to \text{FC}(2) \to (\hat{x}, \hat{y})$.
   - **Candidate B: L2CS-Net with MobileNetV3 Backbone (Abdelrahman et al. 2023 / `backend/eyenav/vision/gaze.py`)**:
     - Input: Normalized face patch ($224 \times 224 \times 3$).
     - Backbone: Pretrained MobileNetV3-Large (~3.2M parameters).
     - Head: Dual binned classification branches (90 bins each for pitch and yaw over $\pm 45^\circ$, $2^\circ$ bin resolution).
     - Continuous Angle via Softmax Expectation:
       $$\hat{\theta} = \sum_{b=1}^{90} p_b \cdot c_b, \quad \hat{\psi} = \sum_{b=1}^{90} q_b \cdot d_b$$
     - Confidence Metric: Normalized Shannon entropy across output probability distributions:
       $$C = 1 - \frac{H(p) + H(q)}{2 \log(90)} \in [0, 1]$$
     - Ray-to-Screen Mapping: Direct projection of 3D gaze vector $\vec{g} = (\cos\hat{\theta}\sin\hat{\psi}, -\sin\hat{\theta}, -\cos\hat{\theta}\cos\hat{\psi})$ to screen plane coordinates via calibrated distance $D$.

#### 2.4.2 Strengths & Weaknesses
- **Strengths**: Highest uncalibrated cross-subject accuracy; learns fine-grained iris textures and corneal reflections; operates even when facial landmark tracking fails.
- **Weaknesses**: High computational latency (~6–15 ms on CPU without GPU), requires strict regularization to avoid demographic overfitting, larger memory footprint (~15–30 MB ONNX).

---

### 2.5 Summary Specification Matrix

| Level | Model Architecture | Primary Inputs | Parameters | Inference Latency (CPU) | Primary Role |
|---|---|---|---|---|---|
| **Level 0** | Trivial Center Dummy | None / Dummy | 0 – 2 | $< 0.001$ ms | Theoretical floor & sanity check |
| **Level 1** | Polynomial Ridge Mapper | 6D Iris + Head Pose | 14 – 56 | $< 0.05$ ms | Real-time personal calibration baseline |
| **Level 2** | Random Forest / GBDT | 24D Engineered Landmarks | ~1.5M (ensemble) | ~1.5 ms | Tabular non-linear feature baseline |
| **Level 3** | L2CS-Net / iTracker CNN | 224×224 Face/Eyes + FaceGrid | ~3.2M – 12M | ~6.0 – 12.0 ms | Appearance-based SOTA candidate |

---

## 3. Pillar 2: Dataset Partitioning & Leakage Prevention

### 3.1 Forensic Inventory of Native GazeCapture Splits
The dataset `archive.zip` contains 263 unique participants. The native partitioning stored in each participant's `info.json` (`Dataset` attribute) must be strictly maintained as the authoritative split:

| Partition | Participant Count (`subject_id`) | Total Video Frames | Share of Frames | Primary Role in ML Lifecycle |
|---|---|---|---|---|
| **`train`** | **230 subjects** | 289,591 frames | 82.89% | Feature extraction, representation learning, parameter optimization |
| **`val`** | **7 subjects** | 13,340 frames | 3.82% | Hyperparameter tuning, early stopping, model architecture selection |
| **`test`** | **26 subjects** | 46,438 frames | 13.29% | **Sealed** final release evaluation benchmark |
| **Total** | **263 subjects** | **349,369 frames** | **100.00%** | Comprehensive multi-device gaze corpus |

### 3.2 The Zero-Leakage Grouping Invariant
The most critical requirement in gaze estimation is **Participant-Group Isolation**:

$$\mathcal{S}_{\text{train}} \cap \mathcal{S}_{\text{val}} = \emptyset, \quad \mathcal{S}_{\text{train}} \cap \mathcal{S}_{\text{test}} = \emptyset, \quad \mathcal{S}_{\text{val}} \cap \mathcal{S}_{\text{test}} = \emptyset$$

where $\mathcal{S}$ denotes the set of unique participant directory IDs (`subject_id`).

#### Why Random Splitting is Prohibited (The Catastrophic Leakage Hazard)
1. **Temporal Video Correlation**: Each participant session comprises sequential video frames recorded at ~30 FPS tracking moving dot stimuli. Adjacent frames ($t$ and $t+1$) possess virtually identical:
   - Facial bone structure and eye morphology
   - Iris pigmentation and sclera vascular patterns
   - Head orientation and distance to camera
   - Room illumination, ambient shadows, and webcam optical sensor noise
2. **The Memorization Trap**: If frames are randomly shuffled across splits (e.g. standard `train_test_split(shuffle=True)` on frame rows), the model memorizes subject-specific facial appearance rather than learning true gaze mechanics.
3. **Deceptive Generalization**: Shuffled splits produce deceptively high accuracy (>98% Hit@25px) during training, but when deployed on a new participant, the model collapses completely (accuracy dropping below Level 0).
4. **Mandate**: All cross-validation must use `GroupKFold` or `LeaveOneGroupOut` grouped strictly by `subject_id`.

### 3.3 Cryptographic Test Set Sealing Rules
To prevent subtle test-set overfitting and metric contamination:
1. **The Sealing Policy**: `test_manifest.csv` must be cryptographically sealed.
2. **Access Prohibition During Development**: During pipeline construction, feature engineering, loss function ablation, hyperparameter tuning, and model checkpoint selection, **no script or agent is permitted to evaluate on `test_manifest.csv`**.
3. **Single Final Evaluation**: The test partition is evaluated exactly **once**, only when the candidate model architecture, weights, and decision thresholds are frozen for release.
4. **Audit Trail**: Every evaluation run on the test set must log:
   - Git commit hash of the model code
   - Model weights SHA-256 hash
   - Preprocessing configuration hash
   - Exact timestamp and evaluator identity

---

## 4. Pillar 3: Data Pipeline & Archive Handling Constraints

### 4.1 `archive.zip` Integrity Invariant
- **File Path**: `c:\Users\Voriganti\Downloads\INAV\archive.zip`
- **File Size**: Exactly `21,616,790,160` bytes (20.132 GB decimal).
- **SHA-256 Hash**: `48d2175ad792f82c2cea7df4d5763c4dc2bb781c3133c32b668ace251814d2c7`.
- **Absolute Preservation Rule**: The archive file must remain untouched, read-only, and **never uncompressed in bulk to disk**.
- **Rationale**:
  - Uncompressing 348,643 individual JPEG files would consume >21.4 GB of disk space.
  - Would risk exhausting Windows NTFS Master File Table (MFT) records and file system handles.
  - Triggers aggressive Windows Defender / search indexer file-locking slowdowns.
  - Directly violates Acceptance Criterion R2 ("Keep the original archive.zip intact").

### 4.2 Safe In-Memory Metadata Extraction
Tabular ground truth, screen coordinates, bounding boxes, and calibration values reside entirely within the **2,362 `.json` files** (totaling only 1.761 GB uncompressed).
The data extraction pipeline must:
1. Open `archive.zip` as a streaming read-only `zipfile.ZipFile` in Python.
2. Filter entry paths matching the pattern `*/*.json`.
3. Read and parse JSON content in-memory without staging raw JSON files to disk:
   ```python
   with zipfile.ZipFile("archive.zip", "r") as zf:
       with zf.open(f"{subject_id}/{subject_id}/dotInfo.json") as handle:
           dot_info = json.load(handle)
   ```
4. Join the parallel JSON arrays (`frames.json`, `dotInfo.json`, `screen.json`, `appleFace.json`, `appleLeftEye.json`, `appleRightEye.json`, `info.json`) row-by-row into structured tabular manifests:
   - `datasets/inav_gaze/manifests/archive_manifest.csv` (complete index)
   - `datasets/inav_gaze/manifests/train_manifest.csv` (230 subjects)
   - `datasets/inav_gaze/manifests/val_manifest.csv` (7 subjects)
   - `datasets/inav_gaze/manifests/test_manifest.csv` (26 subjects)
5. During deep model training (Level 3), individual `.jpg` image frames are streamed dynamically from `archive.zip` using a custom PyTorch `Dataset` that reads byte slices directly via `zf.open(archive_frame_path)`.

### 4.3 Data Quality Filtering Criteria (Exclusion Rules)
Raw crowdsourced mobile data contains significant noise, blinks, and lost tracking. The data pipeline must enforce four deterministic quality filters:

1. **Face Validity Filter**:
   - Condition: `appleFace.IsValid == 1`.
   - Rejection Rate: ~5.94% of frames.
   - Rationale: Discards frames where the user turned away, face was out of camera FOV, or lighting was too dim for face detection.
2. **Eye Visibility Filter**:
   - Condition: `appleLeftEye.IsValid == 1 AND appleRightEye.IsValid == 1`.
   - Rejection Rate: ~31.63% of frames.
   - Rationale: Eliminates natural blinks, heavy eyelid droop (ptosis), squinting, or occlusion from glasses frames.
3. **Screen Bounding Box Sanity Filter**:
   - Condition:
     $$0.0 \le X_{\text{pts}} \le W_{\text{screen}} \quad \text{and} \quad 0.0 \le Y_{\text{pts}} \le H_{\text{screen}}$$
   - Normalized Coordinates:
     $$x_{\text{norm}} = \frac{X_{\text{pts}}}{W_{\text{screen}}} \in [0.0, 1.0], \quad y_{\text{norm}} = \frac{Y_{\text{pts}}}{H_{\text{screen}}} \in [0.0, 1.0]$$
   - Rationale: Eliminates stimulus transition artifacts where dots were positioned off-screen.
4. **Bounding Box Geometry Sanity**:
   - Condition: $W_{\text{face}} > 0, H_{\text{face}} > 0, W_{\text{eye}} > 0, H_{\text{eye}} > 0$.
   - Eye bounding boxes must be geometrically bounded within the face bounding box.

---

## 5. Pillar 4: Privacy, Safety & Ethical Invariants

### 5.1 On-Device Processing & Zero-Transmission Invariant
Gaze tracking data represents uniquely sensitive biometric telemetry (revealing cognitive focus, reading comprehension, fatigue, and potential neurological conditions as detailed in `docs/business/ETHICS.md`).

1. **Strict Local Processing**:
   - 100% of landmark extraction, gaze estimation, polynomial mapping, and intent classification must execute locally on the user's host CPU/device.
   - Zero network transmission: Raw webcam video frames, face/eye crops, facial landmark coordinates, and screen fixation coordinates must never be transmitted across a network or uploaded to external APIs.
2. **Ephemeral In-Memory Lifecycle**:
   - Raw video frames captured from the webcam live in volatile memory only for the duration of the per-frame inference pass (<20 ms).
   - Once landmarks or gaze vectors are computed, raw image buffers are immediately discarded. No video frames are written to disk.
3. **Local Calibration Profile Security**:
   - Calibration profiles (`~/.eyenav/gaze_calibration.json`) store only abstract regression coefficients ($W \in \mathbb{R}^{28 \times 2}$), never facial images or biometric identifiers.

### 5.2 Opt-In Actuation & Visual State Transparency
1. **Default Disabled State**:
   - Upon application launch, desktop cursor actuation is **dormant and disabled by default**.
   - Actuation requires explicit user opt-in via a dedicated UI switch or keyboard hotkey.
2. **Always-Visible HUD Indicator**:
   - When gaze control is active, a persistent, non-intrusive status overlay or border indicates:
     - Active Tracking State (Green: Calibrated / Yellow: Low Confidence / Red: Paused)
     - Current Interaction Mode (Cursor Navigation vs Scroll Mode)
     - Real-time tracking confidence metric ($C \in [0, 1]$)

### 5.3 Physical Override & Multi-Layer Failsafe
Motor control over the desktop must never be permanently ceded to eye gaze. As implemented in `backend/eyenav/cursor/controller.py` and `backend/eyenav/safety.py`:

```
+-----------------------------------------------------------------------------------+
|                        6-LAYER COMMAND SAFETY VERIFICATION                        |
+-----------------------------------------------------------------------------------+
|  Layer 6: Emergency Stop (3s sustained eye closure immediately halts actuation)   |
+-----------------------------------------------------------------------------------+
|  Layer 5: Anti-Pattern Detection (blocks triggers during saccades / reading)      |
+-----------------------------------------------------------------------------------+
|  Layer 4: Dwell Confirmation (high-risk clicks require sustained visual dwell)    |
+-----------------------------------------------------------------------------------+
|  Layer 3: Context Validation (verifies command compatibility with active window)   |
+-----------------------------------------------------------------------------------+
|  Layer 2: Cooldown Rate Limiter (inter-command spacing >= 1.0s)                   |
+-----------------------------------------------------------------------------------+
|  Layer 1: Confidence Threshold Gate (rejects predictions below confidence thresh) |
+-----------------------------------------------------------------------------------+
                                         |
                               FAIL-CLOSED POLICY
           (Any internal error or exception immediately blocks command execution)
```

1. **Physical Mouse Priority**:
   - If the user moves the physical mouse or trackpad by more than `_PHYSICAL_OVERRIDE_PX = 15` pixels, eye tracking immediately pauses for `_PHYSICAL_PAUSE_S = 2.0` seconds.
   - The user can instantly seize control by touching the physical mouse.
2. **Emergency Escape Gesture**:
   - Sustained eye closure for $>2.0$ seconds (or $>3.0$ seconds in `safety.py`) triggers an emergency stop, immediately freezing the cursor and disengaging all click triggers.
3. **OS-Level Corner Failsafe**:
   - `pyautogui.FAILSAFE = True` is permanently enabled, guaranteeing that slamming the cursor into any screen corner aborts execution.
4. **Fail-Closed Confidence Gating**:
   - Commands or clicks are blocked if tracking confidence falls below the adaptive safety threshold ($C < 0.70$).
   - If an unhandled exception or landmark detector dropout occurs, the system defaults to `Blocked(reason=SAFETY_FILTER_ERROR)`. Under no circumstances does the system fail "open" or emit spurious clicks.

### 5.4 Ethics Alignment (with `docs/business/ETHICS.md`)
1. **Demographic Equity**: Gaze models must not degrade for specific demographic groups. The benchmark must report stratified error across device types and participant demographics, requiring that no group underperforms the overall mean by $>5\%$.
2. **Anti-Surveillance Architecture**: The codebase strictly omits attention harvesting, worker productivity logging, or covert telemetry APIs.
3. **User Autonomy**: All filtering parameters (deadzone thresholds, dwell times, smoothing factors) are user-configurable in configuration files, rejecting paternalistic software lock-in.

---

## 6. Integration Blueprint for `docs/ml/ML_PROBLEM_DEFINITION.md`

The specifications from this analysis are structured for immediate insertion into `docs/ml/ML_PROBLEM_DEFINITION.md` under the following sections:

- **Section 4: Baseline Model Hierarchy** (Incorporate §2 above: Level 0 Dummy, Level 1 Polynomial Ridge, Level 2 Random Forest/GBDT, Level 3 L2CS-Net/iTracker).
- **Section 5: Dataset Partitioning & Leakage Prevention** (Incorporate §3 above: 230/7/26 split, zero-participant leakage, GroupKFold mandate, cryptographic test set sealing).
- **Section 6: Archive Invariants & Data Pipeline Constraints** (Incorporate §4 above: 20.13 GB archive preservation, in-memory JSON streaming, 4-point quality filtering).
- **Section 7: Privacy, Safety & Ethical Compliance** (Incorporate §5 above: 100% on-device, opt-in actuation, physical override, 6-layer safety filter, fail-closed policy).
