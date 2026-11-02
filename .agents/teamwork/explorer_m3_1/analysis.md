# IntuiGaze — ML Problem Definition Technical Specification

**Author:** `explorer_m3_1`  
**Milestone:** M3 (ML Problem Definition Specification)  
**Target Document to Author in M3:** `docs/ml/ML_PROBLEM_DEFINITION.md`  
**Date:** 2026-10-29  
**Status:** Complete Technical Specification & Architectural Blueprint  

---

## 1. Executive Summary & Problem Scope

IntuiGaze is a real-time, appearance- and geometry-based eye-navigation system designed to provide hands-free human-computer interaction (cursor control, clicking, scrolling, and navigation commands) via consumer-grade webcams.

Operating on commodity CPU hardware requires balancing statistical predictive accuracy with deterministic safety guarantees, strict inference latency budgets ($\le 10$ ms per frame at 30–60 FPS), and resilience against real-world artifacts (blinks, head jerks, lighting shifts, and glasses reflections).

This specification establishes the mathematical formulations, coordinate transformations, loss functions, secondary auxiliary tasks, and multimodal feature representations that govern machine learning models in IntuiGaze, with specific focus on training against the 20.13 GB MIT GazeCapture benchmark (`archive.zip`) and integrating seamlessly with IntuiGaze's runtime modules (`mapping.py`, `gaze.py`, `intent.py`, and `safety.py`).

---

## 2. Primary Prediction Task: Normalized Screen Coordinate Regression

### 2.1 Formal Mathematical Formulation

Let $\mathcal{X}$ denote the input feature space (raw image crops, geometric landmarks, spatial grids, or hybrid representations).  
Let $\mathcal{Y} \subset \mathbb{R}^2$ denote the compact continuous target space of normalized screen coordinates:

$$\mathcal{Y} = [0, 1] \times [0, 1] = [0, 1]^2$$

The primary learning task is to learn a parameterised mapping function:

$$f_{\boldsymbol{\theta}}: \mathcal{X} \to \mathcal{Y}, \quad \hat{\mathbf{s}} = f_{\boldsymbol{\theta}}(\mathbf{x}) = (\hat{x}_{\text{norm}}, \hat{y}_{\text{norm}})^T$$

where:
- $\hat{x}_{\text{norm}} \in [0.0, 1.0]$ represents the horizontal gaze position on the active display, where $0.0$ is the extreme left border and $1.0$ is the extreme right border.
- $\hat{y}_{\text{norm}} \in [0.0, 1.0]$ represents the vertical gaze position on the active display, where $0.0$ is the extreme top border and $1.0$ is the extreme bottom border.
- $(0.0, 0.0)$ corresponds to the top-left corner of the display (consistent with standard computer graphics and OS windowing conventions: Windows GDI/DirectX, macOS Quartz/Cocoa, X11/Wayland).

### 2.2 Physical Pixel Projection & Screen Dimension Mapping

Given an active physical desktop display with horizontal resolution $W_{\text{screen}} \in \mathbb{N}$ pixels and vertical resolution $H_{\text{screen}} \in \mathbb{N}$ pixels, the continuous prediction $\hat{\mathbf{s}} = (\hat{x}_{\text{norm}}, \hat{y}_{\text{norm}})$ is mapped to discrete integer physical screen coordinates $\hat{\mathbf{p}} = (\hat{x}_{\text{px}}, \hat{y}_{\text{px}}) \in \{0, \dots, W_{\text{screen}}-1\} \times \{0, \dots, H_{\text{screen}}-1\}$ via the affine transformation:

$$\hat{x}_{\text{px}} = \operatorname{round}\left( \hat{x}_{\text{norm}} \cdot (W_{\text{screen}} - 1) \right)$$

$$\hat{y}_{\text{px}} = \operatorname{round}\left( \hat{y}_{\text{norm}} \cdot (H_{\text{screen}} - 1) \right)$$

For sub-pixel cursor movement and temporal filtering (e.g. One-Euro Filter or Kalman Filter in `controller.py`), the continuous floating-point screen coordinates are preserved:

$$\mathbf{p}_{\text{cont}} = \begin{pmatrix} \hat{x}_{\text{norm}} \cdot W_{\text{screen}} \\ \hat{y}_{\text{norm}} \cdot H_{\text{screen}} \end{pmatrix} \in \mathbb{R}^2$$

---

### 2.3 MIT GazeCapture Coordinate Conversion & Device Orientation Dynamics

The primary ground-truth dataset for IntuiGaze is MIT GazeCapture (`archive.zip`), recorded on Apple iOS devices (iPhones and iPads). To construct leak-free, mathematically sound training targets, the extraction pipeline must faithfully convert from raw iOS device records to canonical normalized space.

#### 2.3.1 Ground Truth Data Inputs per Frame
For each frame $k$ in a subject's session:
1. `dotInfo.json`:
   - `XPts[k]`, `YPts[k]`: Gaze target location in Apple UIKit screen points ($\text{pts}$).
   - `XCam[k]`, `YCam[k]`: 3D displacement of the gaze target relative to the camera lens optical center in **centimeters** ($\text{cm}$).
