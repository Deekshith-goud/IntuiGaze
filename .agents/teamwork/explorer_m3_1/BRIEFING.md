# BRIEFING — 2026-10-29T18:05:00Z

## Mission
Formulate rigorous mathematical and technical specifications for IntuiGaze primary and secondary ML tasks for docs/ml/ML_PROBLEM_DEFINITION.md.

## 🔒 My Identity
- Archetype: explorer
- Roles: investigation, synthesis
- Working directory: c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_1
- Original parent: 49d5375b-5d7a-4c9a-8432-b9df2f718d02
- Milestone: Milestone 3 (ML Problem Definition Specification)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Ground formulations in codebase (backend/eyenav/cursor/mapping.py, gaze.py, intent.py) and verified datasets (MIT GazeCapture, etc.)
- Comply with AGENTS.md, PROJECT.md, cursor safety rules

## Current Parent
- Conversation ID: 49d5375b-5d7a-4c9a-8432-b9df2f718d02
- Updated: 2026-10-29T18:05:00Z

## Investigation State
- **Explored paths**:
  - `backend/eyenav/cursor/mapping.py`: Checked polynomial mapping, 6D input feature vector, online rank-1 RLS adaptation, clamping logic.
  - `backend/eyenav/vision/gaze.py`: Checked L2CS-Net MobileNetV3-Large binned classification (90 bins, ±45°), softmax expectation, normalized Shannon entropy confidence.
  - `backend/eyenav/intent.py`: Checked 13-class intent catalog (`idle`, `reading`, `selecting`, etc.), sliding window ($45 \times 32$), attention weights, and suggested commands.
  - `backend/eyenav/safety.py`: Checked 6-layer safety filter, confidence gate (<0.70), anti-pattern detector, emergency stop.
  - `backend/eyenav/vision/landmarks.py`: Checked MediaPipe FaceLandmarker 478 points, iris centers (468, 473), head pose decomposition.
  - `docs/data/DATASET_STRUCTURE.md` & `DATASET_CARD.md`: Checked GazeCapture JSON schemas (`dotInfo.json`, `screen.json`, `appleFace.json`, `faceGrid.json`).
  - `docs/ml/METRICS_POLICY.md`: Checked required evaluation criteria (MAE px, P50/P90/P95 Euclidean, Hit@25/50/100px, macro-F1).
- **Key findings**:
  - Primary regression task must be Normalized Screen Coordinate Regression $f(X) \to (\hat{x}, \hat{y}) \in [0, 1]^2$.
  - Unbounded linear regression with a two-tier safety guard (anomaly track loss detector + deterministic clamp) is superior to Sigmoid output because Sigmoid introduces vanishing gradients at display edges.
  - Huber loss ($\delta=0.02$) and Adaptive Wing loss ($\omega=0.05, \epsilon=0.01$) address outlier blinks and micro-fixation precision.
  - Secondary tasks are 3D gaze direction ($\mathbb{S}^2$) and 13-class temporal intent ($\Delta^{12}$) with Focal Loss.
  - Multimodal inputs include left/right eye crops ($128\times 128$), face crop ($224\times 224$), binary face grid ($25\times 25$), and 478 landmarks ($478\times 3$).
- **Unexplored areas**: None for Milestone 3 specification scope.

## Key Decisions Made
- Authored comprehensive mathematical and technical specification in `analysis.md`.
- Specified exact coordinate mapping equations for all 4 GazeCapture orientations.
- Defined gradient formulations and trade-offs for MSE, Huber, Wing, Pinball, and Multi-task losses.

## Artifact Index
- DISPATCH.md — Incoming dispatch message
- BRIEFING.md — Persistent working memory index
- progress.md — Liveness heartbeat
- analysis.md — Full mathematical and technical specification
- handoff.md — 5-component handoff report
