# IntuiGaze ML evaluation policy

## 1. The target determines the metric

IntuiGaze contains several different problems. Do not mix them into one “accuracy” value.

| Component | Problem type | Primary metrics | Operational metrics |
|---|---|---|---|
| Gaze-to-screen `(x, y)` | Regression | MAE px, RMSE px, median and P90/P95 Euclidean error, hit rate at fixed pixel tolerance | Jitter, jump/overshoot rate, end-to-end latency, target acquisition time |
| Gaze direction vector / yaw-pitch | Regression | Median/mean and P90/P95 angular error in degrees, only with verified units/frame | Prediction latency, invalid-vector rate |
| Blink/dwell/gesture intent | Classification / event detection | Confusion matrix, per-class precision/recall/F1, macro-F1, balanced accuracy, PR-AUC when probability scores are available | False triggers/minute or hour, missed triggers, trigger latency |
| Face/iris/landmark visibility, if classified | Detection/classification | Precision, recall, F1, PR-AUC; localisation error if coordinates are predicted | No-face recovery time, failure rate under lighting/occlusion |
| Whole cursor-control loop | System evaluation | Success rate at a predefined target task and participant/session summaries | Time-to-target, unintended click rate, misses, overshoot, dropped frames, FPS, latency, safety-stop reliability |

## 2. Regression definitions

For prediction `(x_hat, y_hat)` and ground truth `(x, y)`:

- Per-axis absolute error: `abs(x_hat - x)` and `abs(y_hat - y)` in screen pixels.
- Euclidean error: `sqrt((x_hat - x)^2 + (y_hat - y)^2)` in pixels.
- MAE: mean absolute coordinate error, reporting whether it averages both axes or uses Euclidean distance.
- RMSE: square root of mean squared error, with the exact target definition disclosed.
- Hit rate at radius `r`: proportion of evaluated points/trials for which Euclidean error is `<= r`. Choose `r` before final evaluation and explain the UI/task basis for it.
- Percentiles: median, P90 and P95 Euclidean error capture typical and tail behavior. Report counts and aggregation unit.

If screen resolutions differ, provide per-resolution metrics and optionally normalized distance divided by the screen diagonal. Do not combine normalised and pixel units in one number.

## 3. Classification definitions and class imbalance

- Precision answers “of the predicted events, how many were correct?”
- Recall answers “of the true events, how many were detected?”
- F1 summarises precision/recall at a selected operating threshold.
- Macro-F1 averages per-class F1 equally; balanced accuracy averages recall across classes.
- PR-AUC is useful when positive events are uncommon, but the thresholded confusion matrix and actual event rate are still needed.
- ROC-AUC can be included, but should not replace precision/recall or false-trigger-rate reporting for sparse blink/dwell events.
- Always include class support and the threshold used. Do not interpret a high accuracy score as good performance when the majority class dominates.

For event detection, define the matching window, debounce/de-duplication interval, minimum dwell duration and whether multiple predictions in one labelled event count as one or many false triggers. Freeze these definitions before comparison.

## 4. Split and leakage requirements

- Define the deployment claim first: new frames from known people, new sessions from known people, or entirely unseen people/devices.
- For unseen-person performance, keep all samples from a participant in only one partition. Use session/device groups if those are the required generalisation unit.
- Keep adjacent frames/clips and derivatives of the same source together when they are highly correlated.
- Fit all data-dependent transforms only on training data. Use validation for model/threshold selection and final test only after the selection is frozen.
- Report group counts as well as row/frame counts. Large frame counts do not substitute for having diverse independent participants.

## 5. Runtime/safety scorecard

At minimum capture:
- Throughput: mean/median FPS, p95 frame-to-prediction latency, end-to-end latency.
- Stability: dropped/stale frame rate, prediction jump/overshoot rate, invalid prediction rate, time to recover from face/landmark loss.
- Interaction: target acquisition success, time to acquire, false click/activation rate, missed intent rate.
- Safety: explicit opt-in verified; emergency stop verified; low-confidence click blocked; camera/model failure produces no unintended actuation.

Safety fields are hard gates, not weighted trade-offs.

## 6. Threshold selection and release

No universal pixel tolerance or false-click target is assumed by this pack. After the repository audit and stakeholder requirements, write the threshold, metric, aggregation unit and rationale into `configs/ml/evaluation.yaml` before final candidate evaluation. Thresholds must be selected on training/validation data, never tuned against final test results.

A release result must state:
- baseline and candidate with identical split and evaluation code;
- sample, participant and session counts;
- mean/median/tail metrics and group variation;
- classification/event threshold and confusion matrix where applicable;
- latency, FPS, memory, model size and target hardware;
- known weak subgroups and conditions;
- data/model version and run provenance;
- safety-gate results and limitations.

## 7. Avoid a misleading single model score

Do not rank candidates by averaging pixels, F1, latency and false clicks into one unqualified number. Use a table plus hard constraints. A composite score is allowed only as a secondary, predeclared decision aid with published normalization and weights; it cannot override a failed safety gate or a meaningful regression in any critical metric.
