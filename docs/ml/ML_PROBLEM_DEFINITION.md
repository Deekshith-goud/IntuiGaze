# IntuiGaze — Machine Learning Problem Definition, Architectural Specifications, and Evaluation Standards

**Document Identifier:** `docs/ml/ML_PROBLEM_DEFINITION.md`  
**Document Version:** 1.0.0  
**Status:** Approved / Authoritative Engineering Standard  
**Release Milestone:** Milestone 3 (Step 9)  
**Date:** 2026-10-29  
**Target Audience:** Machine Learning Engineers, Computer Vision Researchers, Systems Integrators, Safety & Ethics Auditors  
**Applicable Operating Contracts:**
- Repository Contract: [`AGENTS.md`](../../AGENTS.md)
- ML Evaluation Policy: [`docs/ml/METRICS_POLICY.md`](METRICS_POLICY.md)
- Ethics & Responsible AI: [`docs/business/ETHICS.md`](../business/ETHICS.md)
- Preserved Code Invariant: [`backend/eyenav/cursor/controller.py`](../../backend/eyenav/cursor/controller.py)
- Preserved Data Invariant: `archive.zip` (Root 20.13 GB compressed dataset)
- Preserved Model Asset: `face_landmarker.task` (Root MediaPipe vision model)

---

## Table of Contents

