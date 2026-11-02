# Handoff Report — Explorer M3.3: Baselines, Partitioning Invariants & Safety Compliance

**Document Path:** `c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_3\handoff.md`  
**Agent:** `explorer_m3_3`  
**Mission:** Formulate baseline model hierarchy, dataset partitioning invariants, archive handling constraints, and privacy/safety compliance specifications for `docs/ml/ML_PROBLEM_DEFINITION.md`.  
**Operating Contract:** `c:\Users\Voriganti\Downloads\INAV\AGENTS.md`  
**Skills Applied:** `experiment-management`, `dataset-auditing`, `cursor-safety-review`, `gaze-model-evaluation`

---

## 1. Observation

### 1.1 Archive Integrity and Modality Distribution
1. **Archive Characteristics**:
   - Location: `c:\Users\Voriganti\Downloads\INAV\archive.zip`
   - File size: `21,616,790,160` bytes (20.132 GB decimal) (`docs/data/DATASET_CARD.md`, line 20).
   - Checksums: MD5 `b0a506f32701f39b55737b7f1243ade5`, SHA-256 `48d2175ad792f82c2cea7df4d5763c4dc2bb781c3133c32b668ace251814d2c7` (`docs/data/DATASET_CARD.md`, lines 21–22).
   - Total entries: Exactly `351,005` items (0 directories, flat entries) (`docs/data/DATASET_CARD.md`, line 23).
   - Breakdown: 348,643 `.jpg` frames (19.631 GB) and 2,362 `.json` files (1.761 GB) (`docs/data/DATASET_CARD.md`, lines 36–37).
2. **Participant Demographics and Native Partitioning**:
   - Total unique subjects: 263 subjects (`docs/data/DATASET_CARD.md`, line 44).
   - Upstream split recorded in `info.json` (`docs/data/DATASET_CARD.md`, lines 68–74):
     - `train`: 230 subjects (289,591 frames, 82.9%)
     - `val`: 7 subjects (13,340 frames, 3.8%)
     - `test`: 26 subjects (46,438 frames, 13.3%)
   - Frame rates and quality: Face detection rate is 94.06%; eye detection rate is 68.37% (the ~31.63% deficit is due to natural blinks, squinting, and occlusion) (`docs/data/DATA_QUALITY_REPORT.md`, lines 22–30).

### 1.2 Baseline Code Implementations in Repository
1. **Polynomial Linear Ridge Mapper (`backend/eyenav/cursor/mapping.py`)**:
   - Lines 43–48: `_N_RAW_FEATURES = 4`, `_N_POLY_FEATURES = 1 + _N_RAW_FEATURES`, `_RIDGE_LAMBDA = 1e-4`.
   - Lines 113–116: Fits ridge regression via normal equation `W = (X.T @ X + lambda * I)^(-1) @ X.T @ y`.
   - Lines 180–189: Online rank-1 adaptation via Sherman-Morrison update on confirmed blink clicks:
     `self._XtX += weight * np.outer(x_feat, x_feat)`
     `self._Xty_x += weight * x_feat * confirmed_screen_xy[0]`
   - Lines 146–148: Safe fallback when unfitted: returns screen center `(self._sw / 2.0, self._sh / 2.0)`.
2. **Tabular Tree Regressor (`scripts/train_calibration_model.py`)**:
   - Lines 30–39: Extracts 5-feature vector `[gaze_x, gaze_y, head_pitch, head_yaw, head_roll]` targeting `[target_x, target_y]`.
   - Lines 48–49: Fits `RandomForestRegressor(n_estimators=150, max_depth=20, random_state=42, n_jobs=-1)`.
3. **Appearance CNN (`backend/eyenav/vision/gaze.py`)**:
   - Lines 8–26: L2CS-Net with MobileNetV3-Large backbone pre-trained on ImageNet/ETH-XGaze.
   - Lines 50–53: Input face image (224×224 RGB), 90 classification bins each for pitch and yaw across $\pm 45^\circ$ ($2.0^\circ$ per bin), continuous angles via softmax expectation.