2. `screen.json`:
   - `W[k]`: Screen width in UIKit points in the active orientation.
   - `H[k]`: Screen height in UIKit points in the active orientation.
   - `Orientation[k]`: iOS `UIDeviceOrientation` integer enum $\in \{1, 2, 3, 4\}$.

#### 2.3.2 Device Orientation Specification
In Apple iOS and MIT GazeCapture:
- **Orientation 1 (`UIDeviceOrientationPortrait`)**: Device held upright; Home button at bottom; Front camera at top center.
- **Orientation 2 (`UIDeviceOrientationPortraitUpsideDown`)**: Device inverted; Home button at top; Front camera at bottom center.
- **Orientation 3 (`UIDeviceOrientationLandscapeRight`)**: Device rotated $90^\circ$ clockwise (from user viewpoint, Home button is on the left; camera on the right).
- **Orientation 4 (`UIDeviceOrientationLandscapeLeft`)**: Device rotated $90^\circ$ counter-clockwise (Home button is on the right; camera on the left).

#### 2.3.3 Direct Screen-Space Normalization
In `screen.json`, the values $W[k]$ and $H[k]$ already reflect the active aspect ratio of the screen in the given orientation (for example, on an iPhone 5, Orientation 1 has $W=320, H=568$, whereas Orientation 3/4 has $W=568, H=320$).

Therefore, the direct screen-space normalized ground truth $\mathbf{y}_{\text{norm}} = (x_{\text{norm}}, y_{\text{norm}})^T$ for any valid frame $k$ is computed as:

$$x_{\text{norm}}[k] = \frac{\text{XPts}[k]}{W[k]}$$

$$y_{\text{norm}}[k] = \frac{\text{YPts}[k]}{H[k]}$$

Subject to the validity assertion: $x_{\text{norm}}[k] \in [0.0, 1.0]$ and $y_{\text{norm}}[k] \in [0.0, 1.0]$. Any sample with negative coordinates or values exceeding $1.0$ by more than a floating-point tolerance ($\epsilon = 10^{-4}$) is flagged as an out-of-bounds artifact and quarantined.

#### 2.3.4 Camera-Space Physical Metric Mapping (Centimeter Regression)
For cross-device geometric transfer (e.g. mapping mobile training to arbitrary desktop webcam setups), the target can also be formulated in metric camera space $(x_{\text{cm}}, y_{\text{cm}})$.

Let $(X_{\text{cam}}, Y_{\text{cam}})$ be the displacement in centimeters from camera lens to gaze dot. The camera-to-screen transformation depends on the physical camera offset $(\Delta x_{\text{dev}}, \Delta y_{\text{dev}})$ and the screen's physical points-per-inch ($\text{PPI}$) or points-per-centimeter ($\text{PPC} = \frac{\text{PPI}}{2.54}$):

$$\begin{pmatrix} X_{\text{cam}} \\ Y_{\text{cam}} \end{pmatrix} = \mathbf{R}_{\text{orient}} \cdot \begin{pmatrix} \frac{\text{XPts} - x_{\text{cam\_pts}}}{\text{PPC}} \\ \frac{\text{YPts} - y_{\text{cam\_pts}}}{\text{PPC}} \end{pmatrix}$$

where $\mathbf{R}_{\text{orient}}$ is the 2D rotation matrix corresponding to device orientation $O \in \{1, 2, 3, 4\}$:

$$\mathbf{R}_1 = \begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix}, \quad \mathbf{R}_2 = \begin{pmatrix} -1 & 0 \\ 0 & -1 \end{pmatrix}, \quad \mathbf{R}_3 = \begin{pmatrix} 0 & 1 \\ -1 & 0 \end{pmatrix}, \quad \mathbf{R}_4 = \begin{pmatrix} 0 & -1 \\ 1 & 0 \end{pmatrix}$$

---

### 2.4 Target Bounding vs. Unbounded Linear Regression with Post-Processing Guards

A central architectural decision in gaze coordinate regression is whether to enforce target bounds inside the model via an activation function (e.g., Sigmoid $\sigma(z) = \frac{1}{1 + e^{-z}}$) or to predict unbounded linear coordinates followed by external safety guards.

#### 2.4.1 Analysis of Bounded Output Activation (Sigmoid)
- **Mathematical Form:** $\hat{y} = \sigma(z) = \frac{1}{1 + e^{-z}} \in (0, 1)$.
- **Gradient Behavior:**
  $$\frac{\partial \hat{y}}{\partial z} = \sigma(z)(1 - \sigma(z))$$
- **The Vanishing Edge Problem:** As gaze targets approach the screen edges ($y \to 0$ or $y \to 1$), the required logit $z \to \pm \infty$. Consequently:
  $$\lim_{z \to \pm \infty} \frac{\partial \hat{y}}{\partial z} = 0$$
  This causes severe gradient vanishing near screen borders. In empirical gaze tracking, users frequently look at edge UI elements (taskbars, close buttons, menu bars, browser tabs). A Sigmoid output layer compresses predictions toward the center ($0.5, 0.5$) and requires massive weight updates to reach screen corners, causing edge target under-shooting.

