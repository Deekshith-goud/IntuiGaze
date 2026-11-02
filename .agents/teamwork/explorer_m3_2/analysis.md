# IntuiGaze ML Evaluation Metrics, Error Distributions, and Operational Safety Specification

**Document Path:** `c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m3_2\analysis.md`  
**Author:** `explorer_m3_2` (Milestone 3: ML Problem Definition Specification)  
**Parent Task:** Milestone 3 Subtask 2  
**Operating Contract:** `c:\Users\Voriganti\Downloads\INAV\AGENTS.md`  
**Applied Skills:** `gaze-model-evaluation`, `cursor-safety-review`, `test-quality`  
**Date:** 2026-10-29  

---

## 1. Executive Summary & Core Principles

IntuiGaze is an experimental gaze-controlled computer navigation system designed for hands-free desktop interaction and accessibility. Unlike passive eye-tracking research that only evaluates offline error averages, IntuiGaze couples gaze predictions directly to an operating system cursor and critical command triggers (`select`, `scroll`, `back`, `enter`, `delete`).

In strict compliance with **`AGENTS.md`** and **`docs/ml/METRICS_POLICY.md`**, this specification establishes the evaluation framework, error distribution metrics, statistical significance testing, and operational safety criteria for all machine learning models in IntuiGaze.

### 1.1 Non-Negotiable Evaluation Principles
1. **No Single Headline Number:** Ranking or releasing models based on a single composite "accuracy" or aggregate mean absolute error is strictly forbidden. A model with an impressive mean error can still cause violent cursor jumps or accidental clicks.
2. **Full Error Distribution Reporting:** All regression tasks must report the complete error distribution: Component MAE ($MAE_x, MAE_y$), Median ($P50$), Mean, 90th percentile ($P90$), 95th percentile ($P95$), Maximum error, and Target Hit Rates ($Hit@25\text{px}, Hit@50\text{px}, Hit@100\text{px}$).
3. **Operational Failure Rates as First-Class Metrics:** Low-confidence tracking loss rates, stale frame rates, unintended activation rates per minute/hour, and end-to-end latency are mandatory release criteria.
4. **Hard Safety Gates:** Safety mechanisms—such as the independent physical mouse override, 3-second eye-closure emergency stop, confidence gating, and fail-closed click inhibition—are non-negotiable binary gates. A failure in any safety invariant immediately blocks candidate release, regardless of numerical regression accuracy.
5. **Zero Data Leakage:** Evaluation must strictly preserve participant-grouped partitions (26 unseen subjects in the test set). Performance must be macro-averaged across subjects with bootstrap confidence intervals.

---

## 2. Regression Evaluation Metrics (Screen Coordinate Prediction)

The primary continuous task for IntuiGaze is predicting on-screen gaze coordinates from facial and eye features:
$$f(X) \to (\hat{x}_{\text{norm}}, \hat{y}_{\text{norm}}) \in [0, 1]^2$$
Un-normalized screen pixel coordinates on a display of resolution $(W_{\text{screen}}, H_{\text{screen}})$ are given by:
$$\hat{x}_{\text{px}} = \hat{x}_{\text{norm}} \cdot W_{\text{screen}}, \quad \hat{y}_{\text{px}} = \hat{y}_{\text{norm}} \cdot H_{\text{screen}}$$

Ground truth target coordinates are $(x_i, y_i)$ in pixels, or $(x_{\text{norm}, i}, y_{\text{norm}, i})$ in normalized space.

```
+--------------------------------------------------------------------------------------------------+
|                                    Continuous Gaze Regression                                    |
|                                                                                                  |
|   +-----------------------+   +-----------------------+   +----------------------------------+   |
|   |  Euclidean Distance   |   |     Component MAE     |   |    Target Hit Rates (Hit@R)      |   |
|   |  - Pixels at Ref Res  |   |  - MAE_x (Horizontal) |   |  - Hit@25px  (Fine UI Icons)     |   |
|   |  - Normalized Diag    |   |  - MAE_y (Vertical)   |   |  - Hit@50px  (Standard Buttons)  |   |
|   +-----------+-----------+   +-----------+-----------+   |  - Hit@100px (Coarse Cards/Keys) |   |
|               |                           |               +----------------+-----------------+   |
|               +---------------------------+--------------------------------+                     |
|                                           v                                                      |
|                       +----------------------------------------+                                 |
|                       |    Robust Distributional Statistics    |                                 |
|                       |    - Median (P50) [Typical Error]      |                                 |
|                       |    - Mean         [Traditional]        |                                 |
|                       |    - P90 / P95    [Tail Excursions]    |                                 |
|                       |    - Max Error    [Worst Glitch]       |                                 |
|                       +-------------------+--------------------+                                 |
|                                           |                                                      |
|                                           v                                                      |
|                       +----------------------------------------+                                 |
|                       |     Angular Gaze Error Conversion      |                                 |
|                       |     - Visual Angle (theta in deg)      |                                 |
|                       |     - At Viewing Distance D = 60 cm    |                                 |
|                       +----------------------------------------+                                 |
+--------------------------------------------------------------------------------------------------+
```

### 2.1 Primary Metric: Euclidean Distance Error
For each frame $i \in \{1, \dots, N\}$, the Euclidean distance error $e_i$ is defined as:
$$e_i = \sqrt{(\hat{x}_i - x_i)^2 + (\hat{y}_i - y_i)^2}$$