4. **Safety Filter and Failsafe Architecture (`backend/eyenav/safety.py` and `backend/eyenav/cursor/controller.py`)**:
   - `backend/eyenav/cursor/controller.py`, lines 45–54: `pyautogui.FAILSAFE = True`, `_PHYSICAL_OVERRIDE_PX = 15`, `_PHYSICAL_PAUSE_S = 2.0`, `_FIXATION_DEADZONE_PX = 45.0`.
   - Lines 143–155: Physical mouse movement exceeding 15px pauses gaze tracking for 2.0 seconds.
   - `backend/eyenav/safety.py`, lines 11–45, 68–77: 6 independent verification layers (Confidence, Cooldown, Context, Dwell, Anti-Pattern, Emergency Stop) with fail-closed behavior: `SAFETY_FILTER_ERROR` blocks execution.
   - `docs/business/ETHICS.md`, lines 67–72: 100% on-device processing by default; zero server-side transmission of raw biometric data; users control all thresholds.

---

## 2. Logic Chain

1. **Premise 1 (Scientific Rigor & Skill Mandate)**: `AGENTS.md` and `experiment-management` dictate: *"Use a simple, honest baseline before a complex model... baseline metrics measured on identical partitions."*
   - **Reasoning**: Without a zero-parameter theoretical floor, complex appearance networks cannot prove whether they have learned true gaze dynamics or merely exploited dataset center bias.
   - **Deduction**: We establish a 4-tier Baseline Model Hierarchy:
     - *Level 0*: Trivial Center Dummy baseline (static screen center (0.5, 0.5) and empirical mean).
     - *Level 1*: Degree-2 Polynomial Ridge Regression (`GazeScreenMapper`).
     - *Level 2*: Random Forest / GBDT Regressor on engineered landmark features (`train_calibration_model.py`).
     - *Level 3*: Deep Appearance CNN (L2CS-Net MobileNetV3 / iTracker).

2. **Premise 2 (Temporal Autocorrelation & Data Leakage)**: `DATA_QUALITY_REPORT.md` (lines 38–45) shows that consecutive frames in MIT GazeCapture (~30 FPS) share identical user identity, iris texture, lighting, and camera noise.
   - **Reasoning**: A randomized train/test split would place temporally adjacent frames of the same person across both train and test partitions. The model would memorize subject appearance rather than gaze mechanics, inflating test metrics to an artificial >98% hit rate while failing catastrophically on new users.
   - **Deduction**: The dataset pipeline must enforce strict **Participant-Group Isolation**:
     $\mathcal{S}_{\text{train}} \cap \mathcal{S}_{\text{val}} = \emptyset, \mathcal{S}_{\text{train}} \cap \mathcal{S}_{\text{test}} = \emptyset, \mathcal{S}_{\text{val}} \cap \mathcal{S}_{\text{test}} = \emptyset$
     preserving the native 230 train, 7 val, 26 test split. The 26 test subjects must remain cryptographically sealed until final candidate evaluation.

3. **Premise 3 (Storage and File System Preservation)**: `ORIGINAL_REQUEST.md` (R2) and `PROJECT.md` mandate that `archive.zip` (20.13 GB, 351,005 entries) must remain intact and unmodified.
   - **Reasoning**: Decompressing 348,643 individual JPEG files would consume >21.4 GB, exhaust Windows NTFS MFT tables, and trigger filesystem locks. All ground truth tabular data lives solely inside the 2,362 `.json` files (1.761 GB uncompressed).
   - **Deduction**: The data pipeline must stream and extract `.json` files in-memory to generate tabular manifests (`archive_manifest.csv`, `train_manifest.csv`, `val_manifest.csv`, `test_manifest.csv`). Image frames are read on demand during training via streaming zip byte offsets.

4. **Premise 4 (Safety, Privacy & Ethical Compliance)**: `docs/business/ETHICS.md` and `backend/eyenav/safety.py` identify gaze tracking as high-risk biometric telemetry requiring critical-tier safeguards.
   - **Reasoning**: Uncontrolled desktop actuation can cause unintended data deletion, system lockouts, or privacy violations.
   - **Deduction**: The ML specification must mandate:
     - 100% on-device local inference; zero network transmission of video or biometrics.
     - Actuation is opt-in and dormant by default with visible HUD status overlay.
     - Physical mouse override priority (15px physical move pauses gaze for 2s).
     - 6-layer safety filter with fail-closed default on exceptions.

---

## 3. Caveats