#### 2.4.2 Analysis of Unbounded Linear Output
- **Mathematical Form:** $\hat{\mathbf{s}} = \mathbf{W}_o \mathbf{h} + \mathbf{b}_o \in \mathbb{R}^2$.
- **Gradient Behavior:**
  $$\frac{\partial \hat{\mathbf{s}}}{\partial (\mathbf{W}_o \mathbf{h} + \mathbf{b}_o)} = \mathbf{I}_2$$
  Gradient flow is uniform and linear across the entire visual field, ensuring identical optimization dynamics whether the user fixates on the center or the extreme corners.
- **Risk:** The model can theoretically output values outside $[0, 1]$ during blinks, extreme head poses, or visual noise.

#### 2.4.3 The IntuiGaze Architectural Decision: Unbounded Linear + Two-Stage Safety Guard
IntuiGaze adopts **unbounded linear regression for model training and raw inference**, coupled with a **two-tier post-processing guard**:

1. **Tier 1 — Off-Screen Anomaly Detection (Track Loss Detector):**
   Define an anomaly margin $\epsilon_{\text{guard}} = 0.25$ ($25\%$ beyond screen boundary):
   $$\text{IsAnomaly}(\hat{\mathbf{s}}) = \mathbb{I}\left( \hat{x}_{\text{norm}} < -\epsilon_{\text{guard}} \;\lor\; \hat{x}_{\text{norm}} > 1 + \epsilon_{\text{guard}} \;\lor\; \hat{y}_{\text{norm}} < -\epsilon_{\text{guard}} \;\lor\; \hat{y}_{\text{norm}} > 1 + \epsilon_{\text{guard}} \right)$$
   If $\text{IsAnomaly}(\hat{\mathbf{s}}) = 1$, the frame is marked as **Gaze Divergence / Eye Landmark Loss**. The cursor position update is inhibited, confidence is forced to $0.0$, and the safety filter engages Layer 1 & Layer 5 blocks.

2. **Tier 2 — Deterministic Coordinate Clamping:**
   For valid non-anomalous frames, cursor coordinates are deterministically clamped to the active display bounds:
   $$\hat{x}_{\text{clamped}} = \max\left(0.0, \min\left(1.0, \hat{x}_{\text{norm}}\right)\right)$$
   $$\hat{y}_{\text{clamped}} = \max\left(0.0, \min\left(1.0, \hat{y}_{\text{norm}}\right)\right)$$
   This guarantees that cursor actuation never escapes display boundaries, while preserving unclipped regression gradients during backpropagation.

---

## 3. Loss Functions for Screen Coordinate Regression

Let $\mathbf{y}_i = (x_i, y_i)^T \in [0, 1]^2$ be the ground truth normalized coordinate vector for sample $i$, and $\hat{\mathbf{y}}_i = (\hat{x}_i, \hat{y}_i)^T \in \mathbb{R}^2$ be the model prediction. Let $\mathbf{r}_i = \hat{\mathbf{y}}_i - \mathbf{y}_i$ denote the residual vector, with components $r_{x,i} = \hat{x}_i - x_i$ and $r_{y,i} = \hat{y}_i - y_i$.

### 3.1 Mean Squared Error (MSE) Loss

$$\mathcal{L}_{\text{MSE}}(\mathbf{y}, \hat{\mathbf{y}}) = \frac{1}{2N} \sum_{i=1}^N \|\hat{\mathbf{y}}_i - \mathbf{y}_i\|_2^2 = \frac{1}{2N} \sum_{i=1}^N \left( r_{x,i}^2 + r_{y,i}^2 \right)$$

- **Gradient:**
  $$\frac{\partial \mathcal{L}_{\text{MSE}}}{\partial \hat{\mathbf{y}}_i} = \frac{1}{N} (\hat{\mathbf{y}}_i - \mathbf{y}_i) = \frac{1}{N} \mathbf{r}_i$$
- **Characteristics & Limitations in Gaze Tracking:**
  - *Advantage:* Infinitely differentiable everywhere ($C^\infty$), convex, optimal under Gaussian noise assumptions.
  - *Failure Mode:* The gradient magnitude is strictly proportional to residual magnitude $\|\mathbf{r}_i\|$. In gaze tracking, eye blinks, tracking glitches, and fast exploratory saccades produce massive outlier residuals (e.g., $r > 0.5$ in normalized space). Because MSE penalizes errors quadratically, these outliers generate massive gradients that dominate the batch gradient, destabilizing convergence and corrupting fine fixation accuracy.

---

### 3.2 Huber Loss (Smooth L1 Loss)

To bound the influence of outlier blinks and saccades, the Huber loss provides a smooth transition from quadratic penalty (for small residuals) to linear penalty (for large residuals) controlled by threshold $\delta > 0$:

$$\mathcal{L}_{\text{Huber},\delta}(\mathbf{r}) = \frac{1}{N} \sum_{i=1}^N \left( \ell_\delta(r_{x,i}) + \ell_\delta(r_{y,i}) \right)$$