#### A. Screen Pixels at Reference Resolution
Screen resolutions vary across desktop and mobile displays. To provide consistent comparisons, pixel errors must be reported both at:
1. **Reference Standard Resolution (Full HD 1080p):** $W_{\text{ref}} = 1920\text{ px}, H_{\text{ref}} = 1080\text{ px}$ (standard 24-inch desktop display, $\sim 91.79\text{ PPI}$, pixel pitch $p = 0.2767\text{ mm}$).
2. **Native Device Resolution:** The actual resolution recorded in GazeCapture metadata (`screen.json`: $W, H$ in points) mapped to native physical pixels.

#### B. Normalized Diagonal Error ($e_{\text{diag}}$)
To evaluate model performance independent of screen size and aspect ratio, distance error is normalized by the screen diagonal length:
$$D_{\text{screen}} = \sqrt{W^2 + H^2}$$
$$e_{\text{diag}, i} = \frac{e_i}{D_{\text{screen}}} = \frac{\sqrt{(\hat{x}_i - x_i)^2 + (\hat{y}_i - y_i)^2}}{\sqrt{W^2 + H^2}}$$
In normalized coordinate space $[0, 1]^2$:
$$e_{\text{diag}, i} = \sqrt{(\hat{x}_{\text{norm}, i} - x_{\text{norm}, i})^2 \cdot \frac{W^2}{W^2 + H^2} + (\hat{y}_{\text{norm}, i} - y_{\text{norm}, i})^2 \cdot \frac{H^2}{W^2 + H^2}}$$
*Unit:* Percentage of screen diagonal ($\% D_{\text{diag}}$). A diagonal error of $0.05$ represents $5\%$ of the screen diagonal.

### 2.2 Component Mean Absolute Error ($MAE_x$ and $MAE_y$)
Human eye anatomy, oculomotor mechanics, and head pose introduce significant anisotropy between horizontal and vertical gaze estimation:
$$MAE_x = \frac{1}{N} \sum_{i=1}^N |\hat{x}_i - x_i|, \quad MAE_y = \frac{1}{N} \sum_{i=1}^N |\hat{y}_i - y_i|$$
- **Horizontal ($x$):** Driven primarily by medial/lateral rectus muscles and lateral head yaw. Has wider angular range ($\pm 35^\circ$), but suffers from ear-to-ear camera perspective skew.
- **Vertical ($y$):** Driven by superior/inferior rectus muscles and head pitch. Highly susceptible to upper eyelid droop (ptosis), eyelash shadows, and camera pitch tilt. Typically exhibits $15\%\text{--}35\%$ higher error than horizontal gaze.
- **Reporting Rule:** $MAE_x$ and $MAE_y$ must be reported separately in both pixels and normalized units ($MAE_{x,\text{norm}}, MAE_{y,\text{norm}}$).

### 2.3 Robust Distributional Statistics
Because gaze tracking data contains extreme outlier errors caused by blinks, saccadic overshoot, and momentary tracking dropouts, error distributions are heavily skewed (non-Gaussian, heavy-tailed).

Reporting requirements for screen error $e$:
1. **Median ($P50$):** The 50th percentile of Euclidean error. Represents the typical user experience and is unaffected by extreme momentary tracking spikes.
2. **Mean ($P_{\text{mean}}$):** The arithmetic mean $\bar{e} = \frac{1}{N}\sum e_i$. Useful for historical benchmarking, but sensitive to tail spikes.
3. **90th Percentile ($P90$):** The error threshold below which $90\%$ of predictions fall. Defines the operational boundary for reliable interaction.
4. **95th Percentile ($P95$):** The error threshold below which $95\%$ of predictions fall. Defines the tail risk boundary for erratic cursor excursions.
5. **Maximum Error ($e_{\max}$):** The single worst prediction error in the evaluation partition. Exposes catastrophic failure modes.
6. **Interquartile Range ($IQR = P75 - P25$):** Measures dispersion around the median without outlier distortion.

### 2.4 Target Hit Rates ($Hit@R$)
In graphical user interfaces, users interact with discrete interactive widgets (buttons, links, text fields). Under Fitts' Law, acquisition success depends on whether the cursor settles within the target's interactive bounding area.

We define the Target Hit Rate at radius $R$ pixels:
$$Hit@R = \frac{1}{N} \sum_{i=1}^N \mathbb{I}(e_i \le R) \times 100\%$$
where $\mathbb{I}(\cdot)$ is the indicator function.

#### Pre-declared Radii Standards (Referenced to 1080p FHD):
| Metric | Radius $R$ (px) | Equivalent Radius (mm at 92 PPI) | Target UI Analog / Task Rationale | Minimum Usability Threshold |
|---|---|---|---|---|
| **$Hit@25\text{px}$** | $25\text{ px}$ | $6.9\text{ mm}$ | Fine UI icons, radio buttons, window minimize/close controls ($24\text{--}32\text{ px}$) | $\ge 40\%$ (with fixation gravity) |
| **$Hit@50\text{px}$** | $50\text{ px}$ | $13.8\text{ mm}$ | Standard accessible touch/click targets, toolbar buttons, navigation icons ($48\text{--}64\text{ px}$) | $\ge 70\%$ |
| **$Hit@100\text{px}$** | $100\text{ px}$ | $27.7\text{ mm}$ | Coarse UI cards, on-screen accessibility keyboard keys, navigation tiles ($96\text{--}128\text{ px}$) | $\ge 90\%$ |

*Note:* In `backend/eyenav/cursor/controller.py`, the fixation gravity deadzone is set to `_FIXATION_DEADZONE_PX = 45.0`. When the user fixates near a target, predictions within $45\text{ px}$ are locked to the fixation anchor, directly converting $Hit@50\text{px}$ accuracy into stable target acquisition.

