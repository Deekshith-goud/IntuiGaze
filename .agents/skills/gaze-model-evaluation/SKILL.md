---
name: gaze-model-evaluation
description: Evaluate gaze-to-screen regression, gaze direction, blink/dwell classifiers, and end-to-end cursor interaction with metrics matched to each task.
---

# Gaze model evaluation

1. Identify task and prediction unit before metric selection.
2. For screen `x,y` regression, report MAE/RMSE in pixels, median and high-percentile Euclidean error, and hit rate at predeclared pixel tolerances. Report groups/resolutions separately where justified.
3. For direction regression, report angular error in degrees only after verifying units and coordinate frame.
4. For blink/dwell/intent classification, report confusion matrix, per-class precision/recall/F1, macro-F1, balanced accuracy, class support, and PR-AUC when probability scores are valid. Also report false activations per minute/hour, missed events and trigger latency.
5. For interactive control, measure target acquisition, overshoots, unintended/missed clicks, latency, frame drops and sustained FPS on declared hardware.
6. Compare candidates on identical frozen splits and baseline preprocessing. Report uncertainty/spread and error slices.
7. Keep final test data sealed until model and thresholds are chosen. Do not make a single composite number the sole release decision.

## Output
A baseline/candidate table, metric definitions/units, group/sample counts, confidence/uncertainty approach, error analysis, operational limits and release recommendation.