where:
$$\ell_\delta(r) = \begin{cases} \frac{1}{2} r^2 & \text{if } |r| \le \delta \\ \delta \left( |r| - \frac{1}{2} \delta \right) & \text{if } |r| > \delta \end{cases}$$

- **Gradient:**
  $$\frac{\partial \ell_\delta(r)}{\partial r} = \begin{cases} r & \text{if } |r| \le \delta \\ \delta \cdot \operatorname{sign}(r) & \text{if } |r| > \delta \end{cases}$$
- **Optimal Hyperparameter Configuration for IntuiGaze:**
  - In normalized screen space $[0, 1]$, a typical 1080p fixation tolerance of $\pm 25$ pixels corresponds to $\delta \approx \frac{25}{1920} \approx 0.013$.
  - Recommended threshold: $\delta = 0.02$ (equivalent to $\sim 38$ pixels on 1080p).
  - Outliers with error $> 0.02$ produce a constant bounded gradient of $\pm 0.02$, preventing training explosions from sudden head movements.

---

### 3.3 Adaptive Wing (AWing) Loss for High-Precision Fixations

While Huber loss bounds outlier gradients, its gradient approaches zero linearly as $|r| \to 0$ ($\frac{\partial \ell}{\partial r} = r$). For UI navigation, however, sub-pixel and micro-fixation accuracy is paramount: an error reduction from 20 px to 5 px is far more crucial for clicking a button than an error reduction from 400 px to 385 px during a saccade.

Wing Loss (Feng et al., CVPR 2018) and Adaptive Wing Loss (Wang et al., ICCV 2019) counteract this by using a logarithmic formulation that produces **steep gradients for small residuals** while preserving linear gradients for large errors.

#### Formulation:
$$\mathcal{L}_{\text{Wing}}(r) = \begin{cases} \omega \ln\left( 1 + \left| \frac{r}{\epsilon} \right| \right) & \text{if } |r| < \omega \\ |r| - C & \text{if } |r| \ge \omega \end{cases}$$

where:
$$C = \omega - \omega \ln\left( 1 + \frac{\omega}{\epsilon} \right)$$
and $\omega > 0$ sets the non-linear range, while $\epsilon > 0$ curbs infinite gradient at $r=0$.

- **Gradient:**
  $$\frac{\partial \mathcal{L}_{\text{Wing}}}{\partial r} = \begin{cases} \frac{\omega}{\epsilon + |r|} \operatorname{sign}(r) & \text{if } |r| < \omega \\ \operatorname{sign}(r) & \text{if } |r| \ge \omega \end{cases}$$

- **Gradient Dynamics Comparison:**
  - Near zero ($|r| \to 0$): MSE gradient $\to 0$; Huber gradient $\to 0$. In contrast, Wing gradient approaches $\frac{\omega}{\epsilon} \operatorname{sign}(r)$.
  - Setting $\omega = 0.05$ and $\epsilon = 0.01$ ensures that fine fixation errors receive up to $5\times$ stronger gradient push toward zero, directly eliminating the "slow drift" and residual bias commonly observed around button boundaries.

---

### 3.4 Pinball Loss for Predictive Uncertainty & Confidence Estimation

To feed IntuiGaze's Layer 1 Safety Filter (Confidence Gating), the regression model can be trained via Quantile Regression using the Pinball loss.

Instead of predicting only the conditional mean $\mathbb{E}[y|x]$, the network predicts three quantiles per coordinate: $\tau \in \{0.1, 0.5, 0.9\}$ (10th percentile lower bound $\hat{q}_{0.1}$, median $\hat{q}_{0.5}$, and 90th percentile upper bound $\hat{q}_{0.9}$).

The asymmetric Pinball loss for quantile $\tau \in (0, 1)$ is:

$$\mathcal{L}_{\tau}(r) = \max\left( \tau r, (\tau - 1) r \right) = r \left( \tau - \mathbb{I}(r < 0) \right)$$

where $r = y - \hat{q}_\tau$.

- **Runtime Uncertainty Output:**
  $$\text{Uncertainty}_x = \hat{q}_{0.9}(x) - \hat{q}_{0.1}(x), \quad \text{Uncertainty}_y = \hat{q}_{0.9}(y) - \hat{q}_{0.1}(y)$$
  $$\text{Confidence} = \exp\left( -\frac{\sqrt{\text{Uncertainty}_x^2 + \text{Uncertainty}_y^2}}{\sigma_{\text{gate}}} \right) \in (0, 1]$$
  This gives a principled, distribution-free confidence metric that directly informs the click inhibitor when gaze estimates are diffuse.

---

### 3.5 Multi-Task Loss Formulation

When training a unified or multi-branch model combining screen coordinate regression $\hat{\mathbf{s}}$, 3D gaze direction vector $\hat{\mathbf{d}}$, and temporal intent $\hat{\mathbf{p}}$, the total loss must balance heterogeneous task scales.