### 2.5 Angular Gaze Error (Degrees)
In computer vision and physiological eye tracking literature, gaze accuracy is universally measured in degrees of visual angle ($\theta^\circ$).

#### Conversion Formulation:
Let:
- $D$ = User viewing distance from the screen in centimeters (standard default $D = 60.0\text{ cm}$ for desktop displays).
- $d_{\text{cm}}$ = Physical metric distance on the screen surface between predicted point $(\hat{x}, \hat{y})$ and target point $(x, y)$:
  $$d_{\text{cm}} = e_{\text{px}} \times p_{\text{cm}} = e_{\text{px}} \times \frac{W_{\text{cm}}}{W_{\text{px}}}$$
  For a 24-inch 1080p monitor ($W_{\text{cm}} = 53.13\text{ cm}, W_{\text{px}} = 1920$), pixel pitch $p_{\text{cm}} \approx 0.02767\text{ cm/px}$.

The visual angle error $\theta_{\text{deg}}$ is computed by trigonometry:
$$\theta_{\text{deg}} = \arctan\left(\frac{d_{\text{cm}}}{D}\right) \times \frac{180^\circ}{\pi}$$
For small angles ($d_{\text{cm}} \ll D$), this is approximated by:
$$\theta_{\text{deg}} \approx \frac{d_{\text{cm}}}{D} \times \frac{180^\circ}{\pi} = \frac{e_{\text{px}} \cdot p_{\text{cm}}}{D} \times \frac{180^\circ}{\pi}$$

#### Equivalent Error Reference Table (at $D = 60\text{ cm}$, 24" 1080p):
| Visual Angle ($\theta^\circ$) | Screen Metric Error ($d_{\text{cm}}$) | Screen Pixel Error ($e_{\text{px}}$ at 1080p) | Normalized Diagonal ($\% D$) | Real-World Feasibility Context |
|---|---|---|---|---|
| **$0.5^\circ$** | $0.52\text{ cm}$ | $18.9\text{ px}$ | $0.86\%$ | Commercial infrared eye-tracker (Tobii Eye Tracker 5) |
| **$1.0^\circ$** | $1.05\text{ cm}$ | $37.8\text{ px}$ | $1.72\%$ | High-quality personalized 9-point calibrated webcam model |
| **$1.5^\circ$** | $1.57\text{ cm}$ | $56.8\text{ px}$ | $2.58\%$ | Target for calibrated IntuiGaze `GazeScreenMapper` polynomial |
| **$2.5^\circ$** | $2.62\text{ cm}$ | $94.7\text{ px}$ | $4.30\%$ | Uncalibrated SOTA deep webcam gaze (L2CS-Net / ETH-XGaze) |
| **$3.5^\circ$** | $3.67\text{ cm}$ | $132.6\text{ px}$ | $6.02\%$ | Generic baseline webcam model without personal calibration |
| **$5.0^\circ$** | $5.25\text{ cm}$ | $189.7\text{ px}$ | $8.61\%$ | Trivial center dummy baseline / degraded lighting condition |

---

## 3. Classification & Event Detection Metrics (Intent & Blinks)

IntuiGaze employs a 13-class temporal intent recognition engine (`IntentEngine` in `backend/eyenav/intent.py`) operating over a 1.5-second sliding window (45 frames at 30 FPS). The classes and their suggested OS commands are:

| Class ID | Intent Name | Suggested Command | Safety Risk Level (`safety.py`) | Required Dwell (`_get_dwell_required_ms`) |
|---|---|---|---|---|
| 0 | `idle` | `None` | `low_risk` | None |
| 1 | `reading` | `None` (suppress commands) | `low_risk` | None |
| 2 | `selecting` | `select` | `medium_risk` | $600\text{ ms}$ |
| 3 | `scrolling_up` | `scroll_up` | `low_risk` | None (cooldown $300\text{ ms}$) |
| 4 | `scrolling_down` | `scroll_down` | `low_risk` | None (cooldown $300\text{ ms}$) |
| 5 | `searching` | `None` (suppress commands) | `low_risk` | None |
| 6 | `activation` | `activate` | `medium_risk` | $600\text{ ms}$ |
| 7 | `deactivation` | `deactivate` | `medium_risk` | $600\text{ ms}$ |
| 8 | `confirmation` | `enter` | `medium_risk` | $600\text{ ms}$ (cooldown $1500\text{ ms}$) |
| 9 | `cancellation` | `escape` | `medium_risk` | $600\text{ ms}$ |
| 10 | `nav_back` | `back` | `medium_risk` | $600\text{ ms}$ (cooldown $1200\text{ ms}$) |
| 11 | `nav_forward` | `forward` | `medium_risk` | $600\text{ ms}$ (cooldown $1200\text{ ms}$) |
| 12 | `nav_home` | `home` | `high_risk` | $1200\text{ ms}$ |

*Additional High/Critical Risk Commands in `SafetyFilter`:* `delete` ($1200\text{ ms}$ dwell, $2000\text{ ms}$ cooldown), `shutdown` ($1200\text{ ms}$ dwell), `emergency_call` ($2000\text{ ms}$ dwell).

### 3.1 Extreme Class Imbalance & Metric Selection
In real interaction sessions, passive classes (`idle`, `reading`, `searching`) constitute over $88\%$ of all temporal frames. Active command gestures (`selecting`, `activation`, `nav_back`) represent fewer than $2\%$ of frames.

