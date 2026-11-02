# Handoff Report — Explorer 3: Dataset & ML Task Explorer

**Document Path:** `c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_survey_3\handoff.md`  
**Date:** 2026-10-29  
**Mission:** Survey dataset integration requirements, `archive.zip` contents, ML problem definition, and baseline model criteria.  
**Operating Contract:** `c:\Users\Voriganti\Downloads\INAV\AGENTS.md`  
**Skills Applied:** `dataset-auditing`, `gaze-model-evaluation`

---

## 1. Observation

### 1.1 `archive.zip` Physical & Forensic Characteristics
1. **Archive Location and Integrity**:
   - Path: `c:\Users\Voriganti\Downloads\INAV\archive.zip`
   - File size: `21,616,790,160` bytes (20.132 GB / 21.617 GB decimal) (`docs/data/DATASET_CARD.md`, lines 19–20; confirmed in `docs/audits/INITIAL_REPOSITORY_AUDIT.md`, line 27).
   - Checksums: MD5 `b0a506f32701f39b55737b7f1243ade5`, SHA-256 `48d2175ad792f82c2cea7df4d5763c4dc2bb781c3133c32b668ace251814d2c7` (`docs/data/DATASET_CARD.md`, lines 21–22).
   - Entry Count: Exactly `351,005` items (0 directory headers, all flat file entries) (`docs/data/DATASET_CARD.md`, line 23).
   - Uncompressed size: `22,969,309,215` bytes (21.392 GB), compression ratio 1.06:1 (`docs/data/DATASET_CARD.md`, lines 25–26).
   - Modality breakdown:
     - 348,643 `.jpg` images (19.631 GB)
     - 2,362 `.json` files (1.761 GB)
     (`docs/data/DATASET_CARD.md`, lines 34–38).
2. **Internal Hierarchy and Structure**:
   - Double-nested subject structure from upstream packaging: `<subject_id>/<subject_id>/` (`docs/data/DATASET_STRUCTURE.md`, lines 11–28). Example: `00002/00002/info.json` and `00002/00002/00000.jpg`.
   - Number of unique subjects: 263 subjects (`docs/data/DATASET_CARD.md`, line 44).
   - Average frames per subject: 1,325.6 frames (range: 11 to 3,590 frames) (`docs/data/DATASET_CARD.md`, line 45).
   - Per-subject annotation files present:
     - `frames.json`: Ordered array of frame filenames `["00000.jpg", "00001.jpg", ...]` providing row alignment across all parallel JSON arrays (`docs/data/DATASET_STRUCTURE.md`, lines 38–42).
     - `dotInfo.json`: Parallel arrays containing `DotNum` (`list[int]`), screen coordinates `XPts` and `YPts` (`list[float]`), 3D camera displacement `XCam` and `YCam` in centimeters (`list[float]`), and timestamp `Time` in seconds (`docs/data/DATASET_STRUCTURE.md`, lines 43–50).
     - `screen.json`: Parallel arrays for screen height `H`, width `W` in points, and `Orientation` (1: Portrait, 2: PortraitUpsideDown, 3: LandscapeRight, 4: LandscapeLeft) (`docs/data/DATASET_STRUCTURE.md`, lines 52–57).
     - `appleFace.json`: Face bounding box `X`, `Y`, `W`, `H` and validity flag `IsValid` (`list[int]`) (`docs/data/DATASET_STRUCTURE.md`, lines 58–63).
     - `appleLeftEye.json` / `appleRightEye.json`: Eye bounding box coordinates `X`, `Y`, `W`, `H` and validity flag `IsValid` (`docs/data/DATASET_STRUCTURE.md`, lines 64–69).
     - `faceGrid.json`: 25×25 binary grid feature for face scale/position (`docs/data/DATASET_STRUCTURE.md`, lines 70–74).
     - `info.json`: Session metadata with `TotalFrames`, `NumFaceDetections`, `NumEyeDetections`, `Dataset` split partition (`"train"`, `"val"`, `"test"`), and `DeviceName` (`docs/data/DATASET_STRUCTURE.md`, lines 75–82).
     - `motion.json`: Device IMU motion stream (pitch, roll, yaw, acceleration) (`docs/data/DATASET_STRUCTURE.md`, line 23).
3. **Detection Rates and Provenance**:
   - Provenance: MIT GazeCapture (*"Eye Tracking for Everyone"*, Krafka et al., CVPR 2016) released under the **MIT License** (commercial usability permitted) (`docs/data/DATASET_LICENSE_AND_PROVENANCE.md`, lines 11–26).
   - Overall Face Detection Rate: 94.06% (`docs/data/DATA_QUALITY_REPORT.md`, line 22).
   - Overall Eye Detection Rate: 68.37% (the ~31.6% gap represents natural blinks, occlusions, and extreme gaze angles) (`docs/data/DATA_QUALITY_REPORT.md`, lines 23–30).