1. [Executive Summary & Problem Scope](#1-executive-summary--problem-scope)
2. [Primary Task: Normalized Screen Coordinate Regression](#2-primary-task-normalized-screen-coordinate-regression)
   - [2.1 Mathematical Formulation](#21-mathematical-formulation)
   - [2.2 Screen Coordinate Geometry & Affine Transformations](#22-screen-coordinate-geometry--affine-transformations)
   - [2.3 Output Layer Architecture & Bounding Policy](#23-output-layer-architecture--bounding-policy)
   - [2.4 Loss Function Hierarchy](#24-loss-function-hierarchy)
   - [2.5 Multi-Task Loss Formulation](#25-multi-task-loss-formulation)
3. [Secondary Prediction Tasks](#3-secondary-prediction-tasks)
   - [3.1 Task S1: 3D Gaze Direction Angular Regression](#31-task-s1-3d-gaze-direction-angular-regression)
   - [3.2 Task S2: 13-Class Temporal Intent Recognition](#32-task-s2-13-class-temporal-intent-recognition)
4. [Multimodal Feature Input Space & Latency Budget](#4-multimodal-feature-input-space--latency-budget)
   - [4.1 Multimodal Ingestion Contract](#41-multimodal-ingestion-contract)
   - [4.2 Modality Processing Specifications](#42-modality-processing-specifications)
   - [4.3 Real-Time CPU Latency Budget](#43-real-time-cpu-latency-budget)
5. [Comprehensive Evaluation Metrics & Error Distribution Policy](#5-comprehensive-evaluation-metrics--error-distribution-policy)
   - [5.1 Continuous Regression Metrics](#51-continuous-regression-metrics)
   - [5.2 Predeclared Target Hit Rates](#52-predeclared-target-hit-rates)
   - [5.3 Angular Gaze Error Conversion](#53-angular-gaze-error-conversion)
   - [5.4 Intent Classification & Temporal Event Metrics](#54-intent-classification--temporal-event-metrics)
   - [5.5 Operational Safety Criteria & Failure Modes](#55-operational-safety-criteria--failure-modes)
   - [5.6 Statistical Significance & Disaggregated Slice Evaluation](#56-statistical-significance--disaggregated-slice-evaluation)
6. [Baseline Model Progression Hierarchy](#6-baseline-model-progression-hierarchy)
   - [6.1 Level 0: Trivial Center Dummy Baseline](#61-level-0-trivial-center-dummy-baseline)
   - [6.2 Level 1: Polynomial Ridge Regression Mapper](#62-level-1-polynomial-ridge-regression-mapper)
   - [6.3 Level 2: Random Forest / GBDT Tabular Regressor](#63-level-2-random-forest--gbdt-tabular-regressor)
   - [6.4 Level 3: Deep Appearance CNN](#64-level-3-deep-appearance-cnn)
   - [6.5 Baseline Hierarchy Comparison Matrix](#65-baseline-hierarchy-comparison-matrix)
7. [Dataset Partitioning, Archive Invariants & Leakage Prevention](#7-dataset-partitioning-archive-invariants--leakage-prevention)
   - [7.1 Native MIT GazeCapture Partition Inventory](#71-native-mit-gazecapture-partition-inventory)
   - [7.2 The Zero-Leakage Grouping Invariant](#72-the-zero-leakage-grouping-invariant)
   - [7.3 Cryptographic Test Set Sealing Protocol](#73-cryptographic-test-set-sealing-protocol)
   - [7.4 `archive.zip` Integrity & Safe In-Memory Pipeline](#74-archivezip-integrity--safe-in-memory-pipeline)
   - [7.5 Four-Point Data Quality Filtering Criteria](#75-four-point-data-quality-filtering-criteria)
8. [Safety, Privacy & Ethical Compliance](#8-safety-privacy--ethical-compliance)
   - [8.1 100% On-Device Execution & Ephemeral Frame Lifecycle](#81-100-on-device-execution--ephemeral-frame-lifecycle)
   - [8.2 Opt-In Actuation & Visual State Transparency](#82-opt-in-actuation--visual-state-transparency)
   - [8.3 Physical Mouse Priority Override](#83-physical-mouse-priority-override)
   - [8.4 Six-Layer Command Safety Filter & Fail-Closed Policy](#84-six-layer-command-safety-filter--fail-closed-policy)
   - [8.5 Disability Rights & Anti-Surveillance Ethics](#85-disability-rights--anti-surveillance-ethics)
9. [Model Promotion & Release Verification Gate](#9-model-promotion--release-verification-gate)
10. [References & Document History](#10-references--document-history)

---

## 1. Executive Summary & Problem Scope

IntuiGaze is an experimental, real-time gaze-controlled computer navigation system engineered to provide accessible, hands-free desktop interaction using commodity monocular webcams on standard consumer central processing units (CPUs).

Unlike passive gaze-tracking systems designed purely for observational research or offline heatmaps, IntuiGaze operates in a closed-loop cyber-physical environment. Model predictions are coupled directly to the host operating system's mouse cursor and critical command triggers (`select`, `scroll_up`, `scroll_down`, `back`, `forward`, `enter`, `delete`). Consequently, statistical accuracy cannot be evaluated in isolation from operational safety: an errant saccadic jump, tracking loss spike, or false click can cause permanent user data loss, UI disorientation, or accessibility lock-out.

```
+--------------------------------------------------------------------------------------------------+
|                                  IntuiGaze System Topology                                       |
|                                                                                                  |
|   +------------------+         +----------------------+         +----------------------------+   |
|   | Consumer Webcam  | ------> | MediaPipe / OpenCV   | ------> | Multimodal Feature Space   |   |
|   | (720p/1080p RGB) |         | Vision Front-End     |         | (Crops, Grid, 478 Lndmrks) |   |
|   +------------------+         +----------------------+         +--------------+-------------+   |
|                                                                                |                 |
|                                        +---------------------------------------+                 |
|                                        v                                                         |
|   +------------------------------------------------------------------------------------------+   |
|   | Primary ML Inference Engine (Latency <= 6 ms CPU)                                        |   |
|   |  * Primary: Normalized Coordinate Regression f(X) -> (x_norm, y_norm) in [0, 1]^2        |   |
|   |  * S1 Auxiliary: 3D Gaze Direction Vector d in S^2 (Pitch / Yaw Binned Soft-Argmax)      |   |
|   |  * S2 Auxiliary: 13-Class Temporal Intent Engine over 45x32 Buffer                       |   |
|   +--------------------------------------------+---------------------------------------------+   |
|                                                |                                                 |
|                                                v                                                 |
|   +------------------------------------------------------------------------------------------+   |
|   | Runtime Post-Processing & Cyber-Physical Safety Stack                                    |   |
|   |  * Two-Stage Guard: Track Loss Anomaly Gate (|z - 0.5| > 0.75) + Deterministic [0, 1] Clip |   |
|   |  * Temporal Smoothing: One-Euro Filter + Saccade / Fixation Gravity Deadzone (45.0 px)   |   |
|   |  * Six-Layer Command Verification: Confidence, Cooldown, Context, Dwell, Anti-Pattern,   |   |
|   |    and 3-Second Eye-Closure Emergency Stop (Fail-Closed Default)                         |   |
|   |  * Physical Mouse Priority Override (15 px displacement pauses gaze for 2.0 s)           |   |
|   +--------------------------------------------+---------------------------------------------+   |
|                                                |                                                 |
|                                                v                                                 |
|   +------------------------------------------------------------------------------------------+   |
|   | Operating System Desktop Actuation (pyautogui: FAILSAFE=True, PAUSE=0.0)                 |   |
|   +------------------------------------------------------------------------------------------+   |
+--------------------------------------------------------------------------------------------------+
```

This specification establishes the authoritative mathematical formulations, coordinate transformations, loss functions, secondary auxiliary tasks, multimodal feature representations, evaluation metric suites, baseline hierarchies, dataset partitioning invariants, and safety gates governing all machine learning development in IntuiGaze.

---

## 2. Primary Task: Normalized Screen Coordinate Regression

### 2.1 Mathematical Formulation

Let $\mathcal{X}$ denote the multimodal input feature space (comprising facial crops, eye patches, spatial face grids, and geometric facial landmarks).  
Let $\mathcal{Y} \subset \mathbb{R}^2$ denote the compact continuous target space of normalized screen coordinates:

$$\mathcal{Y} = [0, 1] \times [0, 1] = [0, 1]^2$$

The primary learning task is to learn a parameterised mapping function:

$$f_{\boldsymbol{\theta}}: \mathcal{X} \to \mathcal{Y}, \quad \hat{\mathbf{s}} = f_{\boldsymbol{\theta}}(\mathbf{x}) = \begin{pmatrix} \hat{x}_{\text{norm}} \\ \hat{y}_{\text{norm}} \end{pmatrix} \in [0, 1]^2$$

where:
- $\hat{x}_{\text{norm}} \in [0.0, 1.0]$ represents the horizontal gaze position on the active display ($0.0$ indicates the extreme left display boundary, $1.0$ indicates the extreme right display boundary).
- $\hat{y}_{\text{norm}} \in [0.0, 1.0]$ represents the vertical gaze position on the active display ($0.0$ indicates the extreme top display boundary, $1.0$ indicates the extreme bottom display boundary).
- $(0.0, 0.0)$ corresponds to the top-left corner of the display viewport, strictly adhering to computer graphics and operating system window coordinate standards (Windows GDI/DirectX, macOS Quartz, and X11/Wayland).

### 2.2 Screen Coordinate Geometry & Affine Transformations

#### 2.2.1 Desktop Screen Mapping
Given an active physical desktop display with horizontal resolution $W_{\text{screen}} \in \mathbb{N}$ pixels and vertical resolution $H_{\text{screen}} \in \mathbb{N}$ pixels, continuous normalized predictions $\hat{\mathbf{s}} = (\hat{x}_{\text{norm}}, \hat{y}_{\text{norm}})^T$ are mapped to physical pixel coordinates $\hat{\mathbf{p}} = (\hat{x}_{\text{px}}, \hat{y}_{\text{px}})^T$ via the affine transformation:

$$\hat{x}_{\text{px}} = \operatorname{round}\left( \hat{x}_{\text{norm}} \cdot (W_{\text{screen}} - 1) \right)$$

$$\hat{y}_{\text{px}} = \operatorname{round}\left( \hat{y}_{\text{norm}} \cdot (H_{\text{screen}} - 1) \right)$$

For sub-pixel cursor filtering (e.g., One-Euro Filter or Saccade Fixation Deadzone in `controller.py`), continuous un-rounded floating-point coordinates are maintained:

$$\mathbf{p}_{\text{cont}} = \begin{pmatrix} \hat{x}_{\text{norm}} \cdot W_{\text{screen}} \\ \hat{y}_{\text{norm}} \cdot H_{\text{screen}} \end{pmatrix} \in \mathbb{R}^2$$

#### 2.2.2 MIT GazeCapture Ground Truth Extraction & Device Orientations
The ground truth benchmark dataset for IntuiGaze is the 20.13 GB MIT GazeCapture corpus (`archive.zip`), recorded on Apple iOS devices (iPhones and iPads). To construct leak-free, mathematically consistent training targets across varying hardware, the extraction pipeline maps raw iOS sensor coordinates to canonical normalized space.

For each frame $k$ in a subject's recording session:
1. `dotInfo.json`:
   - $\text{XPts}[k], \text{YPts}[k]$: Gaze target location in Apple UIKit points ($\text{pts}$).
   - $\text{XCam}[k], \text{YCam}[k]$: 3D displacement vector of the gaze target relative to the camera lens optical center in **centimeters** ($\text{cm}$).
2. `screen.json`:
   - $W[k]$: Screen width in UIKit points in the active orientation.
   - $H[k]$: Screen height in UIKit points in the active orientation.
   - $\text{Orientation}[k]$: iOS `UIDeviceOrientation` enum $\in \{1, 2, 3, 4\}$.

#### 2.2.3 Device Orientation Definitions & Transformations
Apple iOS defines four physical device orientations:
- **Orientation 1 (`UIDeviceOrientationPortrait`)**: Device held upright; Home button at bottom; Front camera at top center.
- **Orientation 2 (`UIDeviceOrientationPortraitUpsideDown`)**: Device inverted; Home button at top; Front camera at bottom center.
- **Orientation 3 (`UIDeviceOrientationLandscapeRight`)**: Device rotated $90^\circ$ clockwise (from user perspective, Home button is on the left; camera on the right).
- **Orientation 4 (`UIDeviceOrientationLandscapeLeft`)**: Device rotated $90^\circ$ counter-clockwise (Home button is on the right; camera on the left).

In `screen.json`, $W[k]$ and $H[k]$ record the active display aspect ratio in the specific orientation (e.g., iPhone 5 has $W=320, H=568$ in Orientation 1, and $W=568, H=320$ in Orientations 3 and 4).

Therefore, direct screen-space normalized ground truth $\mathbf{y}_{\text{norm}} = (x_{\text{norm}}, y_{\text{norm}})^T$ is computed as:

$$x_{\text{norm}}[k] = \frac{\text{XPts}[k]}{W[k]}, \quad y_{\text{norm}}[k] = \frac{\text{YPts}[k]}{H[k]}$$

Subject to the validity constraint: $x_{\text{norm}}[k] \in [0.0, 1.0]$ and $y_{\text{norm}}[k] \in [0.0, 1.0]$ within numerical tolerance $\epsilon_{\text{tol}} = 10^{-4}$.

#### 2.2.4 Metric Camera-Space Transformation (Cross-Device Transfer)
For physical metric modeling independent of screen scale, target gaze displacement in centimeters $(X_{\text{cam}}, Y_{\text{cam}})$ relates to screen points via the orientation rotation matrix $\mathbf{R}_{\text{orient}}$ and screen points-per-centimeter ($\text{PPC} = \frac{\text{PPI}}{2.54}$):

$$\begin{pmatrix} X_{\text{cam}} \\ Y_{\text{cam}} \end{pmatrix} = \mathbf{R}_{\text{orient}} \cdot \begin{pmatrix} \frac{\text{XPts} - x_{\text{cam\_pts}}}{\text{PPC}} \\ \frac{\text{YPts} - y_{\text{cam\_pts}}}{\text{PPC}} \end{pmatrix}$$

where:

$$\mathbf{R}_1 = \begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix}, \quad \mathbf{R}_2 = \begin{pmatrix} -1 & 0 \\ 0 & -1 \end{pmatrix}, \quad \mathbf{R}_3 = \begin{pmatrix} 0 & 1 \\ -1 & 0 \end{pmatrix}, \quad \mathbf{R}_4 = \begin{pmatrix} 0 & -1 \\ 1 & 0 \end{pmatrix}$$

---

### 2.3 Output Layer Architecture & Bounding Policy

A foundational architectural decision in gaze coordinate regression is whether to constrain predictions within $[0, 1]$ using a saturating activation function (such as Sigmoid $\sigma(z) = \frac{1}{1 + e^{-z}}$) or to predict unbounded linear logits followed by external safety guards.

#### 2.3.1 Mathematical Rejection of Bounded Sigmoid Activation
- **Mathematical Form:** $\hat{y} = \sigma(z) = \frac{1}{1 + e^{-z}} \in (0, 1)$.
- **Derivative & Gradient Flow:**
  $$\frac{\partial \hat{y}}{\partial z} = \sigma(z)(1 - \sigma(z))$$
- **The Vanishing Edge Gradient Problem:** As gaze targets approach screen borders and corner interactive controls ($y \to 0.0$ or $y \to 1.0$), the required logit input must approach infinity:
  $$\lim_{y \to 0} z = -\infty, \quad \lim_{y \to 1} z = +\infty$$
  Consequently, the backpropagated gradient vanishes asymptotically:
  $$\lim_{z \to \pm \infty} \frac{\partial \hat{y}}{\partial z} = 0$$
- **Operational Failure Mode:** In desktop graphical user interfaces, high-priority interactive targets are concentrated precisely along display borders: the taskbar, system tray, browser tabs, close/minimize buttons, and navigation menus. A Sigmoid output layer compresses network gradients near the borders, causing a catastrophic "center-pull" bias where the cursor resists moving into corners and consistently under-shoots boundary widgets.

#### 2.3.2 Unbounded Linear Regression Architecture
IntuiGaze mandates **unbounded linear logits** for the output regression head:

$$\hat{\mathbf{s}}_{\text{raw}} = \mathbf{W}_o \mathbf{h} + \mathbf{b}_o \in \mathbb{R}^2$$

- **Gradient Dynamics:**
  $$\frac{\partial \hat{\mathbf{s}}_{\text{raw}}}{\partial (\mathbf{W}_o \mathbf{h} + \mathbf{b}_o)} = \mathbf{I}_2$$
  Gradient flow is strictly linear and uniform across the entire visual field, ensuring identical optimization dynamics whether the user fixates on the screen center or extreme corner buttons.

#### 2.3.3 The Two-Stage Post-Processing Safety Guard
To protect against runaway predictions caused by eye blinks, extreme head poses, or visual noise without corrupting training gradients, IntuiGaze implements a deterministic two-stage post-processing guard:

```
Unbounded Logits z in R^2
       |
       v
+---------------------------------------------------------------------------------+
| Stage 1: Off-Screen Anomaly Track Loss Detector                                 |
| Condition: z_x < -0.25 OR z_x > 1.25 OR z_y < -0.25 OR z_y > 1.25                |
+---------------------------------------------------------------------------------+
       |                                          |
    [Anomalous]                                [Valid]
       |                                          |
       v                                          v
+--------------------------------+   +--------------------------------------------+
| * Flag Gaze Divergence / Loss  |   | Stage 2: Deterministic Clamping            |
| * Freeze Cursor Position       |   | x_clamped = max(0.0, min(1.0, z_x))        |
| * Force Confidence C = 0.0     |   | y_clamped = max(0.0, min(1.0, z_y))        |
| * Inhibit Clicks (Layer 1 & 5) |   +--------------------------------------------+
+--------------------------------+                |
                                                  v
                                     Dispatched to One-Euro Filter &
                                     Deadzone Anchor (45.0 px)
```

1. **Stage 1 — Off-Screen Anomaly Track Loss Detector:**
   Define an anomaly margin $\epsilon_{\text{guard}} = 0.25$ (25% beyond the physical screen bezel):
   $$\text{IsAnomaly}(\hat{\mathbf{s}}_{\text{raw}}) = \mathbb{I}\left( \hat{x}_{\text{norm}} < -0.25 \;\lor\; \hat{x}_{\text{norm}} > 1.25 \;\lor\; \hat{y}_{\text{norm}} < -0.25 \;\lor\; \hat{y}_{\text{norm}} > 1.25 \right)$$
   If $\text{IsAnomaly} = 1$, the frame is marked as **Gaze Divergence / Tracking Loss**. The cursor position update is inhibited (cursor freezes at its last verified valid coordinate), prediction confidence is forced to $0.0$, and the safety filter immediately blocks all command emissions.
2. **Stage 2 — Deterministic Coordinate Clamping:**
   For valid non-anomalous frames, coordinates are deterministically clamped to the active display bounds:
   $$\hat{x}_{\text{clamped}} = \max\left(0.0, \min\left(1.0, \hat{x}_{\text{norm}}\right)\right)$$
   $$\hat{y}_{\text{clamped}} = \max\left(0.0, \min\left(1.0, \hat{y}_{\text{norm}}\right)\right)$$
   This ensures that the OS cursor never escapes the physical monitor, while completely eliminating edge gradient vanishing during backpropagation.

---

### 2.4 Loss Function Hierarchy

Let $\mathbf{y}_i = (x_i, y_i)^T \in [0, 1]^2$ be the ground truth normalized coordinate vector, and $\hat{\mathbf{y}}_i = (\hat{x}_i, \hat{y}_i)^T \in \mathbb{R}^2$ be the model prediction. The residual vector is $\mathbf{r}_i = \hat{\mathbf{y}}_i - \mathbf{y}_i = (r_{x,i}, r_{y,i})^T$.

```
+--------------------------------------------------------------------------------------------------+
|                                    Loss Function Hierarchy                                       |
|                                                                                                  |
|   1. Adaptive Wing (AWing) Loss (omega = 0.05, epsilon = 0.01) [PRIMARY RECOMMENDATION]          |
|      - Logarithmic curvature near zero: steep gradients (|r| -> 0) push sub-pixel micro-fixation |
|      - Linear penalty for large errors bounds saccadic outlier explosions                        |
|                                                                                                  |
|   2. Huber / Smooth L1 Loss (delta = 0.02) [ROBUST REGRESSION BASELINE]                          |
|      - Quadratic for |r| <= 0.02 (~38 px on 1080p); Linear for |r| > 0.02                        |
|      - Bounded gradient (+- 0.02) neutralizes blink and head-movement outliers                   |
|                                                                                                  |
|   3. Pinball Loss (tau in {0.1, 0.5, 0.9}) [PREDICTIVE UNCERTAINTY HEAD]                         |
|      - Asymmetric quantile loss: computes 80% confidence interval width U_x, U_y                 |
|      - Generates principled dynamic confidence C = exp(-||U||_2 / sigma) to feed Layer 1 Gate   |
|                                                                                                  |
|   4. Mean Squared Error (MSE) [REJECTED FOR RAW GAZE]                                            |
|      - Quadratic penalty (r^2) allows transient saccades to overpower batch gradients            |
+--------------------------------------------------------------------------------------------------+
```

#### 2.4.1 Mean Squared Error (MSE) & Failure Analysis in Gaze Tracking
$$\mathcal{L}_{\text{MSE}}(\mathbf{y}, \hat{\mathbf{y}}) = \frac{1}{2N} \sum_{i=1}^N \|\hat{\mathbf{y}}_i - \mathbf{y}_i\|_2^2 = \frac{1}{2N} \sum_{i=1}^N \left( r_{x,i}^2 + r_{y,i}^2 \right)$$

- **Gradient:** $\frac{\partial \mathcal{L}_{\text{MSE}}}{\partial \hat{\mathbf{y}}_i} = \frac{1}{N} \mathbf{r}_i$.
- **Failure Mode:** Gradient magnitude is strictly proportional to residual error magnitude $\|\mathbf{r}_i\|$. In unconstrained gaze tracking, natural eye blinks, camera motion blur, and exploratory saccades introduce large transient residuals ($r > 0.5$ in normalized space). Because MSE penalizes errors quadratically, these outlier frames generate massive gradients that dominate mini-batch updates, disrupting convergence on fine fixation targets.

#### 2.4.2 Huber Loss (Smooth L1 Loss)
To bound the influence of saccadic and blink outliers, the Huber loss provides a smooth transition from a quadratic penalty (for small errors) to a linear penalty (for large errors) controlled by threshold $\delta > 0$:

$$\mathcal{L}_{\text{Huber},\delta}(\mathbf{r}) = \frac{1}{N} \sum_{i=1}^N \left( \ell_\delta(r_{x,i}) + \ell_\delta(r_{y,i}) \right)$$

where:

$$\ell_\delta(r) = \begin{cases} \frac{1}{2} r^2 & \text{if } |r| \le \delta \\ \delta \left( |r| - \frac{1}{2} \delta \right) & \text{if } |r| > \delta \end{cases}$$

- **Gradient:**
  $$\frac{\partial \ell_\delta(r)}{\partial r} = \begin{cases} r & \text{if } |r| \le \delta \\ \delta \cdot \operatorname{sign}(r) & \text{if } |r| > \delta \end{cases}$$
- **Hyperparameter Standard for IntuiGaze:**  
  On a Full HD 1080p display ($1920\times 1080$), a typical fixation tolerance of $\sim 38$ pixels corresponds to $\delta = 0.02$ in normalized space ($0.02 \times 1920 \approx 38.4\text{ px}$).  
  Any tracking outlier with error exceeding $0.02$ produces a constant bounded gradient of $\pm 0.02$, preventing training explosions from sudden head jerks or eye blinks.

#### 2.4.3 Adaptive Wing (AWing) Loss for High-Precision Fixations
While Huber loss limits outlier gradients, its gradient approaches zero linearly as $|r| \to 0$ ($\frac{\partial \ell}{\partial r} = r$). For graphical user interfaces, however, sub-pixel fixation accuracy is paramount: reducing error from 20 px to 5 px is far more impactful for clicking a small button than reducing error from 400 px to 385 px during a rapid saccade.

Adaptive Wing Loss utilizes a logarithmic formulation that produces **steep gradients for small residuals** while maintaining linear gradients for large errors:

$$\mathcal{L}_{\text{Wing}}(r) = \begin{cases} \omega \ln\left( 1 + \left| \frac{r}{\epsilon} \right| \right) & \text{if } |r| < \omega \\ |r| - C & \text{if } |r| \ge \omega \end{cases}$$

where:

$$C = \omega - \omega \ln\left( 1 + \frac{\omega}{\epsilon} \right)$$

- **Gradient:**
  $$\frac{\partial \mathcal{L}_{\text{Wing}}}{\partial r} = \begin{cases} \frac{\omega}{\epsilon + |r|} \operatorname{sign}(r) & \text{if } |r| < \omega \\ \operatorname{sign}(r) & \text{if } |r| \ge \omega \end{cases}$$
- **Hyperparameter Standard:** Setting $\omega = 0.05$ and $\epsilon = 0.01$ ensures that fine fixation errors ($|r| < 0.01$) receive up to $5\times$ higher gradient force ($\frac{\omega}{\epsilon} = 5.0$) toward zero compared to Huber or MSE loss, directly eliminating the "slow drift" and residual bias commonly observed around UI button perimeters.

#### 2.4.4 Pinball Loss for Predictive Uncertainty & Confidence Estimation
To directly feed IntuiGaze's Layer 1 Safety Filter (Confidence Gating), the primary regression head can be trained via Quantile Regression using the Pinball loss.

Instead of predicting only the conditional expectation $\mathbb{E}[y|x]$, the network outputs three quantiles per coordinate: $\tau \in \{0.1, 0.5, 0.9\}$ (the 10th percentile lower bound $\hat{q}_{0.1}$, the median $\hat{q}_{0.5}$, and the 90th percentile upper bound $\hat{q}_{0.9}$).

The asymmetric Pinball loss for quantile $\tau \in (0, 1)$ is:

$$\mathcal{L}_{\tau}(r) = \max\left( \tau r, (\tau - 1) r \right) = r \left( \tau - \mathbb{I}(r < 0) \right)$$

where $r = y - \hat{q}_\tau$.

- **Runtime Uncertainty Output:**
  $$\text{Uncertainty}_x = \hat{q}_{0.9}(x) - \hat{q}_{0.1}(x), \quad \text{Uncertainty}_y = \hat{q}_{0.9}(y) - \hat{q}_{0.1}(y)$$
  $$\text{Confidence } C = \exp\left( -\frac{\sqrt{\text{Uncertainty}_x^2 + \text{Uncertainty}_y^2}}{\sigma_{\text{gate}}} \right) \in (0, 1]$$
  This formulation yields a principled, distribution-free confidence metric that automatically suppresses click gestures whenever gaze estimates become diffuse or uncertain.

---

### 2.5 Multi-Task Loss Formulation

When training unified or multi-branch architectures that simultaneously predict screen coordinates $\hat{\mathbf{s}}$, 3D gaze direction $\hat{\mathbf{d}}$, and temporal navigation intent $\hat{\mathbf{p}}$, the total objective function must balance heterogeneous task scales.

#### 2.5.1 Homoscedastic Uncertainty Weighting
Rather than relying on static heuristic hyperparameters ($\lambda_1, \lambda_2, \lambda_3$), IntuiGaze specifies homoscedastic uncertainty weighting (Kendall et al., CVPR 2018):

$$\mathcal{L}_{\text{multi}}(\boldsymbol{\theta}, \sigma_1, \sigma_2, \sigma_3) = \frac{1}{2\sigma_1^2} \mathcal{L}_{\text{coord}}(\mathbf{s}, \hat{\mathbf{s}}) + \frac{1}{2\sigma_2^2} \mathcal{L}_{\text{angular}}(\mathbf{d}, \hat{\mathbf{d}}) + \frac{1}{\sigma_3^2} \mathcal{L}_{\text{intent}}(\mathbf{c}, \hat{\mathbf{p}}) + \ln \sigma_1 + \ln \sigma_2 + \ln \sigma_3$$

where $\sigma_1, \sigma_2, \sigma_3 > 0$ are learnable observation noise scalars optimized via backpropagation alongside model parameters $\boldsymbol{\theta}$. This prevents the large angular loss from overwhelming fine coordinate regression or starving the sparse intent classifier.

---

## 3. Secondary Prediction Tasks

### 3.1 Task S1: 3D Gaze Direction Angular Regression

#### 3.1.1 3D Unit Vector Representation
Let $\mathbf{d} = (d_x, d_y, d_z)^T \in \mathbb{S}^2 \subset \mathbb{R}^3$ be the true gaze direction unit vector in camera optical Cartesian coordinates ($\|\mathbf{d}\|_2 = 1$).

- **Geodesic Angular Error Loss:**
  $$\mathcal{L}_{\text{angular}}(\mathbf{d}, \hat{\mathbf{d}}) = \frac{180^\circ}{\pi} \arccos\left( \frac{\mathbf{d}^T \hat{\mathbf{d}}}{\|\mathbf{d}\|_2 \|\hat{\mathbf{d}}\|_2 + \epsilon_{\text{stab}}} \right)$$
  where $\epsilon_{\text{stab}} = 10^{-7}$ prevents numerical instability when vectors are collinear.
- **Cosine Distance Surrogate Loss:**
  During early training epochs, $\arccos$ gradients can be unstable near collinearity ($\frac{d}{du}\arccos(u) = -\frac{1}{\sqrt{1-u^2}} \to \infty$ as $u \to 1$). Hence, the cosine proximity loss is utilized as an optimization surrogate:
  $$\mathcal{L}_{\text{cos}}(\mathbf{d}, \hat{\mathbf{d}}) = 1 - \frac{\mathbf{d}^T \hat{\mathbf{d}}}{\|\hat{\mathbf{d}}\|_2}$$

#### 3.1.2 Spherical Pitch-Yaw Representation
Gaze direction can be equivalently expressed in spherical pitch $\theta$ (elevation) and yaw $\phi$ (azimuth) in radians:

$$\mathbf{d} = \begin{pmatrix} -\cos \theta \sin \phi \\ -\sin \theta \\ -\cos \theta \cos \phi \end{pmatrix} \quad \Longleftrightarrow \quad \begin{cases} \theta = -\arcsin(d_y) \\ \phi = -\arctan2(d_x, -d_z) \end{cases}$$

#### 3.1.3 L2CS-Net Binned Classification with Soft-Argmax Expectation
To avoid the regression-to-the-mean problem (where mean-squared error smooths away sharp saccadic transitions), IntuiGaze aligns with L2CS-Net (`backend/eyenav/vision/gaze.py`):
1. Discretize pitch $\theta$ and yaw $\phi$ into $B = 90$ discrete bins covering $[-45^\circ, +45^\circ]$ (bin resolution $\Delta = 2.0^\circ$ or $1.0^\circ$).
2. The network outputs raw classification logits: $\mathbf{z}_{\text{pitch}} \in \mathbb{R}^{90}$ and $\mathbf{z}_{\text{yaw}} \in \mathbb{R}^{90}$.
3. Softmax probabilities: $p_b = \frac{e^{z_b}}{\sum_j e^{z_j}}$.
4. Continuous expectation via soft-argmax:
   $$\hat{\theta} = \sum_{b=1}^{90} \text{bin\_center}_b \cdot p_b(\text{pitch}), \quad \hat{\phi} = \sum_{b=1}^{90} \text{bin\_center}_b \cdot p_b(\text{yaw})$$
5. Shannon Entropy Confidence:
   $$H_{\text{norm}}(p) = -\frac{1}{\ln 90} \sum_{b=1}^{90} p_b \ln(p_b + \epsilon), \quad \text{Confidence } C = 1.0 - \frac{H_{\text{norm}}(p) + H_{\text{norm}}(q)}{2.0} \in [0, 1]$$

---

### 3.2 Task S2: 13-Class Temporal Intent Recognition

#### 3.2.1 Target Classes and Semantics (Matching `backend/eyenav/intent.py`)
IntuiGaze defines an explicit 13-class navigation intent catalog matching `INTENT_CLASSES` in `backend/eyenav/intent.py`:

| ID | Class Name | Interaction Semantics | Suggested OS Command | Safety Risk Level (`safety.py`) | Required Dwell Time |
|:--:|:-----------|:----------------------|:---------------------|:--------------------------------|:--------------------|
| 0 | `idle` | Passive resting state, baseline hover | `None` | `low_risk` | None |
| 1 | `reading` | Left-to-right progressive text scan | `None` (**Suppress all clicks**) | `low_risk` | None |
| 2 | `selecting` | Sustained fixation dwell on widget | `"select"` | `medium_risk` | $600\text{ ms}$ |
| 3 | `scrolling_up` | Smooth upward pursuit movement | `"scroll_up"` | `low_risk` | None ($300\text{ ms}$ cooldown) |
| 4 | `scrolling_down` | Smooth downward pursuit movement | `"scroll_down"` | `low_risk` | None ($300\text{ ms}$ cooldown) |
| 5 | `searching` | Rapid exploratory saccadic scanpath | `None` (**Suppress all clicks**) | `low_risk` | None |
| 6 | `activation` | Wake up / enable eye navigation | `"activate"` | `medium_risk` | $600\text{ ms}$ |
| 7 | `deactivation` | Sleep / pause eye navigation | `"deactivate"` | `medium_risk` | $600\text{ ms}$ |
| 8 | `confirmation` | Deliberate long blink or head nod | `"enter"` | `medium_risk` | $600\text{ ms}$ ($1500\text{ ms}$ cooldown) |
| 9 | `cancellation` | Escape gesture / look-away | `"escape"` | `medium_risk` | $600\text{ ms}$ |
| 10 | `nav_back` | Backward page navigation gesture | `"back"` | `medium_risk` | $600\text{ ms}$ ($1200\text{ ms}$ cooldown) |
| 11 | `nav_forward` | Forward page navigation gesture | `"forward"` | `medium_risk` | $600\text{ ms}$ ($1200\text{ ms}$ cooldown) |
| 12 | `nav_home` | Return to root dashboard interface | `"home"` | `high_risk` | $1200\text{ ms}$ |

#### 3.2.2 Temporal Buffer Architecture
The intent engine processes a rolling temporal sliding window:

$$\mathbf{X}_{\text{intent}} \in \mathbb{R}^{T \times F}$$

where:
- Temporal length $T = 45$ frames ($1.5$ seconds at $30\text{ FPS}$).
- Feature dimension $F = 32$ channels per frame, containing:
  - Screen coordinate velocity and acceleration: $(\dot{x}, \dot{y}, \ddot{x}, \ddot{y})$.
  - Iris displacement vectors and Eye Aspect Ratios: $(\text{EAR}_{\text{left}}, \text{EAR}_{\text{right}}, \Delta \text{EAR})$.
  - 3D Head pose angular velocities: $(\dot{\theta}_{\text{pitch}}, \dot{\phi}_{\text{yaw}}, \dot{\psi}_{\text{roll}})$.
  - Fixation dispersion and saccadic peak velocity indicators.

#### 3.2.3 Multi-Class Focal Loss for Severe Class Imbalance
In live user sessions, passive states (`idle`, `reading`, `searching`) account for $>88\%$ of all elapsed frames, whereas active command triggers (`selecting`, `activation`, `nav_home`) represent $<2\%$.

To prevent the classifier from collapsing into an all-idle majority predictor, model optimization uses Multi-Class Focal Loss with inverse-frequency class weighting:

$$\mathcal{L}_{\text{Focal}}(\mathbf{p}, \mathbf{y}) = -\sum_{c=0}^{12} \alpha_c (1 - p_c)^\gamma y_c \ln(p_c + \epsilon)$$

where:
- $\mathbf{y} \in \{0, 1\}^{13}$ is the one-hot ground truth vector.
- $p_c$ is the predicted softmax probability for class $c$.
- $\gamma = 2.0$ is the focusing parameter that down-weights easy passive negatives (`idle`).
- $\alpha_c = \frac{1}{\sqrt{\text{Frequency}(c)}}$ balances rare command event sensitivity.

---

## 4. Multimodal Feature Input Space & Latency Budget

### 4.1 Multimodal Ingestion Contract

IntuiGaze establishes an explicit, modular multimodal ingestion contract combining appearance patches and geometric landmark telemetry:

```
                            +-------------------------------+
                            |      Raw Input Webcam Frame   |
                            +---------------+---------------+
                                            |
                    +-----------------------+-----------------------+
                    |                       |                       |
                    v                       v                       v
            +---------------+       +---------------+       +---------------+
            |  MediaPipe    |       | Face Bounding |       | Eye Bounding  |
            | FaceLandmarker|       |      Box      |       |     Boxes     |
            +-------+-------+       +-------+-------+       +-------+-------+
                    |                       |                       |
                    v                       v                       v
            +---------------+       +---------------+       +---------------+
            | Landmarks L   |       | Face Crop I_F |       |Eye Crops I_L, |
            | (478 x 3)     |       | (224x224x3)   |       |I_R (128x128x3)|
            +-------+-------+       +-------+-------+       +-------+-------+
                    |                       |                       |
                    |                       v                       |
                    |               +---------------+               |
                    |               |Face Grid G    |               |
                    |               | (25 x 25)     |               |
                    |               +-------+-------+               |
                    |                       |                       |
                    v                       v                       v
            +---------------------------------------------------------------+
            |               Multimodal Fusion Concatenation                 |
            +-------------------------------+-------------------------------+
                                            |
                                            v
            +---------------------------------------------------------------+
            |     Primary Regressor & Auxiliary Heads (Inference <= 6 ms)   |
            +---------------------------------------------------------------+
```

### 4.2 Modality Processing Specifications

| Modality Name | Tensor Symbol | Data Type & Shape | Source / Extraction Pipeline | Preprocessing & Normalization |
|:---|:---:|:---:|:---|:---|
| **Left Eye Crop** | $\mathbf{I}_L$ | $\text{float32}, (3, 128, 128)$ | `appleLeftEye.json` or MediaPipe eye contour | Resized to $128\times 128$; ImageNet normalized ($\mu, \sigma$) |
| **Right Eye Crop** | $\mathbf{I}_R$ | $\text{float32}, (3, 128, 128)$ | `appleRightEye.json` or MediaPipe eye contour | Horizontally flipped for Siamese symmetry; ImageNet norm |
| **Face Crop** | $\mathbf{I}_F$ | $\text{float32}, (3, 224, 224)$ | `appleFace.json` or MediaPipe face bbox | Resized to $224\times 224$; ImageNet normalized ($\mu, \sigma$) |
| **Binary Face Grid** | $\mathbf{G}$ | $\text{float32}, (1, 25, 25)$ | `faceGrid.json` or computed from face box | Flattened to $625$-D binary vector $\in \{0, 1\}^{625}$ |
| **Facial Landmarks** | $\mathbf{L}$ | $\text{float32}, (478, 3)$ | MediaPipe FaceLandmarker (`face_landmarker.task`)| Normalized to $[0, 1]$ image space; centered on nose bridge |

#### 4.2.1 Siamese Eye Feature Sharing
To halve the parameter count and memory footprint of the convolutional eye backbone:
- The right eye patch $\mathbf{I}_R$ is mirrored horizontally:
  $$\tilde{\mathbf{I}}_R(c, y, x) = \mathbf{I}_R(c, y, W_{\text{crop}} - 1 - x)$$
- Both $\mathbf{I}_L$ and $\tilde{\mathbf{I}}_R$ pass through an identical weight-shared convolutional backbone (MobileNetV3-Small), producing bilateral eye embeddings $\mathbf{e}_L, \mathbf{e}_R \in \mathbb{R}^{128}$.

#### 4.2.2 Binary Face Grid Encoding
The $25 \times 25$ binary face grid preserves face scale and camera-relative displacement without requiring full-resolution frame processing:
1. Divide the camera sensor resolution into a uniform grid of $25 \times 25$ cells.
2. Given face bounding box $[x_{\min}, y_{\min}, w, h]$ normalized to $[0, 1]$:
   $$G_{u, v} = \begin{cases} 1 & \text{if cell }(u, v)\text{ intersects face bounding box} \\ 0 & \text{otherwise} \end{cases}$$
3. $\mathbf{G}$ passes through a 2-layer MLP ($625 \to 128 \to 64$), outputting spatial feature vector $\mathbf{e}_G \in \mathbb{R}^{64}$.

#### 4.2.3 3D Facial Landmarks (`face_landmarker.task`)
MediaPipe FaceLandmarker extracts 478 3D points. Essential sub-features utilized for lightweight geometric regression include:
- Left Iris Center: Index 468 $(x_{468}, y_{468}, z_{468})$.
- Right Iris Center: Index 473 $(x_{473}, y_{473}, z_{473})$.
- Left Eye Contour: Indices $[33, 160, 158, 133, 153, 144]$.
- Right Eye Contour: Indices $[362, 385, 387, 263, 373, 380]$.
- Head Pose: 3D rotation angles $(\theta_{\text{pitch}}, \phi_{\text{yaw}}, \psi_{\text{roll}})$ derived from the facial transformation matrix.

---

### 4.3 Real-Time CPU Latency Budget

To deliver responsive computer interaction, total end-to-end latency from webcam sensor photon capture to OS cursor update must not exceed $33.33\text{ ms}$ ($\ge 30\text{ FPS}$) and targets $16.67\text{ ms}$ ($60\text{ FPS}$).

On reference commodity consumer hardware (quad-core Intel Core i5-8250U / AMD Ryzen 5, 1.6 GHz base without discrete GPU), the computational budget is allocated as follows:

```
+--------------------------------------------------------------------------------------------------+
|                            Per-Frame Real-Time Latency Budget (Total <= 10.0 ms)                 |
|                                                                                                  |
|   Webcam Frame       MediaPipe Face      Feature Crop       ML Inference Head   Safety Filter,   |
|   Capture & Preproc  Landmarker Task     & Normalization    (ONNX Runtime CPU)  One-Euro & OS    |
|                                                                                                  |
|   [  <= 1.5 ms  ] -> [  <= 4.0 ms  ] -> [  <= 1.0 ms  ] -> [   <= 6.0 ms   ] -> [  <= 1.0 ms  ]  |
|                                                                                                  |
|   Total Frame Pipeline Latency: <= 10.0 ms                                                       |
|   Available Headroom before 30 FPS deadline (33.3 ms): 23.33 ms (70.0% safety buffer)           |
+--------------------------------------------------------------------------------------------------+
```

| Pipeline Stage | Module / Function | Target Latency | Maximum Allowed Budget | Execution Context |
|:---|:---|:---:|:---:|:---|
| **1. Frame Acquisition** | OpenCV capture, BGR $\to$ RGB conversion | $1.0\text{ ms}$ | $1.5\text{ ms}$ | OpenCV native USB capture |
| **2. Landmark Detection** | MediaPipe FaceLandmarker Tasks API (478 pts) | $3.5\text{ ms}$ | $4.0\text{ ms}$ | MediaPipe C++ XNNPACK (4 threads) |
| **3. Feature Extraction** | Eye/Face crop + normalization, FaceGrid | $0.8\text{ ms}$ | $1.0\text{ ms}$ | NumPy / SIMD accelerated |
| **4. ML Model Inference** | Primary Regressor ($f_{\boldsymbol{\theta}}$) + S1/S2 Heads | **$4.0\text{ ms}$** | **$\le 6.0\text{ ms}$** | ONNX Runtime CPUExecutionProvider |
| **5. Post-Processing** | One-Euro filter + SafetyFilter + Clamping | $0.5\text{ ms}$ | $1.0\text{ ms}$ | Algorithmic Python / C-types |
| **Total Pipeline** | **End-to-End Frame-to-Cursor Processing** | **$9.8\text{ ms}$** | **$\le 10.0\text{ ms}$** | **Sustained $\ge 30\text{ FPS}$ (Target $60\text{ FPS}$)** |

---

## 5. Comprehensive Evaluation Metrics & Error Distribution Policy

In strict adherence to [`AGENTS.md`](../../AGENTS.md) and [`docs/ml/METRICS_POLICY.md`](METRICS_POLICY.md), IntuiGaze explicitly prohibits evaluating or ranking candidate models based on a single composite "accuracy" or mean error value. A model with an acceptable mean error can still cause violent cursor jumps or accidental clicks.

### 5.1 Continuous Regression Metrics

For predicted normalized coordinate $\hat{\mathbf{s}}_i = (\hat{x}_{\text{norm},i}, \hat{y}_{\text{norm},i})$ and ground truth target $\mathbf{s}_i = (x_{\text{norm},i}, y_{\text{norm},i})$ across evaluation samples $i \in \{1, \dots, N\}$:

#### 5.1.1 Euclidean Distance Error
1. **Physical Screen Pixels ($e_{\text{px}}$):**
   $$e_{\text{px}, i} = \sqrt{\left((\hat{x}_{\text{norm},i} - x_{\text{norm},i}) \cdot W_{\text{screen}}\right)^2 + \left((\hat{y}_{\text{norm},i} - y_{\text{norm},i}) \cdot H_{\text{screen}}\right)^2}$$
   Must be reported at both:
   - **Reference Resolution:** Full HD 1080p ($W_{\text{ref}} = 1920, H_{\text{ref}} = 1080$, 24-inch monitor, pixel pitch $p = 0.2767\text{ mm}$).
   - **Native Device Resolution:** Device points/pixels recorded in `screen.json`.
2. **Normalized Screen Diagonal Error ($e_{\text{diag}}$):**
   $$e_{\text{diag}, i} = \frac{e_{\text{px}, i}}{\sqrt{W_{\text{screen}}^2 + H_{\text{screen}}^2}} \in [0, 1]$$
   Reported as a percentage of the screen diagonal ($\% D$).

#### 5.1.2 Component Mean Absolute Error ($MAE_x$ and $MAE_y$)
Due to anatomical differences between lateral rectus muscles (horizontal) and superior/inferior rectus muscles (vertical eyelid occlusion), horizontal and vertical tracking exhibit significant anisotropy:
$$MAE_x = \frac{1}{N} \sum_{i=1}^N |\hat{x}_i - x_i|, \quad MAE_y = \frac{1}{N} \sum_{i=1}^N |\hat{y}_i - y_i|$$
Both components must be reported separately in pixels and normalized coordinates.

#### 5.1.3 Robust Distributional Statistics
Because gaze errors follow heavy-tailed, non-Gaussian distributions, candidate evaluations must report the complete error spectrum:
- **Median ($P50$):** Typical user experience, invariant to blink spikes.
- **Mean ($P_{\text{mean}}$):** Classical benchmark reference.
- **90th Percentile ($P90$):** Operational interaction threshold.
- **95th Percentile ($P95$):** Tail risk excursion boundary.
- **Maximum Error ($e_{\max}$):** Worst-case catastrophic tracking glitch.
- **Interquartile Range ($IQR = P75 - P25$):** Core dispersion measure.

---

### 5.2 Predeclared Target Hit Rates

Under Fitts' Law, interactive UI widget acquisition succeeds if the cursor enters the target's interactive bounding area. IntuiGaze pre-declares three operational hit rate thresholds referenced to Full HD 1080p:

$$Hit@R = \frac{1}{N} \sum_{i=1}^N \mathbb{I}(e_{\text{px}, i} \le R) \times 100\%$$

| Target Metric | Radius $R$ (px @ 1080p) | Physical Metric Radius (mm) | UI Target Analog & Usability Rationale | Minimum Release Target |
|:---|:---:|:---:|:---|:---:|
| **$Hit@25\text{px}$** | $25\text{ px}$ | $6.9\text{ mm}$ | Fine UI icons, radio buttons, window close/minimize buttons ($24\text{--}32\text{ px}$) | $\ge 40\%$ (with fixation deadzone) |
| **$Hit@50\text{px}$** | $50\text{ px}$ | $13.8\text{ mm}$ | Accessible touch/click buttons, toolbar controls ($48\text{--}64\text{ px}$) | $\ge 70\%$ |
| **$Hit@100\text{px}$** | $100\text{ px}$ | $27.7\text{ mm}$ | Coarse accessibility cards, on-screen virtual keyboard keys ($96\text{--}128\text{ px}$) | $\ge 90\%$ |

*Architectural Invariant Link:* In `backend/eyenav/cursor/controller.py`, line 54 establishes `_FIXATION_DEADZONE_PX = 45.0`. When the user fixates within $45\text{ px}$ of an anchor, the cursor enters gravity lock, directly converting $Hit@50\text{px}$ accuracy into stable target acquisition.

---

### 5.3 Angular Gaze Error Conversion

To enable scientific comparison with academic computer vision benchmarks (MPIIGaze, ETH-XGaze, Gaze360), screen pixel displacement is converted to visual angle error in degrees ($\theta^\circ$).

#### 5.3.1 Trigonometric Formulation
Let $D$ be the user viewing distance from the display surface in centimeters ($D = 60.0\text{ cm}$ standard desktop default).  
Let $d_{\text{cm}}$ be the physical metric displacement on the screen:

$$d_{\text{cm}} = e_{\text{px}} \cdot p_{\text{cm}} = e_{\text{px}} \cdot \frac{W_{\text{cm}}}{W_{\text{px}}}$$

For a 24-inch 1080p display ($W_{\text{cm}} = 53.13\text{ cm}, W_{\text{px}} = 1920$), pixel pitch $p_{\text{cm}} \approx 0.02767\text{ cm/px}$.

The visual angle error $\theta_{\text{deg}}$ is computed as:

$$\theta_{\text{deg}} = \arctan\left(\frac{d_{\text{cm}}}{D}\right) \cdot \frac{180^\circ}{\pi} \approx \frac{e_{\text{px}} \cdot p_{\text{cm}}}{D} \cdot \frac{180^\circ}{\pi}$$

#### 5.3.2 Reference Equivalence Lookup Table (at $D = 60.0\text{ cm}$, 1080p 24")
| Visual Angle ($\theta^\circ$) | Metric Error ($d_{\text{cm}}$) | Pixel Error ($e_{\text{px}}$ @ 1080p) | Normalized Diagonal ($\% D$) | Operational Context |
|:---:|:---:|:---:|:---:|:---|
| **$0.5^\circ$** | $0.52\text{ cm}$ | $18.9\text{ px}$ | $0.86\%$ | Dedicated infrared hardware eye-tracker (Tobii Eye Tracker 5) |
| **$1.0^\circ$** | $1.05\text{ cm}$ | $37.8\text{ px}$ | $1.72\%$ | High-quality personalized 9-point calibrated `GazeScreenMapper` |
| **$1.5^\circ$** | $1.57\text{ cm}$ | $56.8\text{ px}$ | $2.58\%$ | Target calibrated accuracy for IntuiGaze polynomial pipeline |
| **$2.5^\circ$** | $2.62\text{ cm}$ | $94.7\text{ px}$ | $4.30\%$ | Uncalibrated SOTA deep webcam gaze (L2CS-Net / ETH-XGaze) |
| **$3.5^\circ$** | $3.67\text{ cm}$ | $132.6\text{ px}$ | $6.02\%$ | Generic baseline webcam model without personal calibration |
| **$5.0^\circ$** | $5.25\text{ cm}$ | $189.7\text{ px}$ | $8.61\%$ | Trivial center dummy baseline / degraded lighting condition |

---

### 5.4 Intent Classification & Temporal Event Metrics

1. **Prohibition of Raw Accuracy:** Global classification accuracy $\frac{\sum TP}{N}$ is **strictly banned** as a primary evaluation metric because passive classes (`idle`, `reading`) dominate $>88\%$ of frames.
2. **Mandatory Metrics:**
   - Per-class Precision ($P_c$), Recall ($R_c$), and F1-Score ($F1_c$).
   - Macro-Averaged F1: $\text{Macro-F1} = \frac{1}{13} \sum_{c=0}^{12} F1_c$.
   - Balanced Accuracy: $\text{Balanced-Acc} = \frac{1}{13} \sum_{c=0}^{12} R_c$.
   - PR-AUC for sparse command classes ($c \in \{2, 6, 7, 8, 9, 10, 11, 12\}$).
3. **Confusion Matrix Critical Danger Zones:**
   - Reading Misclassified as Select ($M_{\text{reading}, \text{selecting}}$): **Safety Gate $\le 0.1\%$**.
   - Searching Misclassified as Select ($M_{\text{searching}, \text{selecting}}$): **Safety Gate $\le 0.1\%$**.
   - Reading Misclassified as Home ($M_{\text{reading}, \text{nav\_home}}$): **Safety Gate $0.0\%$**.
4. **Temporal Event Matching & False Trigger Rates:**
   - Event Matching Window: $\Delta t_{\text{match}} = 200\text{ ms}$.
   - Dwell Timing Latency: $650\text{ ms} \pm 50\text{ ms}$ (standard deviation $\sigma_{\text{dwell}} \le 30\text{ ms}$).
   - High-Risk False Trigger Rate: $\text{FTR}_{\text{high-risk}} < 1.0\text{ event / hour}$ of continuous reading.
   - Accidental Double-Blink Click Rate: $< 0.5\text{ false clicks / 10 minutes}$ of natural reading.

---

### 5.5 Operational Safety Criteria & Failure Modes

```
+--------------------------------------------------------------------------------------------------+
|                                    Operational Safety Matrix                                     |
|                                                                                                  |
|   1. Gaze Tracking Loss (Occlusion / Head Pose > 35 deg / Low SNR / High Entropy H > 0.60):      |
|      * Cursor Invariant: FREEZE instantly at last confirmed coordinates (NO jump to center)      |
|      * Click Invariant: ALL commands immediately BLOCKED (Fail-Closed)                           |
|      * Reacquisition: Reset One-Euro and Saccade filters on face recovery (latency <= 150 ms)    |
|                                                                                                  |
|   2. Anomalous Jump Suppression:                                                                 |
|      * Inter-frame displacement Delta d_t > 250 px outside saccade state clamped as ANOMALY      |
|      * Anomalous Jump Rate requirement: AJR <= 0.05% (<= 1 jump per 2,000 frames)                |
|                                                                                                  |
|   3. Stale Frame Pipeline Discard:                                                               |
|      * Capture age (t_now - t_capture) > 50.0 ms -> Frame DISCARDED unconditionally              |
|      * >= 3 consecutive stale frames -> Cursor FREEZE + amber UI warning indicator               |
|                                                                                                  |
|   4. Physical Mouse Priority Override:                                                           |
|      * Physical mouse moved >= 15 px -> Immediate 2.0 s eye tracking pause                       |
|                                                                                                  |
|   5. Emergency Stop Failsafe:                                                                    |
|      * 3.0 s sustained eye closure (EAR < 0.15) -> EMERGENCY_STOP engages, blocking all actions  |
+--------------------------------------------------------------------------------------------------+
```

---

### 5.6 Statistical Significance & Disaggregated Slice Evaluation

1. **Subject-Level Macro-Averaging (Zero Leakage):**
   Test set metrics must be evaluated independently per participant across the $S = 26$ test subjects, reporting the macro-mean, median, and inter-subject variance:
   $$\bar{M}_{\text{macro}} = \frac{1}{26} \sum_{s=1}^{26} M_s, \quad \text{Median}_{\text{macro}} = \operatorname{median}(\{M_1, \dots, M_{26}\})$$
2. **Paired Wilcoxon Signed-Rank Test:**
   Because error distributions are non-Gaussian, statistical superiority of candidate models over baselines is verified via the two-sided Wilcoxon signed-rank test on per-subject median errors ($p < 0.01$, candidate superior in $\ge 18$ of 26 subjects).
3. **Bootstrap Confidence Intervals:**
   Report 95% Confidence Intervals derived via non-parametric subject-level bootstrapping with $B = 10,000$ iterations.
4. **Disaggregated Sub-Population Slices:**
   - **Orientation Slices:** Orientation 1 (Portrait), 2 (Portrait Upside Down), 3 (Landscape Right), 4 (Landscape Left).
   - **Device Form Factor Slices:** Phone (iPhone) vs Tablet (iPad).
   - **Gaze Eccentricity Slices:** Foveal Center ($\le 20\% D$), Mid-Field ($20\%\text{--}40\% D$), Extreme Periphery ($> 40\% D$).

---

## 6. Baseline Model Progression Hierarchy

In compliance with [`AGENTS.md`](../../AGENTS.md) and the `experiment-management` methodology, complex neural models must never be evaluated in isolation. An honest benchmark requires a disciplined four-tier progression where each level establishes a strict justification hurdle for subsequent models.

```
+-----------------------------------------------------------------------------------+
|                           BASELINE MODEL HIERARCHY                                |
+-----------------------------------------------------------------------------------+
|  Level 3: Deep Neural Network / Appearance CNN (L2CS-Net / iTracker)              |
|           Inputs: Face/Eye RGB Patches (224x224) + FaceGrid (25x25)               |
|           Latency: ~4.0-6.0 ms CPU | SOTA uncalibrated gaze tracking              |
+-----------------------------------------------------------------------------------+
                                         ^
|  Level 2: Non-Linear Tabular Regressor (Random Forest / GBDT)                     |
|           Inputs: 24D engineered facial/pupil landmarks + 3D head pose            |
|           Latency: ~1.0-2.0 ms CPU | Robust non-linear interaction modeling       |
+-----------------------------------------------------------------------------------+
                                         ^
|  Level 1: Polynomial Ridge Regression / Linear Mapper (GazeScreenMapper)          |
|           Inputs: Degree-2 polynomial expansion of 6D iris/pose features          |
|           Latency: <0.05 ms CPU | Closed-form O(1) online adaptation              |
+-----------------------------------------------------------------------------------+
                                         ^
|  Level 0: Trivial Center Dummy Baseline                                           |
|           Outputs: Static Screen Center (0.5, 0.5) or Empirical Training Mean     |
|           Latency: 0 ms CPU | Theoretical error floor and sanity gate             |
+-----------------------------------------------------------------------------------+
```

### 6.1 Level 0: Trivial Center Dummy Baseline
- **Formulation:** Predicts constant screen center $\hat{\mathbf{s}}_{\text{center}} = (0.5, 0.5)^T$, or the empirical training mean $\hat{\mathbf{s}}_{\text{mean}} = \frac{1}{N_{\text{train}}}\sum \mathbf{s}_i$.
- **Scientific Purpose:** Human computer users exhibit pronounced **central fixation bias**. Level 0 establishes the theoretical error floor (~0.22–0.28 normalized diagonal error). Any candidate model that fails to outperform Level 0 by $\ge 30\%$ error reduction is rejected as failing to learn gaze mechanics.
- **Complexity:** 0 parameters, $<0.001\text{ ms}$ latency.

### 6.2 Level 1: Polynomial Ridge Regression Mapper
- **Formulation:** Directly aligns with `backend/eyenav/cursor/mapping.py` (`GazeScreenMapper`).
- **Input Feature Vector:** $\mathbf{x} = [p_{lx}, p_{ly}, p_{rx}, p_{ry}, \theta_{\text{yaw}}, \theta_{\text{pitch}}]^T \in \mathbb{R}^6$ from MediaPipe iris landmarks (468, 473) and head pose.
- **Polynomial Expansion:** Degree-2 quadratic expansion $\Phi(\mathbf{x}) \in \mathbb{R}^{28}$ capturing eyeball curvature and perspective projection.
- **Closed-Form Ridge Fit:**
  $$\mathbf{W}^* = \left(\Phi(\mathbf{X})^T \Phi(\mathbf{X}) + \lambda \mathbf{I}\right)^{-1} \Phi(\mathbf{X})^T \mathbf{Y}, \quad \lambda = 10^{-4}$$
- **Online Rank-1 Personal Adaptation:** Updates via Sherman-Morrison rank-1 update on verified user clicks without full matrix reinversion:
  $$\mathbf{A}_{t+1}^{-1} = \mathbf{A}_t^{-1} - \frac{\mathbf{A}_t^{-1} \mathbf{u}_t \mathbf{u}_t^T \mathbf{A}_t^{-1}}{1 + \mathbf{u}_t^T \mathbf{A}_t^{-1} \mathbf{u}_t}$$
- **Complexity:** 56 parameters, $<0.05\text{ ms}$ latency on CPU.

### 6.3 Level 2: Random Forest / GBDT Tabular Regressor
- **Formulation:** Aligns with `scripts/train_calibration_model.py`. Fits non-linear ensemble trees over 24 engineered geometric features (relative pupil-to-canthus ratios $u_L, v_L$, Eye Aspect Ratio $\text{EAR}$, interpupillary distance $\text{IPD}$, bounding box ratios, and 25×25 FaceGrid centroid).
- **Ensemble Configuration:** `RandomForestRegressor(n_estimators=150, max_depth=20, min_samples_split=5, max_features='sqrt')`.
- **Complexity:** ~1.5M nodes, ~1.5 ms latency on multi-threaded CPU.

### 6.4 Level 3: Deep Appearance CNN
- **Formulation:** End-to-end appearance models learning directly from face and eye image patches.
  - **Candidate A (iTracker / MIT GazeCapture Native):** Convolutional towers for $\mathbf{I}_L, \mathbf{I}_R (128\times 128)$, $\mathbf{I}_F (224\times 224)$, and FaceGrid $\mathbf{G} (25\times 25)$, fused into a 128-D linear regression head.
  - **Candidate B (L2CS-Net MobileNetV3 / `gaze.py`):** Pretrained MobileNetV3-Large backbone (~3.2M parameters) predicting 90-bin pitch and yaw soft-argmax expectations.
- **Complexity:** ~3.2M to 12M parameters, $4.0\text{--}6.0\text{ ms}$ inference latency on CPU using ONNX Runtime.

### 6.5 Baseline Hierarchy Comparison Matrix

| Level | Model Architecture | Primary Inputs | Parameters | Inference Latency (CPU) | Primary Role in ML Lifecycle |
|:---:|:---|:---|:---:|:---:|:---|
| **Level 0** | Trivial Center Dummy | None / Constant | 0 – 2 | $< 0.001\text{ ms}$ | Theoretical floor & sanity check |
| **Level 1** | Polynomial Ridge Mapper | 6D Iris + Head Pose | 14 – 56 | $< 0.05\text{ ms}$ | Real-time personal calibration baseline |
| **Level 2** | Random Forest / GBDT | 24D Engineered Landmarks | ~1.5M | ~1.5 ms | Tabular non-linear feature baseline |
| **Level 3** | L2CS-Net / iTracker CNN | 224×224 Face/Eyes + FaceGrid | ~3.2M – 12M | $4.0\text{--}6.0\text{ ms}$ | Appearance-based SOTA candidate |

---

## 7. Dataset Partitioning, Archive Invariants & Leakage Prevention

### 7.1 Native MIT GazeCapture Partition Inventory

The dataset stored in `archive.zip` contains 263 unique participants. The native partitioning stored in each participant's `info.json` (`Dataset` attribute) must be strictly maintained as the authoritative split:

| Partition Name | Participant Count (`subject_id`) | Total Video Frames | Share of Total Frames | Role in ML Lifecycle |
|:---|:---:|:---:|:---:|:---|
| **`train`** | **230 subjects** | 289,591 frames | 82.89% | Feature extraction, representation learning, parameter optimization |
| **`val`** | **7 subjects** | 13,340 frames | 3.82% | Hyperparameter tuning, early stopping, model architecture selection |
| **`test`** | **26 subjects** | 46,438 frames | 13.29% | **Cryptographically sealed** final release benchmark |
| **Total** | **263 subjects** | **349,369 frames** | **100.00%** | Comprehensive multi-device gaze corpus |

### 7.2 The Zero-Leakage Grouping Invariant

The most vital scientific constraint in gaze estimation is **Participant-Group Isolation**:

$$\mathcal{S}_{\text{train}} \cap \mathcal{S}_{\text{val}} = \emptyset, \quad \mathcal{S}_{\text{train}} \cap \mathcal{S}_{\text{test}} = \emptyset, \quad \mathcal{S}_{\text{val}} \cap \mathcal{S}_{\text{test}} = \emptyset$$

where $\mathcal{S}$ denotes the set of unique participant directory IDs (`subject_id`).

#### Why Random Splitting is Catastrophic (The Biometric Memorization Trap)
In MIT GazeCapture, participants recorded sequential video clips (~30 FPS) following a moving target. Adjacent video frames ($t$ and $t+1$) possess virtually identical facial bone geometry, iris pigmentation, sclera vascular patterns, room lighting, and camera optical noise.

If frames are randomly shuffled across splits (`train_test_split(shuffle=True)`), the model memorizes subject identity rather than learning generalized gaze mechanics. This creates deceptively inflated test metrics (>98% Hit@25px) that collapse to worse than Level 0 when tested on a new user. **All cross-validation must use `GroupKFold` grouped strictly by `subject_id`.**

### 7.3 Cryptographic Test Set Sealing Protocol
To prevent subtle test-set overfitting and metric contamination:
1. `datasets/inav_gaze/manifests/test_manifest.csv` is cryptographically sealed with a SHA-256 hash.
2. During pipeline development, feature engineering, loss ablations, and checkpoint selection, **no script or agent is permitted to evaluate on the test partition**.
3. The test set is evaluated exactly **once**, only when the candidate model weights and decision thresholds are frozen for release.
4. Evaluation runs must log the Git commit hash, model weights SHA-256 hash, and preprocessing configuration hash.

### 7.4 `archive.zip` Integrity & Safe In-Memory Pipeline
- **File Path:** `c:\Users\Voriganti\Downloads\INAV\archive.zip`
- **File Size:** Exactly `21,616,790,160` bytes (20.132 GB decimal).
- **SHA-256 Checksum:** `48d2175ad792f82c2cea7df4d5763c4dc2bb781c3133c32b668ace251814d2c7`.
- **Preservation Invariant:** The archive must remain untouched on disk and **never uncompressed in bulk**. Uncompressing 348,643 individual JPEG files would consume >21.4 GB, risk exhausting Windows NTFS Master File Table (MFT) records, and trigger file-locking slowdowns.
- **Safe In-Memory Extraction Pipeline:**
  All tabular metadata lives in the **2,362 `.json` files** (totaling only 1.761 GB uncompressed). The data pipeline streams these JSON files directly into memory:
  ```python
  with zipfile.ZipFile("archive.zip", "r") as zf:
      with zf.open(f"{subject_id}/{subject_id}/dotInfo.json") as handle:
          dot_info = json.load(handle)
  ```
  The pipeline extracts and joins metadata row-by-row into structured CSV manifests (`archive_manifest.csv`, `train_manifest.csv`, `val_manifest.csv`, `test_manifest.csv`). Image frames are read on demand during training via streaming zip byte offsets.

### 7.5 Four-Point Data Quality Filtering Criteria

Raw crowdsourced mobile data contains tracking dropouts, blinks, and out-of-bounds stimulus artifacts. The data pipeline must enforce four deterministic quality filters:

1. **Face Detection Validity Filter:**
   - Condition: `appleFace.IsValid == 1`.
   - Rejection Rate: ~5.94% of frames.
   - Discards frames where the user looked away or lighting was insufficient for face localization.
2. **Eye Visibility Filter:**
   - Condition: `appleLeftEye.IsValid == 1 AND appleRightEye.IsValid == 1`.
   - Rejection Rate: ~31.63% of frames.
   - Eliminates natural blinks, heavy eyelid ptosis, squinting, and occlusion from glasses frames.
3. **Screen Bounding Box Sanity Filter:**
   - Condition: $0.0 \le \text{XPts} \le W_{\text{screen}}$ and $0.0 \le \text{YPts} \le H_{\text{screen}}$ ($x_{\text{norm}}, y_{\text{norm}} \in [0.0, 1.0]$).
   - Eliminates off-screen stimulus transition artifacts.
4. **Bounding Box Geometric Sanity Filter:**
   - Condition: $W_{\text{face}} > 0, H_{\text{face}} > 0, W_{\text{eye}} > 0, H_{\text{eye}} > 0$. Eye bounding boxes must be geometrically bounded within the face bounding box.

---

## 8. Safety, Privacy & Ethical Compliance

### 8.1 100% On-Device Execution & Ephemeral Frame Lifecycle

In compliance with [`docs/business/ETHICS.md`](../business/ETHICS.md), eye movement patterns reveal sensitive cognitive, medical, and psychological telemetry (reading comprehension, fatigue, neurological indicators):

1. **Strict Local Processing:** 100% of landmark extraction, gaze estimation, polynomial mapping, and intent classification must execute locally on the user's host CPU. Zero network transmission of webcam frames, crops, landmark coordinates, or gaze trajectories is permitted.
2. **Ephemeral In-Memory Frame Lifecycle:** Video frames captured from the webcam live in volatile memory strictly for the duration of the per-frame inference pass (<20 ms). Once landmarks and gaze coordinates are computed, raw image buffers are immediately overwritten and garbage collected. No video frames are written to disk.
3. **Local Profile Storage:** Calibration profiles (`~/.eyenav/gaze_calibration.json`) store only abstract regression coefficients ($\mathbf{W} \in \mathbb{R}^{28 \times 2}$), never facial imagery or personal identifiers.

### 8.2 Opt-In Actuation & Visual State Transparency
1. **Default Dormant State:** Upon application startup, desktop cursor actuation is **disabled by default**. Actuation requires explicit user opt-in via a UI toggle or keyboard shortcut.
2. **Persistent Visual HUD Indicator:** When gaze tracking is active, an on-screen HUD displays:
   - Tracking State (Green: Calibrated / Yellow: Low Confidence / Red: Paused).
   - Interaction Mode (Cursor Navigation vs Scroll Mode).
   - Real-time tracking confidence ($C \in [0, 1]$).

### 8.3 Physical Mouse Priority Override
Motor control of the operating system must never be irrevocably ceded to gaze tracking. As enforced in `backend/eyenav/cursor/controller.py` (lines 52–53, 143–155):
- If the user moves the physical mouse or trackpad by more than `_PHYSICAL_OVERRIDE_PX = 15` pixels, eye tracking immediately pauses for `_PHYSICAL_PAUSE_S = 2.0` seconds.
- The user can instantly seize control by touching the physical mouse.

### 8.4 Six-Layer Command Safety Filter & Fail-Closed Policy

Every command generated by the intent engine must pass all six verification layers in `backend/eyenav/safety.py`:

```
+-----------------------------------------------------------------------------------+
|                        SIX-LAYER COMMAND SAFETY VERIFICATION                      |
+-----------------------------------------------------------------------------------+
|  Layer 6: Emergency Stop (3s sustained eye closure immediately halts actuation)   |
+-----------------------------------------------------------------------------------+
|  Layer 5: Anti-Pattern Detection (blocks triggers during saccades / reading)      |
+-----------------------------------------------------------------------------------+
|  Layer 4: Dwell Confirmation (high-risk clicks require sustained visual dwell)    |
+-----------------------------------------------------------------------------------+
|  Layer 3: Context Validation (verifies command compatibility with active window)   |
+-----------------------------------------------------------------------------------+
|  Layer 2: Cooldown Rate Limiter (inter-command spacing >= 1.0s)                   |
+-----------------------------------------------------------------------------------+
|  Layer 1: Confidence Threshold Gate (rejects predictions below confidence thresh) |
+-----------------------------------------------------------------------------------+
                                         |
                                FAIL-CLOSED POLICY
            (Any internal error or exception immediately blocks command execution)
```

- **Fail-Closed Default:** If any safety check encounters an unhandled exception or tracking dropout, the filter defaults to `VerifiedCommand(blocked=True, block_reason=BlockReason.SAFETY_FILTER_ERROR)`. Spurious clicks are never emitted under failure conditions.
- **Emergency Stop:** 3.0 seconds of sustained eye closure ($\text{EAR} < 0.15$) immediately engages Layer 6 `EMERGENCY_STOP`, freezing cursor motion and command emission until manually re-enabled.

### 8.5 Disability Rights & Anti-Surveillance Ethics
1. **Demographic Equity:** Gaze models must not degrade for specific demographic groups. Stratified evaluations across device types and participant demographics must verify that no subgroup underperforms the overall mean by $>5\%$.
2. **Anti-Surveillance Architecture:** The codebase strictly omits attention harvesting, worker productivity monitoring, or covert telemetry APIs.
3. **User Autonomy:** All filtering parameters (deadzone thresholds, dwell timings, smoothing factors) are user-configurable, rejecting paternalistic software lock-in.

---

## 9. Model Promotion & Release Verification Gate

Before any trained machine learning model checkpoint or mapping configuration can be registered into `backend/eyenav/models/` or enabled in the live application pipeline, it must pass all **eight binary promotion gates**:

| # | Gate Identifier | Verification Criteria | Evaluation Mandate | Pass/Fail |
|:---:|:---|:---|:---|:---:|
| **1** | **Zero Participant Leakage** | 0 frames or subjects from the 26-subject test set appeared in training/validation splits or preprocessing fits. | Subject ID intersection check ($\mathcal{S}_{\text{train}} \cap \mathcal{S}_{\text{test}} = \emptyset$) | [ ] |
| **2** | **Latency Budget Compliance** | 95th percentile inference latency $\le 6.0\text{ ms}$ on reference CPU ($\le 10.0\text{ ms}$ total per-frame pipeline; $\ge 30\text{ FPS}$ sustained). | Benchmark on quad-core Intel Core i5 / AMD Ryzen 5 | [ ] |
| **3** | **Catastrophic Error Ceiling** | P95 Euclidean distance error $\le 180\text{ px}$ on 1080p reference display across the sealed 26-subject test set. | Subject-macro evaluation on test manifest | [ ] |
| **4** | **Reading Command Suppression** | False command activation rate during continuous reading patterns $\le 1.0\text{ event / hour}$ ($M_{\text{reading}, \text{selecting}} \le 0.1\%$). | Synthetic reading scanpath simulation | [ ] |
| **5** | **Fail-Closed Confidence Gate** | Frames with tracking confidence $C < 0.85$ produce `VerifiedCommand(blocked=True)` with zero click emission. | Verification unit tests on `SafetyFilter` | [ ] |
| **6** | **Emergency Stop Integrity** | 3.0-second continuous eye closure triggers `EMERGENCY_STOP` with $100\%$ reliability across 100 consecutive trials. | Automated state machine test harness | [ ] |
| **7** | **Physical Override Priority** | Physical mouse displacement $\ge 15\text{ px}$ pauses eye tracking for $2.0\text{ s}$ with zero delay. | Hardware injection test in `controller.py` | [ ] |
| **8** | **Automated Test Isolation** | Automated test suites execute exclusively with mock cursor adapters; real OS desktop mouse movement strictly disabled. | `pytest tests/` passing with zero actuation | [ ] |

---

## 10. References & Document History

### 10.1 Key Scientific Literature
1. Krafka, K., Khosla, A., Kellnhofer, P., Kannan, H., Bhandarkar, S., Matusik, W., & Torralba, A. (2016). Eye tracking for everyone. In *Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR)*, pp. 2176–2184.
2. Abdelrahman, A. A., Hempel, T., Khalifa, A., & Ding, Z. (2023). L2CS-Net: Fine-grained gaze estimation in unconstrained environments. In *Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV)*.
3. Feng, Z. H., Kittler, J., Awais, M., Huber, P., & Wu, X. J. (2018). Wing loss for robust facial landmark localisation with convolutional neural networks. In *CVPR*, pp. 2235–2245.
4. Wang, X., Bo, L., & Fuxin, L. (2019). Adaptive wing loss for robust face alignment via heatmap regression. In *ICCV*, pp. 6971–6981.
5. Kendall, A., Gal, Y., & Cipolla, R. (2018). Multi-task learning using uncertainty to weigh losses for scene geometry and semantics. In *CVPR*, pp. 7482–7491.
6. Casiez, G., Roussel, N., & Vogel, D. (2012). 1 € filter: A simple speed-based low-pass filter for noisy input in interactive systems. In *Proceedings of the SIGCHI Conference on Human Factors in Computing Systems*, pp. 2527–2530.
7. MacKenzie, I. S. (1992). Fitts' law as a research and design tool in human-computer interaction. *Human-Computer Interaction*, 7(1), 91–139.

### 10.2 Document Revision History
| Version | Date | Author / Agent | Changes / Milestone Rationale |
|:---:|:---:|:---:|:---|
| **1.0.0** | 2026-10-29 | `worker_m3` | Initial comprehensive specification unifying findings from Explorers M3.1, M3.2, and M3.3 for Milestone 3 (Step 9). |