**Rule:** Overall classification accuracy $\frac{\sum TP}{\sum N}$ is **strictly prohibited** as a summary metric. A trivial model predicting `idle` on every frame achieves $>85\%$ accuracy while rendering the system completely inoperable.

#### Mandatory Per-Class Metrics:
1. **Precision ($P_c$):**
   $$P_c = \frac{TP_c}{TP_c + FP_c}$$
   Measures reliability of command execution. Low precision causes accidental commands.
2. **Recall ($R_c$):**
   $$R_c = \frac{TP_c}{TP_c + FN_c}$$
   Measures responsiveness. Low recall causes missed commands (user frustration).
3. **F1-Score ($F1_c$):**
   $$F1_c = \frac{2 \cdot P_c \cdot R_c}{P_c + R_c}$$
4. **Macro-Averaged F1 ($\text{Macro-F1}$):**
   $$\text{Macro-F1} = \frac{1}{C} \sum_{c=1}^C F1_c$$
   Weights all classes equally, preventing dominant classes from masking catastrophic gesture failure.
5. **Balanced Accuracy ($\text{B-Acc}$):**
   $$\text{Balanced Accuracy} = \frac{1}{C} \sum_{c=1}^C \frac{TP_c}{TP_c + FN_c} = \frac{1}{C} \sum_{c=1}^C R_c$$
6. **Precision-Recall AUC (PR-AUC):** For all sparse command classes ($c \in \{2, 6, 7, 8, 9, 10, 11, 12\}$), report PR-AUC computed across varying confidence thresholds $\tau \in [0.50, 0.99]$.

### 3.2 Confusion Matrix & Asymmetric Cost Matrix
Evaluation must include a full $13 \times 13$ normalized confusion matrix $M$, where $M_{i,j}$ represents the fraction of true class $i$ classified as class $j$.

#### Safety Risk Matrix (Asymmetric Cost of Errors):
In accessibility navigation, false positive command executions carry drastically higher cost than false negative omissions:
- **Missed Command (False Negative):** User fixates or double-blinks, but no click occurs. User simply repeats the gesture. Cost is low.
- **Accidental Command (False Positive):** User is reading text or scanning a webpage, and an accidental `select`, `delete`, or `enter` fires. This could delete documents, submit forms, or disrupt navigation. Cost is catastrophic.

```
+--------------------------------------------------------------------------------------------------+
|                             Intent Asymmetric Risk Architecture                                  |
|                                                                                                  |
|   True Intent: READING / SEARCHING                                                               |
|   +------------------------------------------------------------------------------------------+   |
|   | Predicted as READING/SEARCHING   --> SAFE (Reading suppression active)                  |   |
|   | Predicted as IDLE                --> SAFE (No command suggested)                         |   |
|   | Predicted as SELECTING/NAV       --> CATASTROPHIC FALSE TRIGGER (Safety Violation)       |   |
|   +------------------------------------------------------------------------------------------+   |
|                                                                                                  |
|   True Intent: SELECTING / NAVIGATION                                                            |
|   +------------------------------------------------------------------------------------------+   |
|   | Predicted as SELECTING/NAV       --> SUCCESS (Proceeds to multi-layer dwell/confidence)  |   |
|   | Predicted as IDLE/READING        --> RECOVERABLE FALSE NEGATIVE (User re-attempts)       |   |
|   +------------------------------------------------------------------------------------------+   |
+--------------------------------------------------------------------------------------------------+
```

#### Critical Danger Zones Monitored in Confusion Matrix:
1. $M_{\text{reading}, \text{selecting}}$: Reading saccade misclassified as a click. **Safety threshold: $\le 0.1\%$**.
2. $M_{\text{searching}, \text{selecting}}$: Visual search pattern misclassified as a click. **Safety threshold: $\le 0.1\%$**.
3. $M_{\text{reading}, \text{nav\_home}}$: Reading misclassified as system home navigation. **Safety threshold: $0.0\%$**.
4. $M_{\text{idle}, \text{deactivation}}$: Inadvertent deactivation while looking away. **Safety threshold: $\le 0.5\%$**.

### 3.3 Temporal Event Alignment & Operational Trigger Rates
Real-time interaction operates in the time domain. Discrete intent events must be evaluated using temporal event matching rather than isolated frame classification.

1. **Temporal Matching Window ($\Delta t$):** A predicted gesture event at timestamp $t_{\text{pred}}$ is matched to ground truth event at $t_{\text{gt}}$ if:
   $$|t_{\text{pred}} - t_{\text{gt}}| \le \Delta t_{\text{match}} = 200\text{ ms}$$
   Multiple predictions within the same matching window are de-duplicated into a single event.
2. **Dwell Detection Latency:** For fixation/dwell-triggered clicks, the latency is measured from the onset of gaze entry into the target bounding box $t_{\text{entry}}$ to the issuance of `VerifiedCommand(blocked=False)` $t_{\text{exec}}$:
   $$\text{Latency}_{\text{dwell}} = t_{\text{exec}} - t_{\text{entry}}$$
   - Target for medium-risk commands ($600\text{ ms}$ nominal dwell): $650\text{ ms} \pm 50\text{ ms}$.
   - Dwell Timing Jitter: Standard deviation $\sigma_{\text{dwell}} \le 30\text{ ms}$.
3. **Operational False Trigger Rate (FTR):**
   - **FTR per Hour (High-Risk Actions):** During continuous natural reading, typing, and video watching, total false executions of `select`, `enter`, `delete`, or `home` must be:
     $$\text{FTR}_{\text{high-risk}} < 1.0\text{ event / hour}$$
   - **FTR per Minute (Scroll Actions):** False scroll activations during static reading:
     $$\text{FTR}_{\text{scroll}} < 0.2\text{ events / minute}$$