### 1.2 Status of ML Problem Definition & Existing ML Codebase
1. **`docs/ml/ML_PROBLEM_DEFINITION.md` Status**:
   - Verified via `find_by_name` and `grep_search`: The file `docs/ml/ML_PROBLEM_DEFINITION.md` does **NOT** exist in the repository.
   - Files existing in `docs/ml/`: `DATA_CARD_TEMPLATE.md`, `EXPERIMENT_CARD_TEMPLATE.md`, `METRICS_POLICY.md`, `ML_READINESS_SCORECARD.md`, `REPOSITORY_AUDIT_TEMPLATE.md`, `ROADMAP.md`.
   - Therefore, `docs/ml/ML_PROBLEM_DEFINITION.md` is planned and must be authored in subsequent execution stages.
2. **Existing ML Modules in `backend/eyenav/`**:
   - `backend/eyenav/vision/landmarks.py`: Wraps MediaPipe FaceLandmarker Tasks API (`face_landmarker.task`) to extract 478 3D landmarks (including iris points #468 and #473), computes Eye Aspect Ratio (EAR) for blink detection, and computes 3D head pose via OpenCV `cv2.RQDecomp3x3`.
   - `backend/eyenav/vision/gaze.py`: Implements appearance-based gaze estimation using L2CS-Net with MobileNetV3-Large backbone (Abdelrahman et al., 2023). Uses binned classification (90 bins for pitch and yaw over ±45°) converted to continuous angles via softmax expectation, and normalized Shannon entropy as confidence scoring.
   - `backend/eyenav/cursor/mapping.py`: `GazeScreenMapper` maps 6D raw gaze features `[left_iris_x, left_iris_y, right_iris_x, right_iris_y, head_yaw, head_pitch]` to screen coordinates `(screen_x, screen_y)`. Uses degree-2 polynomial / linear ridge regression (`_poly_features`) with online recursive least squares rank-1 updates on confirmed blink clicks.
   - `backend/eyenav/intent.py`: `IntentEngine` implements a Tiny Temporal Transformer for navigation intent classification across 13 classes over a 1.5-second sliding window (45 frames × 32 feature dimensions) with attention weights exported for interpretability.
   - `backend/eyenav/models/`: Contains pre-trained serialized artifacts `intent_classifier.pkl` and `spatial_mapper.pkl`.
   - `scripts/calibrate_ml.py`: Interactive Tkinter tool collecting 50 user fixation points into `data/calibration_<timestamp>.csv`.
   - `scripts/train_calibration_model.py`: Fits a `RandomForestRegressor(n_estimators=150, max_depth=20)` on calibration CSV data and saves `backend/eyenav/models/spatial_mapper.pkl`.
   - `scripts/audit_dataset.py`: Standalone metadata-only dataset auditor with bounded memory and streaming CSV/TSV/JSONL validation.

---

## 2. Logic Chain

### 2.1 From Safe Archive Invariants to Pipeline Extraction Strategy
- **Premise 1**: `archive.zip` is 20.13 GB compressed and contains 351,005 entries (348,643 `.jpg` frames, 2,362 `.json` metadata files).
- **Premise 2**: Uncompressing 348,643 `.jpg` images to disk violates the zero-waste and storage integrity guidelines, risks inode exhaustion, and risks file locking on Windows. Furthermore, `ORIGINAL_REQUEST.md` (R2/Acceptance Criteria) requires: *"Keep the original `archive.zip` intact... verify data integrity without modifying `archive.zip`."*
- **Premise 3**: Gaze prediction models and calibration algorithms require tabular ground truth (screen target coordinates, camera coordinates, face/eye bounding boxes, validity flags) and feature vectors. All of this tabular data resides solely within the 2,362 `.json` files (totaling only 1.761 GB uncompressed).
- **Deduction**: The dataset pipeline must **stream or extract ONLY metadata `.json` files** directly from `archive.zip` in-memory (or cache extracted JSONs into `datasets/inav_gaze/interim/metadata/`) to construct deterministic manifests (`.csv` / `.jsonl`). Individual image frames should be streamed directly from `archive.zip` on demand during training via a custom PyTorch/TensorFlow dataset class using `zipfile.ZipFile.open()`, leaving `archive.zip` strictly unmodified on disk.

### 2.2 From Temporal Auto-Correlation to Participant-Group Partitioning
- **Premise 1**: GazeCapture sessions consist of continuous video capture at ~30 FPS tracking moving dots.
- **Premise 2**: Consecutive video frames from the same subject share virtually identical eye anatomy, iris texture, lighting, skin tone, camera calibration, and room background (`docs/data/DATA_QUALITY_REPORT.md`, lines 38–41).
- **Premise 3**: Standard random splitting (`train_test_split(shuffle=True)`) distributes adjacent frames of the same person across both train and test sets, causing massive data leakage. The model memorizes user-specific eye features rather than general gaze mechanics, producing artificially inflated metrics that collapse when evaluated on new participants.
- **Deduction**: The dataset pipeline **must strictly group all splits by participant (`subject_id`)**. The official GazeCapture partitions stored in `info.json` must be preserved:
  - `train`: 230 subjects (289,591 frames, 82.9%)
  - `val`: 7 subjects (13,340 frames, 3.8%)
  - `test`: 26 subjects (46,438 frames, 13.3%)
  The test partition must remain sealed until candidate evaluation.

### 2.3 From Task Structure to ML Problem Definition Formulation
- **Premise 1**: IntuiGaze requires real-time screen cursor positioning from webcams on CPU hardware (sub-10ms latency).
- **Premise 2**: The ground truth in `archive.zip` provides both 2D screen coordinates (`XPts`, `YPts` in points) and 3D camera coordinates (`XCam`, `YCam` in cm) alongside face/eye bounding boxes.
- **Premise 3**: Screen dimensions vary across devices (e.g. 568×320 for iPhone 5 vs 1024×768 for iPad) and orientations (portrait vs landscape).
- **Deduction**: The primary prediction task in `docs/ml/ML_PROBLEM_DEFINITION.md` must be formulated as **Screen Coordinate Regression**:
  $$f(X) \to (\hat{x}_{\text{norm}}, \hat{y}_{\text{norm}}) \in [0, 1]^2$$
  where $X$ comprises either extracted facial/iris landmarks (geometric branch) or normalized face/eye image crops (appearance branch). Target pixel coordinates are obtained by un-normalizing against target device resolution: $(\hat{x}_{\text{px}}, \hat{y}_{\text{px}}) = (\hat{x}_{\text{norm}} \cdot W_{\text{screen}}, \hat{y}_{\text{norm}} \cdot H_{\text{screen}})$.

### 2.4 From Evaluation Policy to Baseline & Evaluation Criteria
- **Premise 1**: `METRICS_POLICY.md` forbids conflating multiple tasks into a single composite metric and requires reporting error distributions, tail errors, and operational limits.
- **Premise 2**: Outlier saccades and head turns create long-tailed error distributions in gaze tracking.
- **Deduction**:
  - Evaluation of screen regression models cannot rely solely on Mean Absolute Error (MAE).
  - The evaluation harness must compute:
    1. **MAE (pixels)** per axis ($x$ and $y$).
    2. **Euclidean Error (pixels)**: Mean, **Median (P50)**, **P90**, and **P95** tail error.
    3. **Normalized Diagonal Error**: Euclidean error divided by screen diagonal $\sqrt{W^2 + H^2}$ to normalize across iPhone vs iPad screens.
    4. **Hit Rate Tolerance**: Fraction of predictions within predefined radii: Hit@25px, Hit@50px, Hit@100px.
    5. **Baseline Hierarchy**:
       - *Baseline 0 (Trivial/Dummy)*: Constant screen center prediction $(\frac{W}{2}, \frac{H}{2})$.
       - *Baseline 1 (Heuristic / Polynomial)*: 2nd-degree polynomial ridge regression (`backend/eyenav/cursor/mapping.py`).
       - *Baseline 2 (Classical ML)*: Random Forest Regressor on geometric features (`scripts/train_calibration_model.py`).
       - *Baseline 3 (Deep Appearance)*: L2CS-Net MobileNetV3 appearance-based CNN.

---

## 3. Caveats

1. **Unopened Binary Archive**: While forensic reports (`docs/data/DATASET_CARD.md`, `DATASET_STRUCTURE.md`) comprehensively document the 351,005 entries, MD5/SHA-256 hashes, subject counts, and JSON schemas, direct in-memory inspection of `archive.zip` via python was bypassed during this turn due to Windows process sandboxing constraints and lack of unsandboxed permissions. The findings rely on the forensic audit files generated on October 29, 2026.
2. **Desktop vs Mobile Geometry**: `archive.zip` is derived from MIT GazeCapture, which was recorded on Apple iPhones and iPads held in hand or placed on stands. IntuiGaze targets desktop/laptop navigation with a webcam positioned above or below a desktop monitor. Cross-domain transfer (mobile front-camera $\to$ desktop webcam) requires personal calibration adaptation (as implemented in `GazeScreenMapper` and `scripts/calibrate_ml.py`).
3. **Absence of `ML_PROBLEM_DEFINITION.md`**: `docs/ml/ML_PROBLEM_DEFINITION.md` has not yet been authored. This report defines its complete requirements and structure, which will be implemented in subsequent execution steps.

---

## 4. Conclusion

1. **`archive.zip` Inventory & Extraction Strategy**:
   - Contains 263 subjects, 348,643 frames (`.jpg`), and 2,362 annotation `.json` files from MIT GazeCapture (20.13 GB compressed, 21.39 GB uncompressed).
   - Under no circumstances should the entire archive be unzipped to disk.
   - The data pipeline must safely stream metadata `.json` files in-memory to generate structured manifests (`archive_manifest.csv`, `train_manifest.csv`, `val_manifest.csv`, `test_manifest.csv`), and stream frame images dynamically during model training.
2. **ML Problem Definition Status**:
   - `docs/ml/ML_PROBLEM_DEFINITION.md` does not yet exist and is the primary missing architectural document needed before training.
   - The primary task must be formally specified as **Normalized Screen Coordinate Regression** $(\hat{x}, \hat{y}) \in [0, 1]^2$, with secondary tasks covering Gaze Direction Regression (angular error) and Navigation Intent Classification (13 classes).
3. **Dataset Pipeline Specifications**:
   - **Participant Boundaries**: Zero subject overlap across train (230 subjects), val (7 subjects), and test (26 subjects) splits.
   - **Filtering Rules**: Discard or flag frames where `appleFace.IsValid == 0` or `appleLeftEye.IsValid == 0` or `appleRightEye.IsValid == 0` (~31.6% of frames have eye occlusions or blinks).
   - **Schema Contract**: Manifests must enforce explicit types, screen resolution dimensions, orientation flags, normalized coordinates, and archive relative paths.
4. **Baseline Models & Evaluation Gates**:
   - Evaluation harness must report MAE px, Median/P90/P95 Euclidean error, normalized screen diagonal error, and Hit@25/50/100px.
   - Baselines must follow the hierarchy: Dummy Center $\to$ Polynomial Ridge $\to$ Random Forest $\to$ L2CS-Net CNN.
   - Release requires passing all hard safety gates: no live desktop control in automated tests, emergency stop functional, and fail-closed click inhibition under low confidence.

---

## 5. Verification Method

### 5.1 Independent Document & File Verification
To independently verify the observations made in this report, inspect the following files:
1. Check missing `ML_PROBLEM_DEFINITION.md`:
   - Inspect directory: `docs/ml/`
   - Notice absence of `docs/ml/ML_PROBLEM_DEFINITION.md`.
2. Inspect dataset forensic metadata:
   - File: `docs/data/DATASET_CARD.md` (lines 19–75)
   - File: `docs/data/DATASET_STRUCTURE.md` (lines 9–83)
   - File: `docs/data/DATA_QUALITY_REPORT.md` (lines 9–45)
   - File: `docs/data/DATASET_LICENSE_AND_PROVENANCE.md` (lines 11–26)
3. Inspect existing ML modules and tests:
   - File: `backend/eyenav/cursor/mapping.py` (lines 50–135)
   - File: `backend/eyenav/vision/gaze.py` (lines 83–105)
   - File: `backend/eyenav/intent.py` (lines 52–110)
   - File: `scripts/train_calibration_model.py` (lines 12–64)
   - File: `scripts/audit_dataset.py` (lines 96–250)
   - File: `tests/test_audit_dataset_script.py` (lines 22–48)
   - File: `tests/test_safety_filter.py` (lines 75–225)

### 5.2 Verification Commands
When test execution is enabled in a suitable Python environment, run the following verification commands from the project root:
```bash
# 1. Run dataset audit smoke test
pytest tests/test_audit_dataset_script.py -v

# 2. Run safety filter tests (hard safety gates)
pytest tests/test_safety_filter.py -v

# 3. Run intent engine tests
pytest tests/test_intent_engine.py -v

# 4. Verify manifest validation using scripts/audit_dataset.py on sample data
python scripts/audit_dataset.py --root tests/ --format auto
```

### 5.3 Invalidation Conditions
This survey and its conclusions will be invalidated if:
1. `archive.zip` is found to be corrupted, truncated, or contains non-GazeCapture data.
2. The user or project owner declares a different primary prediction task (e.g. 3D eyeball sphere orientation rather than 2D screen coordinate regression).
3. The license of `archive.zip` is modified or restricted from commercial use.
