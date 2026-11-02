## 2026-10-29T17:55:58Z
You are explorer_m3_1, an exploration agent for Milestone 3 (ML Problem Definition Specification).
Your working directory is: c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_1\

MANDATORY FIRST STEP: Read the following files before starting:
- c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\ORIGINAL_REQUEST.md
- c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\orchestrator\PROJECT.md
- c:\Users\Voriganti\Downloads\INAV\AGENTS.md
- c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_survey_3\handoff.md
- c:\Users\Voriganti\Downloads\INAV\backend\eyenav\cursor\mapping.py
- c:\Users\Voriganti\Downloads\INAV\backend\eyenav\vision\gaze.py
- c:\Users\Voriganti\Downloads\INAV\backend\eyenav\intent.py

Objective:
Formulate the rigorous mathematical and technical specifications for the primary and secondary ML tasks for IntuiGaze, to be incorporated into docs/ml/ML_PROBLEM_DEFINITION.md.

Key topics to specify in detail:
1. Primary Prediction Task:
   - Formal mathematical definition of Normalized Screen Coordinate Regression: f(X) -> (x_norm, y_norm) in [0, 1]^2.
   - Screen coordinate mapping: conversion between device screen points (x_pts, y_pts), device orientation (orientations 1-4 from MIT GazeCapture), screen dimensions (screen_w, screen_h), and normalized coordinates.
   - Target bounding and clipping vs unbounded regression with post-processing guards.
2. Loss Functions:
   - Mean Squared Error (MSE) loss.
   - Huber / Smooth L1 loss (robustness to outlier blinks/head jerks).
   - Adaptive Wing Loss / Pinball loss for gaze regression.
   - Multi-task loss formulation if combining coordinate regression with gaze direction or intent.
3. Secondary Tasks:
   - Gaze direction angular regression: 3D gaze vector d in S^2 or pitch/yaw angles (theta, phi) in radians.
   - 13-class temporal intent classification (fixation, saccade, pursuit, dwell, etc. matching intent.py).
4. Feature Input Space:
   - Multimodal inputs: left eye crop I_L, right eye crop I_R, face crop I_F, binary face grid G (25x25), facial landmark coordinates L in R^(478x3).

Deliverables:
- Write full analysis and recommendations to c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_1\analysis.md
- Write handoff report to c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_1\handoff.md
- Send completion message to orchestrator via send_message with your handoff summary and path.