4. **False Blink Trigger Rate:**
   In `backend/eyenav/cursor/controller.py`, double-blink triggers left click if two blinks occur within $\Delta t = 0.6\text{ s}$ (`_DOUBLE_BLINK_WINDOW_S = 0.6`).
   - Natural human spontaneous blink rate: $12\text{--}18\text{ blinks/minute}$.
   - Involuntary double-blink probability: $\sim 1.5\%$.
   - **Target False Click Rate from Natural Blinking:** $< 0.5\text{ false clicks / 10 minutes}$ of unconstrained reading.

---

## 4. Operational Failure Modes & Safety Criteria

IntuiGaze incorporates a 6-layer verification system (`SafetyFilter` in `backend/eyenav/safety.py`) and safety guards in `GazeCursorController` (`backend/eyenav/cursor/controller.py`). Candidate models and tracking pipelines must be evaluated against formal operational failure definitions.

```
+--------------------------------------------------------------------------------------------------+
|                                6-Layer Verification Architecture                                 |
|                                                                                                  |
|   Input Intent Prediction + EyeLandmarks                                                         |
|   |                                                                                              |
|   v                                                                                              |
|   [Layer 6: Emergency Stop] -------> Active? ----(YES)----> BLOCKED (Reason: EMERGENCY_STOP)    |
|   | (NO)                                                                                         |
|   v                                                                                              |
|   [Layer 1: Confidence Gate] ------> < Threshold? -(YES)--> BLOCKED (Reason: CONFIDENCE_THRESH) |
|   | (NO)                                                                                         |
|   v                                                                                              |
|   [Layer 2: Cooldown Limiter] -----> In Cooldown? -(YES)--> BLOCKED (Reason: COOLDOWN_ACTIVE)    |
|   | (NO)                                                                                         |
|   v                                                                                              |
|   [Layer 3: Context Validation] ---> Reading/Search? (YES)-> BLOCKED (Reason: CONTEXT_MISMATCH)  |
|   | (NO)                                                                                         |
|   v                                                                                              |
|   [Layer 4: Dwell Confirmation] ---> Dwell Met? --(NO)----> BLOCKED (Reason: DWELL_INCOMPLETE)   |
|   | (YES)                                                                                        |
|   v                                                                                              |
|   [Layer 5: Anti-Pattern Check] ---> High Entropy? (YES)--> BLOCKED (Reason: ANTI_PATTERN)       |
|   | (NO)                                                                                         |
|   v                                                                                              |
|   APPROVED COMMAND (VerifiedCommand: blocked=False, execution_id=UUID, layers_passed=6)          |
+--------------------------------------------------------------------------------------------------+
```

### 4.1 Gaze Tracking Loss & Low Confidence Gating
1. **Failure Modes:**
   - Face occlusion or subject leaves camera field of view.
   - Extreme head pose: Head yaw $|\psi| > 35^\circ$ or pitch $|\theta| > 25^\circ$.
   - Inadequate illumination: Image signal-to-noise ratio $\text{SNR} < 10\text{ dB}$ or mean facial luma $< 25$ (out of 255).
   - High prediction uncertainty: Normalized entropy $H_{\text{norm}} = -\sum p \ln p / \ln C > 0.60$ (`SafetyFilter` Layer 5).
2. **Safety Action on Tracking Loss:**
   - **Cursor Invariant:** Cursor position freezes instantly at the last confirmed valid coordinates. Cursor must NEVER jump to screen center $(0.5, 0.5)$ or drift when tracking is lost.
   - **Click Invariant:** All command emissions and click gestures are immediately blocked (`Fail-Closed`).
   - **Filter Reset:** When face is reacquired, smoothing filters (`OneEuroFilter`, `SaccadeFixationDetector`, `LagCompensationPredictor`) must be reset via `controller.reset_filters()` to purge stale momentum.
3. **Operational Metric:**
   - **Tracking Loss Rate ($\% \text{TLR}$):** Fraction of elapsed session time in tracking loss.
   - **Reacquisition Latency ($t_{\text{reacq}}$):** Time required to restore full tracking after subject returns to camera view (target $\le 150\text{ ms}$).

### 4.2 Maximum Cursor Jump Distance & Velocity Clamping
Abrupt cursor teleportation causes severe user disorientation, motion sickness, and dangerous accidental clicks across application windows.

1. **Physiological Saccadic Constraint:**
   - The fastest human ocular saccades peak at angular velocities of $\sim 700\text{--}900^\circ/\text{s}$.
   - On a 24" 1080p display at $60\text{ cm}$, $900^\circ/\text{s}$ equates to $\sim 34,000\text{ px/s}$.
   - At $30\text{ FPS}$ ($\Delta t = 33.3\text{ ms}$), the maximum physiological displacement between consecutive frames is:
     $$\Delta d_{\text{physio, max}} \approx 34,000\text{ px/s} \times 0.0333\text{ s} \approx 1,130\text{ px}$$
   - However, during focused task navigation (fixations and micro-saccades), frame-to-frame displacement rarely exceeds $150\text{ px}$.