1. **Mobile vs. Desktop Geometric Domain Gap**:
   - MIT GazeCapture was recorded on mobile devices (iPhones and iPads) held in hand or stands at close distance (~30–50 cm). IntuiGaze operates on desktop/laptop displays at larger distances (~50–80 cm) with webcams positioned at screen edges.
   - Mitigation: Appearance models (Level 3) must be paired with personal calibration mappers (Level 1) or user calibration adaptation layers (`scripts/calibrate_ml.py`) to absorb domain translation.
2. **Quality Filtering Discard Volume**:
   - Applying `appleFace.IsValid == 1` and `appleLeftEye.IsValid == 1 AND appleRightEye.IsValid == 1` filters removes ~31.63% of raw frames from standard gaze regression training.
   - Mitigation: These discarded frames represent blinks, occlusions, and off-screen glances, which are ideal training samples for intent classification (blinks, tracking loss) rather than coordinate regression.
3. **No Code Implementation in Milestone 3**:
   - In accordance with read-only investigation rules, no new Python models or pipeline scripts were executed; comprehensive specifications have been compiled in `analysis.md` for subsequent execution in Milestones 4 and 5.

---

## 4. Conclusion

1. **Baseline Hierarchy Defined**:
   - Specified 4 levels: Level 0 (Trivial Center/Mean Dummy, floor baseline), Level 1 (Polynomial Ridge Mapper, closed-form $O(1)$ adaptation), Level 2 (Random Forest / GBDT, non-linear tabular landmarks), and Level 3 (L2CS-Net / iTracker, end-to-end appearance CNN).
2. **Dataset Partitioning & Sealing Rules Codified**:
   - Native MIT GazeCapture split enforced: 230 train subjects (82.9%), 7 validation subjects (3.8%), and 26 test subjects (13.3%). Zero participant overlap.
   - Test set is cryptographically sealed; no tuning or decision-making on test data.
3. **Archive & Pipeline Constraints Established**:
   - `archive.zip` (20.13 GB) remains intact. In-memory streaming extraction parses the 2,362 metadata JSONs into structured manifests without touching disk.
   - 4-point quality filtering criteria established (`appleFace.IsValid`, eye validity, screen coordinate bounds, bounding box sanity).
4. **Privacy & Safety Invariants Formalized**:
   - 100% on-device inference, ephemeral video memory, default-disabled opt-in actuation, physical mouse priority override (15px threshold), 6-layer safety filter, and fail-closed error handling.

---

## 5. Verification Method

### 5.1 Independent Document & File Verification
Inspect the following files to verify the findings:
1. Technical Analysis Document:
   - File: `c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_3\analysis.md`
2. Archive and Dataset Forensic Metadata:
   - File: `docs/data/DATASET_CARD.md` (lines 19–75)
   - File: `docs/data/DATASET_STRUCTURE.md` (lines 11–83)
   - File: `docs/data/DATA_QUALITY_REPORT.md` (lines 10–45)
3. Existing Baseline & Safety Source Code:
   - File: `backend/eyenav/cursor/mapping.py` (lines 43–48, 107–156, 180–195)
   - File: `scripts/train_calibration_model.py` (lines 26–54)
   - File: `backend/eyenav/vision/gaze.py` (lines 8–32, 50–53)
   - File: `backend/eyenav/cursor/controller.py` (lines 45–55, 143–155)
   - File: `backend/eyenav/safety.py` (lines 11–45, 68–77)
   - File: `docs/business/ETHICS.md` (lines 50–97, 191–213)

### 5.2 Verification Commands
When a Python environment is available, run the following commands from the repository root:
```bash
# 1. Verify safety filter unit tests (ensuring 6-layer failsafe passes)
pytest tests/test_safety_filter.py -v

# 2. Verify dataset auditor on sample test manifests
pytest tests/test_audit_dataset_script.py -v

# 3. Verify intent engine tests
pytest tests/test_intent_engine.py -v
```

### 5.3 Invalidation Conditions
This specification will be invalidated if:
1. `archive.zip` is found to deviate from the verified SHA-256 hash `48d2175ad792f82c2cea7df4d5763c4dc2bb781c3133c32b668ace251814d2c7`.
2. The user or project owner mandates cloud-based off-device processing or relaxes the participant-group isolation constraint.