#### 3.5.1 Linear Combination Loss
$$\mathcal{L}_{\text{total}} = \lambda_1 \mathcal{L}_{\text{coord}}(\mathbf{s}, \hat{\mathbf{s}}) + \lambda_2 \mathcal{L}_{\text{angular}}(\mathbf{d}, \hat{\mathbf{d}}) + \lambda_3 \mathcal{L}_{\text{intent}}(\mathbf{c}, \hat{\mathbf{p}})$$

Baseline weighting: $\lambda_1 = 1.0$ (normalized coord MSE/Huber $\sim 10^{-2}$ to $10^{-3}$), $\lambda_2 = 0.01$ (angular error in degrees $\sim 2^\circ$ to $10^\circ$), $\lambda_3 = 0.1$ (cross-entropy $\sim 0.5$ to $2.0$).

#### 3.5.2 Homoscedastic Uncertainty Weighting (Principled Multi-Task)
To eliminate manual hyperparameter tuning and prevent one task from starving others, IntuiGaze specifies homoscedastic uncertainty weighting (Kendall et al., CVPR 2018):

$$\mathcal{L}_{\text{multi}}(\boldsymbol{\theta}, \sigma_1, \sigma_2, \sigma_3) = \frac{1}{2\sigma_1^2} \mathcal{L}_{\text{coord}} + \frac{1}{2\sigma_2^2} \mathcal{L}_{\text{angular}} + \frac{1}{\sigma_3^2} \mathcal{L}_{\text{intent}} + \ln \sigma_1 + \ln \sigma_2 + \ln \sigma_3$$

where $\sigma_1, \sigma_2, \sigma_3 > 0$ are learnable observation noise scalars optimized via backpropagation alongside network weights $\boldsymbol{\theta}$.

---

## 4. Secondary Tasks Specification

### 4.1 Task S1: 3D Gaze Direction Angular Regression

#### 4.1.1 3D Unit Gaze Vector Representation
Let $\mathbf{d} = (d_x, d_y, d_z)^T \in \mathbb{S}^2 \subset \mathbb{R}^3$ be the true gaze direction unit vector in camera Cartesian coordinate space ($\|\mathbf{d}\|_2 = 1$).

- **Angular Error Loss Function:**
  The metric and loss function evaluates the geodesic angular separation in degrees:
  $$\mathcal{L}_{\text{angular}}(\mathbf{d}, \hat{\mathbf{d}}) = \frac{180^\circ}{\pi} \arccos\left( \frac{\mathbf{d}^T \hat{\mathbf{d}}}{\|\mathbf{d}\|_2 \|\hat{\mathbf{d}}\|_2 + \epsilon_{\text{stab}}} \right)$$
  where $\epsilon_{\text{stab}} = 10^{-7}$ prevents numerical instability at $\pm 1$.

- **Cosine Proximity Surrogate Loss:**
  During early training, $\arccos$ gradients can be unstable near collinearity ($\frac{d}{du}\arccos(u) = -\frac{1}{\sqrt{1-u^2}} \to \infty$ as $u \to 1$). Hence, the cosine distance loss is used as an optimization surrogate:
  $$\mathcal{L}_{\text{cos}}(\mathbf{d}, \hat{\mathbf{d}}) = 1 - \frac{\mathbf{d}^T \hat{\mathbf{d}}}{\|\hat{\mathbf{d}}\|_2}$$

#### 4.1.2 Spherical Pitch-Yaw Representation
Alternatively, gaze direction is expressed in spherical coordinates as pitch $\theta$ (elevation) and yaw $\phi$ (azimuth) in radians or degrees:

$$\mathbf{d} = \begin{pmatrix} -\cos \theta \sin \phi \\ -\sin \theta \\ -\cos \theta \cos \phi \end{pmatrix} \quad \Longleftrightarrow \quad \begin{cases} \theta = -\arcsin(d_y) \\ \phi = -\arctan2(d_x, -d_z) \end{cases}$$

#### 4.1.3 L2CS-Net Binned Classification with Soft-Argmax Expectation
To avoid the regression averaging problem (where regression models predict the mean of multimodal distributions, blurring sharp saccades), IntuiGaze adopts the L2CS-Net formulation (`backend/eyenav/vision/gaze.py`):
1. Discretize pitch $\theta$ and yaw $\phi$ into $B = 90$ discrete bins covering $[-45^\circ, +45^\circ]$ (bin width $\Delta = 1.0^\circ$ or $2.0^\circ$).
2. Model outputs raw classification logits: $\mathbf{z}_{\text{pitch}} \in \mathbb{R}^{90}$ and $\mathbf{z}_{\text{yaw}} \in \mathbb{R}^{90}$.
3. Softmax probabilities: $p_b = \frac{e^{z_b}}{\sum_j e^{z_j}}$.
4. Continuous expectation (soft-argmax):
   $$\hat{\theta} = \sum_{b=1}^{90} \text{bin\_center}_b \cdot p_b(\text{pitch})$$
   $$\hat{\phi} = \sum_{b=1}^{90} \text{bin\_center}_b \cdot p_b(\text{yaw})$$
5. Combined loss: Cross-entropy classification on ground-truth bin index + MSE on continuous expectation.

---

### 4.2 Task S2: 13-Class Temporal Intent Classification