2. **Safety Jump Threshold ($\Delta d_{\text{jump\_max}}$):**
   - Any frame-to-frame cursor displacement $\Delta d_t = \sqrt{(x_t - x_{t-1})^2 + (y_t - y_{t-1})^2} > 250\text{ px}$ without a detected saccade state is classified as an **Anomalous Prediction Jump**.
   - **Guard Mechanism:** Clamped by `OneEuroFilter(min_cutoff=0.05, beta=0.001)` and fixation gravity well (`_FIXATION_DEADZONE_PX = 45.0`).
   - **Operational Metric:** **Anomalous Jump Rate (AJR)**:
     $$\text{AJR} = \frac{\text{Count}(\Delta d_t > 250\text{ px and } GazeState \ne SACCADE)}{\text{Total Frames}} \times 100\%$$
     *Requirement:* $\text{AJR} \le 0.05\%$ (no more than 1 anomalous jump per 2,000 frames).

### 4.3 End-to-End Latency Budget & Frame Rate Maintenance
To achieve smooth cursor tracking and responsive control, IntuiGaze must maintain a sustained processing rate of $\ge 30\text{ FPS}$ on standard consumer x86_64 CPUs (e.g. Intel Core i5-8250U, quad-core, 1.6 GHz base) without discrete GPU acceleration.

$$\text{Frame Budget at } 30\text{ FPS} = \frac{1000\text{ ms}}{30} = 33.33\text{ ms}$$
IntuiGaze establishes an aggressive internal **target budget of $\le 20.0\text{ ms}$ per frame**, ensuring a $40\%$ headroom margin for background OS tasks and preventing frame drops.

#### Detailed Pipeline Component Latency Budget:
```
+--------------------------------------------------------------------------------------------------+
|                            Real-Time Per-Frame Latency Budget (<= 20 ms)                         |
|                                                                                                  |
|   Webcam Frame       MediaPipe Face      Gaze Inference /     Intent Engine    Safety Filter     |
|   Capture & Preproc  Landmarker Task     Mapper Polynomial    Transformer      & Smoothing       |
|                                                                                                  |
|   [  <= 5.0 ms  ] -> [  <= 6.0 ms  ] -> [  <= 4.0 ms  ] -> [  <= 3.0 ms  ] -> [  <= 2.0 ms  ]    |
|                                                                                                  |
|   Cumulative Latency: 5.0 ms -> 11.0 ms -> 15.0 ms -> 18.0 ms -> 20.0 ms                        |
|   Available Headroom before 30 FPS deadline (33.3 ms): 13.33 ms (40.0% safety margin)           |
+--------------------------------------------------------------------------------------------------+
```

| Pipeline Stage | Function / Module | Target Latency (ms) | Maximum Allowed Latency (ms) | Target Hardware Context |
|---|---|---|---|---|
| **1. Frame Acquisition** | OpenCV capture, format conversion, BGR $\to$ RGB | $3.5\text{ ms}$ | $5.0\text{ ms}$ | 720p @ 30 FPS USB 2.0/3.0 webcam |
| **2. Landmark Detection** | MediaPipe FaceLandmarker Tasks API (478 3D landmarks) | $5.0\text{ ms}$ | $6.0\text{ ms}$ | CPU (tflite/onnx runtime, 4 threads) |
| **3. Gaze Estimation** | `GazeScreenMapper` polynomial or L2CS-Net MobileNetV3 | $2.5\text{ ms}$ | $4.0\text{ ms}$ | Polynomial: $<0.5\text{ ms}$; L2CS-Net: $3.8\text{ ms}$ |
| **4. Intent Engine** | `IntentEngine` Tiny Temporal Transformer (45-frame window) | $2.0\text{ ms}$ | $3.0\text{ ms}$ | ONNX Runtime CPU |
| **5. Safety & Smoothing** | `SafetyFilter` (6 layers) + `OneEuroFilter` + Saccade detector | $1.0\text{ ms}$ | $1.5\text{ ms}$ | Pure NumPy / algorithmic |
| **6. Cursor Actuation** | OS cursor movement (`pyautogui.moveTo`) | $0.5\text{ ms}$ | $1.0\text{ ms}$ | OS Windows API (`PAUSE = 0.0`) |
| **TOTAL PIPELINE** | End-to-end (Camera sensor photon to OS cursor move) | **$14.5\text{ ms}$** | **$20.5\text{ ms}$** | Sustains $\ge 30\text{ FPS}$ (capable of $45\text{ FPS}$) |

#### Operational Metric:
- **95th Percentile Pipeline Latency ($L_{P95}$):** Must be $\le 25.0\text{ ms}$.
- **Dropped Frame Rate (DFR):** Percentage of camera frames that exceed the $33.33\text{ ms}$ deadline and are dropped. Requirement: $\text{DFR} \le 1.0\%$.

### 4.4 Stale Frame Handling & Pipeline Desynchronization
- **Stale Frame Definition:** Any frame whose acquisition timestamp $t_{\text{capture}}$ is older than $50.0\text{ ms}$ relative to processing time ($t_{\text{now}} - t_{\text{capture}} > 50\text{ ms}$).
- **Stale Frame Rule:** Stale frames must be discarded immediately without executing cursor actuation or intent state updates. Gaze control must never actuate based on stale historical eye positions.
- **Consecutive Stale Frame Trigger:** If $\ge 3$ consecutive frames are stale (indicating camera bus stall or CPU throttling $> 100\text{ ms}$), the system must freeze the cursor and trigger an amber UI warning indicator.

### 4.5 Emergency Stop & Failsafe Verification
Safety in IntuiGaze is governed by four independent physical and software escape vectors:

| Escape Mechanism | Trigger Condition | Code Enforcement Location | Action Taken | Override Recovery |
|---|---|---|---|---|
| **1. Physical Mouse Override** | Physical mouse moved $> 15\text{ px}$ from commanded position | `backend/eyenav/cursor/controller.py` lines 143–155 | Immediately pause eye tracking for $2.0\text{ seconds}$ (`_PHYSICAL_PAUSE_S = 2.0`) | Resumes automatically after $2.0\text{ s}$ of physical stillness |
| **2. Extended Eye Closure** | Sustained eye closure for $\ge 3.0\text{ s}$ ($EAR < 0.68 \times \text{baseline}$) | `backend/eyenav/safety.py` lines 38–40, 172–184 | Layer 6 triggers `EMERGENCY_STOP`; blocks ALL commands unconditionally | Requires explicit user re-enable via `clear_emergency_stop()` |
| **3. Screen Corner Failsafe** | Cursor driven into any screen corner $(0, 0)$ | PyAutoGUI core (`pyautogui.FAILSAFE = True`) | Raises `pyautogui.FailSafeException`, terminates cursor thread | Application restart required |
| **4. Global Escape Hotkey** | Pressing `Win+F9` or `Esc` on physical keyboard | Global keyboard hook | Calls `SafetyFilter.trigger_emergency_stop()` | Manual unpause |

**Automated Test Invariant:** In compliance with `AGENTS.md` and `PROJECT.md` R2, desktop mouse actuation is strictly forbidden during automated tests (`pytest`). All tests must use mock/stub cursor adapters or dry-run mode.

---

## 5. Statistical Significance & Model Comparison Methodology

### 5.1 Participant-Grouped Evaluation Architecture (Zero Leakage)
As established in `docs/data/DATASET_CARD.md` and `explorer_survey_3/handoff.md`, the dataset partition consists of:
- **Train Split:** 230 subjects ($289,591$ frames, $82.9\%$)
- **Validation Split:** 7 subjects ($13,340$ frames, $3.8\%$)
- **Test Split (Sealed):** 26 subjects ($46,438$ frames, $13.3\%$)

#### Macro-Averaging vs Micro-Averaging:
- **Micro-Average:** Pooling all $46,438$ test frames together. This is **prohibited as the sole evaluation metric** because subjects with thousands of frames (e.g. 3,590 frames) would disproportionately dominate subjects with fewer frames (e.g. 500 frames).
- **Macro-Average (Subject-Level):** Compute metric $M_s$ independently for each of the $S = 26$ test subjects, then calculate the mean, median, and spread across the 26 subjects:
  $$\bar{M}_{\text{macro}} = \frac{1}{S} \sum_{s=1}^S M_s, \quad \text{Median}_{\text{macro}} = \text{Median}(\{M_1, \dots, M_S\})$$

### 5.2 Hypothesis Testing & Significance Criteria
When comparing a candidate model $M_{\text{cand}}$ against an established baseline $M_{\text{base}}$:

1. **Paired Non-Parametric Testing (Wilcoxon Signed-Rank Test):**
   - Because per-subject error distributions violate normality assumptions, the standard paired Student's $t$-test is invalid.
   - We perform the **two-sided Wilcoxon signed-rank test** on the paired per-subject median errors:
     $$d_s = \text{Median}(e_{s, \text{cand}}) - \text{Median}(e_{s, \text{base}}) \quad \text{for } s \in \{1, \dots, 26\}$$
   - **Significance Level:** A candidate model is deemed statistically superior only if $p < 0.01$ and $d_s < 0$ in $\ge 18$ of the 26 subjects ($> 69\%$).
2. **Bootstrap Confidence Intervals:**
   - 95% Confidence Intervals are computed via non-parametric subject bootstrap with $B = 10,000$ resamples:
     $$\text{CI}_{95\%} = [\text{Percentile}_{2.5\%}(M^*), \text{Percentile}_{97.5\%}(M^*)]$$
   - Reported for all primary metrics: Median Euclidean px, P90 Euclidean px, and $Hit@50\text{px}$.

### 5.3 Slice-Based Disaggregated Evaluation
To guarantee that improvements are robust and not achieved by optimizing for a single device or posture, performance must be disaggregated across the following sub-population slices:

```
+--------------------------------------------------------------------------------------------------+
|                                    Slice-Based Disaggregation                                    |
|                                                                                                  |
|   [Device Orientation Slices]        [Hardware Device Slices]         [Gaze Eccentricity Slices] |
|   - Portrait (Orientation 1)         - iPhone (Small screen)          - Foveal Center (<= 20% D) |
|   - Portrait Upside Down (2)         - iPad (Large tablet)            - Mid-field (20% - 40% D)  |
|   - Landscape Right (3)                                               - Extreme Periphery (>40%) |
|   - Landscape Left (4)                                                                           |
+--------------------------------------------------------------------------------------------------+
```

1. **Device Orientation Slices:**
   - Orientation 1 (Portrait), Orientation 2 (Portrait Upside Down), Orientation 3 (Landscape Right), Orientation 4 (Landscape Left).
   - Landscape orientations are critical because they mirror desktop monitor aspect ratios ($16:9$).
2. **Device Hardware Family:**
   - Phone vs Tablet: iPhone screens ($320\text{--}414\text{ pt}$ width) vs iPad screens ($768\text{--}1024\text{ pt}$ width).
3. **Gaze Eccentricity (Center vs Periphery):**
   - Screen Center ($< 20\%$ diagonal distance from center $(0.5, 0.5)$).
   - Screen Periphery / Corners ($> 40\%$ diagonal distance from center).
   - Camera lens distortion and eye rotation mechanics cause periphery errors to be typically $2\times$ higher than central gaze.

---

## 6. Unified Evaluation Reporting Specification

### 6.1 Standard Evaluation Metric Table Schema
Every evaluation run in IntuiGaze must generate a structured report conforming to the following metric schema:

