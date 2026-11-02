## 2026-10-29T17:56:11Z
You are explorer_m3_2, an exploration agent for Milestone 3 (ML Problem Definition Specification).
Your working directory is: c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_2\

MANDATORY FIRST STEP: Read the following files before starting:
- c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\ORIGINAL_REQUEST.md
- c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\orchestrator\PROJECT.md
- c:\Users\Voriganti\Downloads\INAV\AGENTS.md
- c:\Users\Voriganti\Downloads\INAV\.agents\skills\gaze-model-evaluation\SKILL.md
- c:\Users\Voriganti\Downloads\INAV\.agents\skills\cursor-safety-review\SKILL.md
- c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_survey_3\handoff.md
- c:\Users\Voriganti\Downloads\INAV\backend\eyenav\safety.py
- c:\Users\Voriganti\Downloads\INAV\backend\eyenav\cursor\controller.py

Objective:
Formulate the comprehensive evaluation metrics, error distribution reporting, statistical significance criteria, and operational failure definitions for IntuiGaze's ML prediction task, strictly complying with AGENTS.md requirements (no single headline number, full error distributions, reporting operational failure rates).

Key topics to specify in detail:
1. Regression Evaluation Metrics:
   - Primary metric: Euclidean Distance Error on Screen (in pixels at reference resolution, and in normalized diagonal units).
   - Component MAE: MAE_x and MAE_y in pixels and normalized coordinates.
   - Robust Distributional Statistics: Median (P50), Mean, P90, P95, and Maximum error.
   - Target Hit Rates: Hit@25px, Hit@50px, Hit@100px (percentage of predictions within target button radii).
   - Angular Gaze Error (degrees): conversion between screen error, viewing distance D, and visual angle.
2. Classification & Event Detection Metrics (for intent & blinks):
   - Precision, Recall, F1-score per intent class.
   - Confusion matrix analysis.
   - Temporal event alignment (latency to detect dwell, false blink trigger rate).
3. Operational Failure Modes & Safety Criteria:
   - Gaze tracking loss / low confidence detection rate.
   - Maximum cursor jump distance threshold (prevent abrupt jumps).
   - Latency budget: end-to-end inference budget <= 20ms per frame to maintain >= 30 FPS.
   - Stale frame handling and confidence gating thresholds.
   - Emergency stop / escape gesture verification.

Deliverables:
- Write full analysis and recommendations to c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_2\analysis.md
- Write handoff report to c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_2\handoff.md
- Send completion message to orchestrator via send_message with your handoff summary and path.