#### 4.2.1 Target Classes and Semantics (Matching `intent.py`)
IntuiGaze defines an explicit 13-class navigation intent catalog:

| ID | Class Name | Interaction Semantics | Command Output (`INTENT_TO_COMMAND`) | Safety Behavior |
|:--:|:-----------|:----------------------|:-------------------------------------|:----------------|
| 0 | `idle` | Baseline resting state, no navigation intent | `None` | Passive hover, no click |
| 1 | `reading` | Left-to-right progressive scanlines | `None` | **Suppress all commands** |
| 2 | `selecting` | Fixation dwell / deliberate click intent | `"select"` | Requires Layer 4 Dwell confirmation |
| 3 | `scrolling_up` | Sustained upward gaze pursuit | `"scroll_up"` | Cooldown throttled |
| 4 | `scrolling_down` | Sustained downward gaze pursuit | `"scroll_down"` | Cooldown throttled |
| 5 | `searching` | Rapid exploratory saccadic scanpaths | `None` | **Suppress all commands** |
| 6 | `activation` | Intent to wake up / enable EyeNav | `"activate"` | Requires confirmation |
| 7 | `deactivation` | Intent to sleep / disable EyeNav | `"deactivate"` | Instant toggle |
| 8 | `confirmation` | Affirmative response to prompt (long blink/nod) | `"enter"` | Action verified |
| 9 | `cancellation` | Abort current action (escape gesture) | `"escape"` | Clears pending dwells |
| 10 | `nav_back` | Backward page navigation gesture | `"back"` | Rate-limited |
| 11 | `nav_forward` | Forward page navigation gesture | `"forward"` | Rate-limited |
| 12 | `nav_home` | Return to home / main interface | `"home"` | Rate-limited |

#### 4.2.2 Temporal Sequence Formulation
The intent classifier processes a temporal sliding window buffer:

$$\mathbf{X}_{\text{intent}} \in \mathbb{R}^{T \times F}$$

where:
- Temporal length $T = 45$ frames ($1.5$ seconds at $30$ FPS).
- Feature dimension $F = 32$ per frame, comprising:
  - Screen coordinate velocity and acceleration: $(\dot{x}, \dot{y}, \ddot{x}, \ddot{y})$.
  - Iris displacement vectors and Eye Aspect Ratios (EAR): $(\text{EAR}_{\text{left}}, \text{EAR}_{\text{right}}, \Delta \text{EAR})$.
  - 3D Head pose velocities: $(\dot{\theta}_{\text{pitch}}, \dot{\phi}_{\text{yaw}}, \dot{\psi}_{\text{roll}})$.
  - Fixation dispersion and saccade velocity magnitude.

#### 4.2.3 Class Imbalance & Multi-Class Focal Loss
In real usage, class distribution is extremely skewed: `idle` and `reading` account for $>85\%$ of frames, while `activation`, `deactivation`, and `confirmation` are rare events ($<1\%$).

To prevent the classifier from collapsing to an all-idle dummy model, the optimization objective uses Multi-Class Focal Loss with inverse-frequency weighting:

$$\mathcal{L}_{\text{Focal}}(\mathbf{p}, \mathbf{y}) = -\sum_{c=0}^{12} \alpha_c (1 - p_c)^\gamma y_c \ln(p_c + \epsilon)$$

where:
- $\mathbf{y} \in \{0, 1\}^{13}$ is the one-hot target vector.
- $p_c$ is the predicted softmax probability for class $c$.
- $\gamma = 2.0$ is the focusing parameter that down-weights easy negatives (`idle`).
- $\alpha_c = \frac{1}{\sqrt{\text{Frequency}(c)}}$ balances rare event sensitivity.

---

## 5. Feature Input Space: Multimodal Ingestion Contract

IntuiGaze supports a modular, multimodal feature representation designed for hybrid geometric and appearance modeling.

```
                           ┌───────────────────────────────┐
                           │      Raw Input Frame          │
                           └──────────────┬────────────────┘
                                          │
                  ┌───────────────────────┼───────────────────────┐
                  ▼                       ▼                       ▼
          ┌───────────────┐       ┌───────────────┐       ┌───────────────┐
          │  MediaPipe    │       │ Face Bounding │       │ Eye Bounding  │
          │ FaceLandmarker│       │      Box      │       │     Boxes     │
          └───────┬───────┘       └───────┬───────┘       └───────┬───────┘
                  │                       │                       │
                  ▼                       ▼                       ▼
          ┌───────────────┐       ┌───────────────┐       ┌───────────────┐
          │ Landmarks L   │       │ Face Crop I_F │       │Eye Crops I_L, │
          │ (478 x 3)     │       │ (224x224x3)   │       │I_R (128x128x3)│
          └───────┬───────┘       └───────┬───────┘       └───────┬───────┘
                  │                       │                       │
                  │                       ▼                       │
                  │               ┌───────────────┐               │
                  │               │Face Grid G    │               │
                  │               │ (25 x 25)     │               │
                  │               └───────┬───────┘               │
                  │                       │                       │
                  ▼                       ▼                       ▼
          ┌───────────────────────────────────────────────────────────────┐
          │             Multimodal Fusion / Feature Concatenation         │
          └───────────────────────────────┬───────────────────────────────┘
                                          ▼
          ┌───────────────────────────────────────────────────────────────┐
          │      Primary Regressor & Secondary Heads (Latency ≤ 10ms)     │
          └───────────────────────────────────────────────────────────────┘
```

