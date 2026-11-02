## 2026-10-29T18:02:48Z
You are worker_m3, a worker agent implementing Milestone 3: ML Problem Definition Specification for IntuiGaze.
Your working directory is: c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\worker_m3\

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MANDATORY FIRST STEP: Read the following files before starting:
- c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\ORIGINAL_REQUEST.md
- c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\orchestrator\PROJECT.md
- c:\Users\Voriganti\Downloads\INAV\AGENTS.md
- c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_1\analysis.md
- c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_1\handoff.md
- c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_2\analysis.md
- c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_2\handoff.md
- c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_3\analysis.md
- c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_3\handoff.md
- c:\Users\Voriganti\Downloads\INAV\docs\ml\METRICS_POLICY.md
- c:\Users\Voriganti\Downloads\INAV\docs\business\ETHICS.md

WRITE OWNERSHIP:
You have exclusive write ownership of:
`c:\Users\Voriganti\Downloads\INAV\docs\ml\ML_PROBLEM_DEFINITION.md`
and your own directory: `c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\worker_m3\`
DO NOT modify any other files in the repository.
PRESERVE INVARIANTS:
- backend/eyenav/cursor/controller.py MUST remain untouched.
- docs/business/ETHICS.md MUST remain untouched.
- archive.zip MUST remain intact at repository root.
- face_landmarker.task MUST remain intact at repository root.

TASK DESCRIPTION:
Author the comprehensive, publication-grade specification document `docs/ml/ML_PROBLEM_DEFINITION.md` unifying the synthesized findings from Explorers M3.1, M3.2, and M3.3.

Document Structure Requirements for `docs/ml/ML_PROBLEM_DEFINITION.md`:
1. Document Header & Metadata (Title, Status, Version, Target Audience, Applicable Contracts: AGENTS.md, METRICS_POLICY.md, ETHICS.md).
2. Executive Summary & Problem Scope.
3. Primary Task: Normalized Screen Coordinate Regression:
   - Mathematical formulation: f(X) -> (x_norm, y_norm) in [0, 1]^2.
   - Screen coordinate geometry and affine transformations across all 4 MIT GazeCapture device orientations.
   - Output layer architecture: unbounded linear logits + two-stage guard (anomaly track loss detector + [0, 1] clipping), explaining why Sigmoid is rejected (edge gradient vanishing).
   - Loss function hierarchy: Huber/Smooth L1 (delta=0.02) and Adaptive Wing Loss (omega=0.05, epsilon=0.01) vs MSE; Pinball loss for uncertainty estimation.
4. Secondary Prediction Tasks:
   - Task S1: 3D Gaze Direction Angular Regression (pitch/yaw spherical angles in radians, L2CS-Net 90-bin soft-argmax expectation, Shannon entropy confidence).
   - Task S2: 13-Class Temporal Intent Recognition matching `backend/eyenav/intent.py` INTENT_CLASSES over 45x32 sliding buffers, trained via Multi-Class Focal Loss.
5. Multimodal Feature Input Space:
   - 5 input modalities: left eye crop (128x128), right eye crop (128x128, flipped for Siamese sharing), face crop (224x224), binary face grid (25x25), MediaPipe 478 landmarks.
   - Real-time CPU latency budget: <= 6ms model inference, <= 10ms total per-frame pipeline (sustaining >= 30 FPS, targeting 60 FPS).
6. Comprehensive Evaluation Metrics & Error Distribution Policy:
   - Continuous metrics: Euclidean distance error in pixels and normalized diagonal, component MAE_x and MAE_y, full distribution percentiles (P50 Median, Mean, P90, P95, Max).
   - Predeclared target hit rates: Hit@25px, Hit@50px (aligned with _FIXATION_DEADZONE_PX = 45.0), Hit@100px.
   - Angular conversion formula (viewing distance D=60cm, 1080p reference display).
   - Operational safety criteria: tracking loss fail-closed, anomalous jump suppression (>250 px/frame clamp), stale frame handling (>50ms discard).
   - Statistical testing: Wilcoxon signed-rank test across 26 test subjects, 10,000 bootstrap CIs, slice-based evaluations (orientation, device, eccentricity).
7. Baseline Model Progression Hierarchy:
   - Level 0: Trivial Center Dummy baseline (0.5, 0.5).
   - Level 1: Degree-2 Polynomial Ridge Regression (GazeScreenMapper with closed-form lambda=1e-4 and online rank-1 adaptation).
   - Level 2: Random Forest / GBDT Regressor on engineered landmark features.
   - Level 3: Deep Appearance CNN (L2CS-Net / iTracker).
8. Dataset Partitioning, Archive Invariants & Leakage Prevention:
   - Native MIT GazeCapture split: 230 train subjects (82.9%), 7 validation subjects (3.8%), 26 test subjects (13.3%). Zero participant overlap.
   - Sealed test set rules.
   - archive.zip handling: in-memory streaming extraction of 2,362 JSON metadata files; zero decompression of 20GB images to disk.
   - 4-point quality filtering criteria.
9. Safety, Privacy & Ethical Compliance:
   - 100% on-device local execution; zero transmission of biometric frames.
   - Ephemeral in-memory frame lifecycle; default-dormant opt-in actuation; physical mouse override priority (15px threshold).
   - 6-layer safety filter with fail-closed default.
10. Model Promotion & Verification Gate (8-point binary checklist).