```markdown
### Model Evaluation Scorecard: [Model Name / Checkpoint ID]
- **Date & Git Commit:** [YYYY-MM-DD | Commit Hash]
- **Dataset Partition:** Test Set (26 unseen subjects, 46,438 frames)
- **Reference Resolution:** 1920 × 1080 (FHD Desktop, 92 PPI) | Viewing Distance: 60 cm

| Metric Category | Specific Metric | Unit | Mean ± Std | Median (P50) | P90 Tail | P95 Tail | Max Error | Baseline Comparison (Delta) |
|---|---|---|---|---|---|---|---|---|
| **Coordinate Regression** | Euclidean Error (px @ 1080p) | pixels | [val] ± [val] | [val] | [val] | [val] | [val] | [val vs baseline] |
| | Normalized Diagonal Error | % Screen Diag | [val] % | [val] % | [val] % | [val] % | [val] % | [val vs baseline] |
| | Component MAE_x | pixels | [val] | [val] | [val] | [val] | [val] | [val vs baseline] |
| | Component MAE_y | pixels | [val] | [val] | [val] | [val] | [val] | [val vs baseline] |
| | Visual Angle Error | degrees (°) | [val]° | [val]° | [val]° | [val]° | [val]° | [val vs baseline] |
| **Target Acquisition** | Hit@25px (Fine Targets) | % trials | [val] % | - | - | - | - | [val vs baseline] |
| | Hit@50px (Standard Targets) | % trials | [val] % | - | - | - | - | [val vs baseline] |
| | Hit@100px (Coarse Targets) | % trials | [val] % | - | - | - | - | [val vs baseline] |
| **Intent Classification** | Macro-F1 (13 classes) | score ∈ [0, 1] | [val] | - | - | - | - | [val vs baseline] |
| | Balanced Accuracy | score ∈ [0, 1] | [val] | - | - | - | - | [val vs baseline] |
| | Select Gesture Precision | score ∈ [0, 1] | [val] | - | - | - | - | [val vs baseline] |
| | Select Gesture Recall | score ∈ [0, 1] | [val] | - | - | - | - | [val vs baseline] |
| **Operational & Safety** | End-to-End Latency (P95) | ms | [val] ms | [val] ms | [val] ms | [val] ms | [val] ms | [Budget <= 20.0 ms] |
| | Sustained Frame Rate | FPS | [val] FPS | - | - | - | - | [Target >= 30.0 FPS] |
| | Dropped Frame Rate | % frames | [val] % | - | - | - | - | [Gate <= 1.0%] |
| | Anomalous Jump Rate (>250px) | % frames | [val] % | - | - | - | - | [Gate <= 0.05%] |
| | False Command Rate (Reading) | events / hour | [val] | - | - | - | - | [Gate < 1.0 / hour] |
```

### 6.2 Hard Safety Release Gate Checklist
Before any trained model artifact can be registered into `backend/eyenav/models/` or enabled in the live pipeline, it must satisfy all 8 binary safety gates:

- [ ] **Gate 1 (Zero Participant Leakage):** Verified that 0 frames or subjects from the 26-subject test set appeared in training/validation splits or preprocessing fits.
- [ ] **Gate 2 (Latency Budget Compliance):** P95 inference latency on reference CPU $\le 20.0\text{ ms}$ ($\ge 30\text{ FPS}$ sustained).
- [ ] **Gate 3 (Catastrophic Error Ceiling):** P95 Euclidean error $\le 180\text{ px}$ on reference 1080p display (ensures cursor stays within general quadrant of gaze).
- [ ] **Gate 4 (Reading Suppression):** False command activation rate during continuous reading patterns $\le 1.0\text{ event / hour}$.
- [ ] **Gate 5 (Fail-Closed Confidence Gate):** Verified that frames with prediction confidence $< 0.85$ produce `VerifiedCommand(blocked=True)` with zero click emission.
- [ ] **Gate 6 (Emergency Stop Integrity):** 3-second continuous eye closure triggers `EMERGENCY_STOP` with $100\%$ reliability across 100 consecutive synthetic test trials.
- [ ] **Gate 7 (Physical Override Integrity):** Physical mouse movement of $\ge 15\text{ px}$ pauses eye tracking for $2.0\text{ s}$ with zero delay.
- [ ] **Gate 8 (Automated Test Isolation):** Test suites execute with mock cursor adapters; real OS desktop mouse movement strictly disabled.

---

## 7. Actionable Implementation Path for Downstream Milestones

1. **For Milestone 3 Synthesis (`docs/ml/ML_PROBLEM_DEFINITION.md`):**
   - Transcribe Section 2 (Regression Metrics), Section 3 (Intent Metrics), Section 4 (Operational Safety Criteria), and Section 6 (Release Gate Checklist) directly into `docs/ml/ML_PROBLEM_DEFINITION.md`.
2. **For Milestone 4 (`scripts/audit_dataset.py` & Manifest Generator):**
   - Manifest schema must store both pixel targets (`XPts`, `YPts`), screen dimensions (`screen_w`, `screen_h`), orientation (`1..4`), and precomputed normalized coordinates (`target_x_norm`, `target_y_norm`) to enable exact computation of $e_{\text{px}}$ and $e_{\text{diag}}$.
3. **For Milestone 5 (Evaluation Harness & Baseline Models):**
   - Build `tests/ml/eval_harness.py` implementing the vectorised metric functions: `compute_euclidean_metrics()`, `compute_hit_rates()`, `compute_confusion_matrix()`, and `run_wilcoxon_comparison()`.
