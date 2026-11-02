## 2026-10-29T17:56:23Z
You are explorer_m3_3, an exploration agent for Milestone 3 (ML Problem Definition Specification).
Your working directory is: c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_3\

MANDATORY FIRST STEP: Read the following files before starting:
- c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\ORIGINAL_REQUEST.md
- c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\orchestrator\PROJECT.md
- c:\Users\Voriganti\Downloads\INAV\AGENTS.md
- c:\Users\Voriganti\Downloads\INAV\.agents\skills\experiment-management\SKILL.md
- c:\Users\Voriganti\Downloads\INAV\.agents\skills\dataset-auditing\SKILL.md
- c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_survey_3\handoff.md
- c:\Users\Voriganti\Downloads\INAV\docs\business\ETHICS.md

Objective:
Formulate the baseline model hierarchy, dataset partitioning invariants (leakage prevention), and privacy/safety compliance specifications for IntuiGaze, to be incorporated into docs/ml/ML_PROBLEM_DEFINITION.md.

Key topics to specify in detail:
1. Baseline Model Hierarchy:
   - Level 0: Trivial Center Dummy baseline (predicts constant screen center (0.5, 0.5) or empirical mean target). Establishes theoretical floor.
   - Level 1: Polynomial Ridge Regression / Linear Mapper (GazeScreenMapper using facial landmarks/pupil positions with polynomial feature expansion degree 2-3).
   - Level 2: Random Forest / Gradient Boosted Trees regressor on engineered landmark features and head pose vectors.
   - Level 3: Deep Neural Network / L2CS-Net / iTracker architecture (convolutional feature extractor on eye patches + face grid).
2. Dataset Partitioning & Leakage Prevention:
   - Strict subject-grouped split based on MIT GazeCapture native partitioning: 230 subjects (82.9%) train, 7 subjects (3.8%) val, 26 subjects (13.3%) test.
   - Zero participant overlap between train, val, and test to avoid cross-frame temporal data leakage.
   - Final test set sealing rules: test set is evaluated ONLY once model selection is frozen.
3. Data Pipeline & Archive Constraints:
   - archive.zip invariant: 20.13 GB compressed archive must remain intact; metadata JSONs extracted in-memory to build tabular manifests.
   - Quality filtering criteria: appleFace.IsValid == 1, eye validity flags, screen bounding box sanity.
4. Privacy, Safety & Ethical Invariants:
   - On-device inference by default; no transmission of raw video frames or biometric crops.
   - User opt-in for gaze control; independent physical escape failsafe; fail-safe confidence gating.

Deliverables:
- Write full analysis and recommendations to c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_3\analysis.md
- Write handoff report to c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_3\handoff.md
- Send completion message to orchestrator via send_message with your handoff summary and path.
