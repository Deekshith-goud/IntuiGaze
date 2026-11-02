# Gaze ML metrics and evaluation rules

## Choose the task before choosing metrics

1. **Screen-coordinate mapping:** continuous `x,y` targets; treat as regression.
2. **Gaze direction:** continuous 3D vector or yaw/pitch; evaluate angular error only after confirming coordinate frame and units.
3. **Blink/dwell/intent:** binary or multiclass classification and/or event detection.
4. **Cursor control:** end-to-end closed-loop system evaluation; model metrics alone are insufficient.

## Screen-coordinate regression metrics

Report at minimum: mean absolute error (MAE) in pixels, root mean squared error (RMSE) in pixels, median Euclidean gaze error, 90th/95th percentile Euclidean error, and target-hit rate within predeclared pixel radii. If screen sizes differ, additionally normalise error by diagonal or report per-resolution groups. Describe the coordinate origin, scaling/DPI handling, screen dimensions, calibration procedure, and whether metrics are per-frame or per-target trial.

Use error distribution and tail metrics: RMSE or mean alone can conceal rare large cursor jumps. Report per-participant and per-session values where allowed, plus aggregate summaries. Do not call a pixel-error metric “accuracy” without defining a tolerance-based success event.

## Gaze-direction metrics

If valid direction labels are available, report mean/median angular error in degrees and a high percentile. Verify that predicted and target vectors use the same coordinate system, are normalised appropriately, and that angle calculation is numerically stable. Do not convert screen-pixel error into degrees without a defensible geometric calibration.

## Blink/dwell/intent classification and events

Report confusion matrix, class support, per-class precision/recall/F1, macro-F1, balanced accuracy, and PR-AUC for rare positive events when probabilities are available. ROC-AUC may be reported but cannot replace precision/recall. Include false activations per minute or per hour, missed intended activations, and trigger latency. Define the event-matching tolerance and deduplication window.

## End-to-end cursor performance

Measure target acquisition/success rate, time-to-target, overshoot/jump rate, unintended click rate, missed click rate, stale-frame rate, dropped-frame rate, end-to-end latency, and sustained FPS on declared hardware. Include low-light, glasses/reflections, head movement, camera movement, partial-face loss, and session drift where applicable.

## Comparison discipline

- Compare candidates on exactly the same frozen partitions and preprocessing.
- Always include the existing implementation as a baseline where it can be run reproducibly.
- Report mean and spread across folds/runs or participant groups; include sample/group counts.
- Do not average incompatible units or let a single composite score conceal a safety-critical regression.
- Select primary metrics and acceptance thresholds before the final comparison. If product requirements are unknown, establish the baseline first and obtain a documented decision; do not invent universal pixel or false-click thresholds.
- Keep final-test results sealed until model selection and threshold selection are finished.