### 5.1 Specification of Modalities

| Modality | Symbol | Data Type & Shape | Source / Extraction Method | Preprocessing & Normalization |
|:---------|:------:|:-----------------:|:--------------------------|:------------------------------|
| **Left Eye Image Crop** | $\mathbf{I}_L$ | $\text{float32}, (3 \times 128 \times 128)$ | `appleLeftEye.json` bounding box or MediaPipe eye landmarks | Resized to $128\times 128$; ImageNet normalized $(\mu, \sigma)$ |
| **Right Eye Image Crop** | $\mathbf{I}_R$ | $\text{float32}, (3 \times 128 \times 128)$ | `appleRightEye.json` bounding box or MediaPipe eye landmarks | Horizontally mirrored for Siamese weight sharing; ImageNet norm |
| **Face Image Crop** | $\mathbf{I}_F$ | $\text{float32}, (3 \times 224 \times 224)$ | `appleFace.json` bounding box | Resized to $224\times 224$; ImageNet normalized $(\mu, \sigma)$ |
| **Binary Face Grid** | $\mathbf{G}$ | $\text{float32}, (1 \times 25 \times 25)$ | `faceGrid.json` or computed from face box in full frame | Flattened to $625$-D binary vector $\in \{0, 1\}^{625}$ |
| **Facial Landmarks** | $\mathbf{L}$ | $\text{float32}, (478 \times 3)$ | MediaPipe FaceLandmarker Tasks API (`face_landmarker.task`) | Normalized to $[0, 1]$ image space; centered on nose bridge |

---

### 5.2 Modality Details

#### 5.2.1 Eye Image Crops ($\mathbf{I}_L, \mathbf{I}_R$) and Siamese Symmetry
To exploit bilateral anatomical symmetry and halve the parameter count of the eye feature extractor:
- The right eye patch $\mathbf{I}_R$ is flipped horizontally before feeding into the CNN backbone:
  $$\tilde{\mathbf{I}}_R(c, y, x) = \mathbf{I}_R(c, y, W_{\text{crop}} - 1 - x)$$
- Both $\mathbf{I}_L$ and $\tilde{\mathbf{I}}_R$ pass through an identical weight-shared CNN backbone (e.g. MobileNetV3-Small or ResNet-18), producing embedding vectors $\mathbf{e}_L, \mathbf{e}_R \in \mathbb{R}^{128}$.

#### 5.2.2 Binary Face Grid ($\mathbf{G}$)
The $25 \times 25$ binary face grid encodes the position and scale of the user's face relative to the camera sensor without requiring full-resolution frame processing:
1. Divide the camera sensor resolution into a uniform grid of $25 \times 25$ cells.
2. Given face bounding box $[x_{\min}, y_{\min}, w, h]$ normalized to $[0, 1]$:
   $$G_{u, v} = \begin{cases} 1 & \text{if cell }(u, v)\text{ overlaps the face bounding box} \\ 0 & \text{otherwise} \end{cases}$$
3. $\mathbf{G}$ passes through a 2-layer MLP ($625 \to 128 \to 64$), outputting spatial feature vector $\mathbf{e}_G \in \mathbb{R}^{64}$.

#### 5.2.3 3D Facial Landmarks ($\mathbf{L} \in \mathbb{R}^{478 \times 3}$)
MediaPipe FaceLandmarker provides 478 3D points. Crucial geometric sub-features extracted for low-latency linear/polynomial regression include:
- Left Iris Center: Index 468 $(x_{468}, y_{468}, z_{468})$.
- Right Iris Center: Index 473 $(x_{473}, y_{473}, z_{473})$.
- Eye Corners & Contours:
  - Left eye: $[33, 160, 158, 133, 153, 144]$
  - Right eye: $[362, 385, 387, 263, 373, 380]$
- 3D Head Pose: Derived rotation angles $(\theta_{\text{pitch}}, \phi_{\text{yaw}}, \psi_{\text{roll}})$ from the $4\times 4$ facial transformation matrix via OpenCV RQ decomposition.

---

### 5.3 Real-Time CPU Latency Budget Allocation

For interactive computer navigation, total latency from frame capture to mouse cursor dispatch must not exceed $16.6$ ms ($60$ FPS) or at minimum $33.3$ ms ($30$ FPS). On a standard quad-core consumer CPU (Intel Core i5-8250U / AMD Ryzen 5 without discrete GPU), the computational budget is allocated as follows:

| Stage | Operation | Max Latency Budget | Target Execution Engine |
|:------|:----------|:------------------:|:------------------------|
| **1. Vision Capture** | OpenCV camera capture + RGB conversion | $2.0$ ms | OpenCV Native |
| **2. Landmark Extraction** | MediaPipe FaceLandmarker Tasks API | $4.0$ ms | MediaPipe C++ Runtime (XNNPACK) |
| **3. Feature Extraction** | Eye/Face crop + normalization / Grid | $1.0$ ms | NumPy / OpenCV optimized |
| **4. ML Inference** | Model Forward Pass ($f_{\boldsymbol{\theta}}$) | $\le 6.0$ ms | ONNX Runtime (CPUExecutionProvider) |
| **5. Post-Processing** | One-Euro filter + SafetyFilter + Clamping | $0.5$ ms | Pure Python / C-types |
| **Total Pipeline** | **End-to-End Frame-to-Cursor Latency** | **$\le 13.5$ ms** | **Sustained $\ge 60$ FPS** |

---

## 6. Integration Architecture with IntuiGaze Runtime & Safety Systems

### 6.1 Coupling with `GazeScreenMapper` (`backend/eyenav/cursor/mapping.py`)
In the existing codebase, `GazeScreenMapper` implements polynomial regression mapping from geometric features to screen pixels:
- The primary ML model $f_{\boldsymbol{\theta}}$ provides the base generalized mapping:
  $$\hat{\mathbf{s}}_{\text{base}} = f_{\boldsymbol{\theta}}(\mathbf{x}) \in [0, 1]^2$$
- `GazeScreenMapper` acts as the **personal adaptation and calibration layer**:
  $$\mathbf{p}_{\text{calibrated}} = \mathbf{W}_{\text{calib}} \cdot \phi(\hat{\mathbf{s}}_{\text{base}}) + \mathbf{b}_{\text{calib}}$$
  where $\phi(\cdot)$ is a 2nd-degree polynomial expansion and $\mathbf{W}_{\text{calib}}$ is initialized via 9-point user calibration and adapted online via rank-1 Recursive Least Squares (RLS) on confirmed blink-clicks.

### 6.2 Coupling with `GazeCursorController` (`backend/eyenav/cursor/controller.py`)
- Uncommitted fixation deadzone invariant: `_FIXATION_DEADZONE_PX = 45.0`.
- When predicted velocity $\|\mathbf{v}_{\text{cursor}}\|_2 < \text{threshold}$, the cursor enters gravity lock, eliminating natural eye tremor and microsaccadic jitter during button fixation.

### 6.3 Coupling with `SafetyFilter` (`backend/eyenav/safety.py`)
Predictions from $f_{\boldsymbol{\theta}}$ directly drive the 6-layer safety filter:
1. **Layer 1 (Confidence Gate):** If ML output confidence $< 0.70$ (or uncertainty interval width $> 0.15$), all click commands are inhibited.
2. **Layer 3 (Context Gate):** If Task S2 predicts `reading` or `searching`, mouse clicks and navigation commands are strictly blocked.
3. **Layer 5 (Anti-Pattern Gate):** If regression coordinates exhibit off-screen anomaly ($\text{IsAnomaly} = 1$), cursor updates freeze.
4. **Layer 6 (Emergency Stop):** 3-second sustained eye closure (detected via $\text{EAR} < 0.15$) engages emergency stop, blocking all actuation.

---

## 7. Concrete Recommendations for Authoring `docs/ml/ML_PROBLEM_DEFINITION.md`

When Milestone 3 synthesizes and creates `docs/ml/ML_PROBLEM_DEFINITION.md`, the document should adopt the following structured table of contents and specifications directly derived from this analysis:

1. **Title & Document Scope:** Formal problem definition for IntuiGaze gaze tracking and intent engine.
2. **Task Taxonomy:**
   - Primary: Normalized Screen Coordinate Regression ($[0, 1]^2$).
   - Secondary Auxiliary: 3D Gaze Direction Angular Regression ($\mathbb{S}^2$).
   - Secondary Temporal: 13-Class Navigation Intent Classification ($\Delta^{12}$).
3. **Mathematical Formulation & Coordinate Systems:** Include all conversion formulas between UIKit screen points, device orientations (1–4), camera physical displacement ($\text{cm}$), and normalized unit screen space.
4. **Bounding & Clamping Policy:** Document unbounded linear regression with the two-tier anomaly/clamping guard.
5. **Loss Functions:**
   - Prescribe Huber loss ($\delta = 0.02$) and Adaptive Wing loss ($\omega = 0.05, \epsilon = 0.01$) as the standard regression objectives over raw MSE.
   - Prescribe Multi-Class Focal Loss for intent classification.
   - Prescribe homoscedastic uncertainty weighting for multi-task heads.
6. **Feature Space & Data Schema:** Detail the 5 input modalities ($\mathbf{I}_L, \mathbf{I}_R, \mathbf{I}_F, \mathbf{G}, \mathbf{L}$) with exact tensor shapes, normalization constants, and MediaPipe landmark index mappings.
7. **Latency & Resource Contracts:** Enforce $\le 6.0$ ms ONNX CPU forward pass and $\le 10.0$ ms total frame processing budget.
8. **Compliance with Repository Invariants:** Reference `AGENTS.md`, `METRICS_POLICY.md`, and cursor safety rules.
