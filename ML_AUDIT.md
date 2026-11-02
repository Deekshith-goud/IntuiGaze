# IntuiGaze (EyeNav) — Comprehensive Machine Learning Audit

This document provides an exhaustive technical audit of the machine learning architectures, mathematical models, and data strategies utilized in the IntuiGaze (EyeNav) project. 

The system transitions elegantly from foundational heuristics to advanced sequence modeling, strictly adhering to the architectural requirements of **edge deployment (CPU-bound inference)** and **real-time low latency (sub-10ms)**.

---

## 1. Vision & Landmark Extraction (Foundation / Intermediate)

### Concept: Geometric Heuristics via Pre-Trained CNNs
The first stage of the pipeline relies on **MediaPipe Tasks API** (`backend/eyenav/vision/landmarks.py`), which uses the BlazeFace and FaceMesh architectures.

*   **Implementation**: 
    *   Extracts a dense 478-point 3D facial mesh, including explicit iris tracking landmarks (left: 468, right: 473).
    *   Extracts Facial Transformation Matrices (3x4) to decompose the 3D head pose into Euler angles (Pitch, Yaw, Roll) via OpenCV `cv2.RQDecomp3x3`.
*   **Geometric Feature Engineering**:
    *   **Eye Aspect Ratio (EAR)**: A foundational mathematical heuristic used to detect eye openness. It computes the ratio of vertical to horizontal distances between eyelid landmarks.
        ```text
        EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||)
        ```
    *   **Distance-Invariant Gaze Vector**: Normalizes iris displacement relative to eye bounding box width/height to make raw gaze calculation scale-invariant before passing it to the ML mappers.

---

## 2. Gaze Estimation (Intermediate / Advanced)

### Concept: Appearance-Based Convolutional Neural Networks (CNNs)
While MediaPipe provides geometric iris tracking, EyeNav utilizes **L2CS-Net** for highly accurate appearance-based gaze estimation (`backend/eyenav/vision/gaze.py`). 

*   **Architecture (MobileNetV3-Large Backbone)**:
    *   Input: 224x224 RGB face patch (normalized using ImageNet statistics).
    *   Output: Binned classification logits for Pitch (90 bins) and Yaw (90 bins), covering ±45°.
*   **Mathematical Concept (Binned Classification to Continuous Regression)**:
    *   Instead of directly regressing angles (which suffers from averaging artifacts near gaze boundaries), the model predicts a probability distribution over 90 discrete bins.
    *   A softmax-weighted mean is applied to convert the logits back to a continuous angle:
        ```python
        exp_logits = np.exp(logits - logits.max())
        probs = exp_logits / exp_logits.sum()
        angle = sum(probs * bins)
        ```
*   **Architectural Tradeoff (ADR-003)**:
    *   The team explicitly rejected ResNet-50 (18ms latency) and GazeTR Vision Transformers (25ms latency) in favor of **MobileNetV3**.
    *   This choice sacrifices a small amount of accuracy (2.1° to 2.9° uncalibrated MAE on ETH-XGaze) to achieve a **~6ms CPU latency**, strictly adhering to the edge-deployment requirement. Calibration brings this error down to the target ≤1°.
*   **Explainability (Confidence Scoring)**:
    *   The confidence of the gaze estimate is calculated dynamically using the **normalized Shannon Entropy** of the output logits. A sharper probability distribution yields lower entropy and higher confidence.

---

## 3. Spatial Mapping & Calibration (Foundation ML)

### Concept: Polynomial Ridge Regression & Online Adaptation
To map a 6-dimensional gaze feature vector `[left_x, left_y, right_x, right_y, head_yaw, head_pitch]` to a 2D screen coordinate `(x, y)`, the system uses regression models (`backend/eyenav/cursor/mapping.py`).

*   **Offline Calibration (`scripts/train_calibration_model.py`)**:
    *   Uses **Random Forest Regressor** (an ensemble learning method) to map complex, non-linear gaze dynamics to screen coordinates over large, clean datasets.
*   **Online Adaptive Mapping**:
    *   Because the eye's angular range compresses near the edges of the visual field, a purely linear mapping fails. The system uses a **Degree-2 Polynomial Approximation**.
    *   **Ridge Regression (L2 Regularization)**: Used during the initial 9-point calibration to prevent overfitting on extremely small sample sizes by adding a penalty term `λ * I` to the covariance matrix.
    *   **Recursive Least Squares (Rank-1 Update)**: The model learns continuously. Every time a user executes a successful "click" (long blink), the system treats that as a ground-truth label and updates the regression weights incrementally via a weighted outer product:
        ```python
        XtX += weight * np.outer(x_feat, x_feat)
        Xty_x += weight * x_feat * confirmed_screen_x
        ```

---

## 4. Intent Recognition (Advanced Sequence Modeling)

### Concept: Tiny Temporal Transformers
To distinguish between visually similar actions (e.g., *Reading* vs *Searching* vs *Selecting*), the system analyzes temporal sequences rather than static frames (`backend/eyenav/intent.py`).

*   **Architecture**:
    *   Input: A sliding window of 45 frames (1.5 seconds) of 32-dimensional feature vectors.
    *   Model: A 4-layer **Transformer Encoder** outputting a probability distribution across 13 distinct navigation intents (e.g., `scrolling_up`, `confirmation`, `nav_back`).
*   **Architectural Justification (ADR-002)**:
    *   LSTMs/GRUs were rejected because vanishing gradients limit context to ~30 frames and they lack interpretability.
    *   The Transformer's Self-Attention mechanism effectively captures long-range dependencies (e.g., a long fixation at frame 0, followed by a double blink at frame 40).
*   **Explainable AI (XAI)**:
    *   The model exports its **Attention Weights**. The system uses `np.argsort(attention_weights)` to identify the top 5 frames that drove the classification, providing a human-readable explanation (e.g., *"Detected selecting: focused fixation followed by deliberate blink"*).

---

## 5. Dataset Strategy & Bias Mitigation

Machine Learning is only as good as its data. The `DATASET_SPEC.md` outlines a highly mature, production-grade ML data strategy (The EyeNav Proprietary Intent Dataset - EPID):

*   **Taxonomy**: Defines a strict 5-level label taxonomy (Eye State → Blink Type → Gaze Direction → Eyebrow State → Intent) to eliminate annotator ambiguity.
*   **Temporal Annotation**: Sequences are auto-labeled based on prompted timings and manually verified by annotators.
*   **Bias Assessment**: 
    *   Mandates diversity across 6+ ethnic groups, Fitzpatrick skin tones 1-6, and various visual conditions (glasses, contacts).
    *   Requires stratification of model performance across demographics to prevent performance degradation for minority groups.
*   **Data Version Control**: All datasets are hashed and versioned via DVC to ensure reproducible ML training pipelines.

---

## Conclusion

The IntuiGaze project exhibits a highly disciplined application of Machine Learning. It avoids the trap of using "the biggest model" and instead carefully selects ML concepts based on mathematical necessity and production constraints:
1. **Foundation ML (Ridge Regression / Random Forest)** for fast, online spatial mapping.
2. **Intermediate ML (MobileNetV3 CNNs)** for robust, real-time gaze feature extraction.
3. **Advanced ML (Transformers)** for complex temporal intent recognition and explainability.
