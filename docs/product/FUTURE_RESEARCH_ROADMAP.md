# EyeNav — Future Research Roadmap

**Document Version:** 1.0  
**Status:** Approved  
**Owner:** Research Team  
**Last Updated:** 2024-Q4  
**Horizon:** 2025–2030  

---

## 1. Overview

This document maps EyeNav's research agenda across a 5-year horizon. It identifies open problems, proposes research directions, and prioritizes them by scientific impact and commercial value.

EyeNav is not merely a product — it is a research platform. Every design decision is a testable hypothesis. Every deployment is an opportunity for data collection and learning.

---

## 2. Open Problems (2025)

### 2.1 The Intent Ambiguity Problem

**Problem:** Two visually identical fixation sequences (same gaze, same blinks) may represent completely different intents (reading vs. preparing to select). Current temporal window approach (1.5s) captures local patterns but lacks global context.

**Research Direction:** Hierarchical intent models with multiple time scales:
- Short window (500ms): gesture detection
- Medium window (1.5s): intent classification (current)
- Long window (30s): session context (reading mode, navigation mode, fatigue state)

**Potential Outcome:** Reduce false positive rate from 0.1% to < 0.01% by incorporating session-level context.

### 2.2 Zero-Shot Calibration

**Problem:** Current uncalibrated accuracy (~3° MAE) is insufficient for small targets (<2cm on screen). Calibration takes 30 seconds and requires sustained effort — barrier for severe disability users.

**Research Direction:** Appearance-normalization using 3D face geometry to compensate for user variation without explicit calibration. Neural calibration (learn user mapping from first 30 seconds of use, not explicit calibration points).

**Related Work:** Few-shot gaze adaptation (Guo et al., 2020), meta-learning for personalization.

**Potential Outcome:** ≤ 1.5° MAE without any explicit calibration step.

### 2.3 Gaze Estimation Under Extreme Conditions

**Problem:** Current models degrade significantly with:
- Very low lighting (< 10 lux)
- Thick-framed glasses with reflections
- Extreme head poses (>45°)
- Non-frontal camera angles (phone, tablet)

**Research Direction:** Lighting-invariant gaze estimation using 3D face priors + domain adaptation. Synthetic data generation for rare conditions (UnityEyes-2 or Blender-based pipeline).

**Potential Outcome:** Maintain < 4° MAE in conditions where current models produce 8–15°.

### 2.4 Multimodal Intent Disambiguation

**Problem:** Gaze alone is ambiguous. Head pose, pupil dilation, micro-expressions provide additional signal. No existing model fuses all of these with temporal attention.

**Research Direction:** Multi-modal fusion model combining:
- Gaze vector (current)
- Head pose (yaw, pitch, roll)
- Pupil diameter (arousal/attention proxy)
- Eyebrow dynamics
- Micro-saccade pattern

**Potential Outcome:** 5–10% intent accuracy improvement over gaze-only model.

### 2.5 Fatigue and State Detection

**Problem:** User gaze behavior changes significantly with fatigue, medication, stress, and time of day. A static threshold system fails fatigued users at the times they need assistive technology most.

**Research Direction:** Online fatigue detection from gaze kinematics (saccade velocity, fixation duration, PERCLOS metric). Adaptive threshold adjustment based on detected fatigue level.

**Evidence Base:** Sirevaag & Stern (2000) demonstrated PERCLOS (% time eyes closed) as a reliable drowsiness measure. Application to assistive tech fatigue is novel.

**Potential Outcome:** 30% reduction in false positives during fatigued use.

---

## 3. Research Roadmap

### 3.1 2025 — Foundations

| Research Topic | Type | Priority | Outcome |
|---|---|---|---|
| Publish EPID dataset paper | Dataset | P0 | CVPR / NeurIPS datasets track |
| Publish EyeNav technical paper | System | P0 | CHI 2026 |
| Zero-shot calibration prototype | Model | P1 | Internal benchmark |
| Fatigue detection baseline | Model | P1 | Internal benchmark |
| Bias evaluation across 6 demographic groups | Evaluation | P0 | Published with EPID |

### 3.2 2026 — Expanded Intent Model

| Research Topic | Type | Priority | Outcome |
|---|---|---|---|
| Hierarchical intent model (3-timescale) | Model | P0 | ICCV 2026 |
| Multimodal fusion (gaze + head + pupil) | Model | P1 | ECCV 2026 |
| Domain adaptation for extreme conditions | Model | P1 | WACV 2026 |
| Neural calibration (few-shot) | Model | P0 | CVPR 2026 |
| Longitudinal user study (6-month) | User study | P0 | CHI 2027 |

### 3.3 2027 — Mobile and Edge

| Research Topic | Type | Priority | Outcome |
|---|---|---|---|
| Sub-10MB gaze model for mobile | Model compression | P0 | MobileNet-style gaze |
| TensorRT deployment on Jetson | Edge AI | P1 | Embedded benchmark |
| Real-time on-device training (personalization) | Learning | P1 | ICLR 2027 |
| AR/VR gaze with vergence | Gaze | P0 | ISMAR 2027 |
| Nystagmus-specific model | Accessibility | P1 | Accessibility & Computing 2027 |

### 3.4 2028 — Clinical Translation

| Research Topic | Type | Priority | Outcome |
|---|---|---|---|
| ALS clinical trial partnership | Clinical | P0 | IRB-approved study |
| AAC (Augmentative Communication) integration | Integration | P0 | RESNA 2028 |
| EMG + gaze fusion for locked-in syndrome | Multimodal | P1 | Nature Digital Medicine |
| Social gaze (multi-person awareness) | Social HCI | P2 | CHI 2028 |

### 3.5 2029–2030 — Future Frontiers

| Research Topic | Type | Notes |
|---|---|---|
| Neural interface (BCI) + gaze fusion | Speculative | 10-year horizon |
| Gaze-based authentication | Security | Privacy-safe biometric |
| Attention-driven UI adaptation | Adaptive UI | UI reshapes based on gaze |
| Gaze language (standardized gesture language) | HCI theory | Beyond commands |
| Global gaze dataset (1B+ frames) | Dataset | Community effort |

---

## 4. Publication Strategy

### 4.1 Target Venues

| Venue | Focus | Deadline (approx.) |
|---|---|---|
| CHI (ACM SIGCHI) | HCI, accessibility, user studies | September |
| CVPR | Computer vision, gaze estimation | November |
| ICCV | Computer vision, deep learning | March |
| NeurIPS | Machine learning, datasets | May |
| ECCV | European CV conference | March |
| ISMAR | Augmented and mixed reality | May |
| ASSETS (ACM SIGACCESS) | Accessibility | April |

### 4.2 Publication Priority

1. **EPID Dataset Paper** — Establish EyeNav's data contribution to the field. Open-source the dataset (with consent). This builds community trust and citation impact.

2. **Technical Whitepaper** — Full system paper: architecture, evaluation, user study. Target CHI 2026.

3. **Zero-Shot Calibration** — High scientific novelty. Target CVPR 2026.

4. **Hierarchical Intent Model** — Novel architecture contribution. Target ICCV 2026.

5. **Clinical Study (ALS)** — High-impact application paper. Target Nature Digital Medicine.

### 4.3 Open Science Commitment

EyeNav commits to:
- Publishing dataset papers with dataset release (community benefit > IP protection for datasets)
- Publishing evaluation code alongside papers (reproducibility)
- Preprint on arXiv before conference publication
- Model weights released for academic use where not core IP

---

## 5. Research Infrastructure

### 5.1 Compute Budget Estimate

| Resource | Purpose | Estimated Cost/Year |
|---|---|---|
| GPU cluster (4× A100) | Model training | $60,000 (cloud) or $120,000 (owned) |
| Storage (100TB NVMe) | EPID dataset | $30,000 |
| Annotation platform | EPID labeling | $20,000 |
| A/B testing infrastructure | Production experiments | $5,000 |
| MLflow server | Experiment tracking | $2,000 |
| **Total** | | **~$117,000/year** |

### 5.2 Academic Partnerships

Target partnerships with:
- MIT CSAIL — Gaze and attention research
- Stanford HCI Group — Accessibility and interaction
- CMU HCII — Human-computer interaction
- ETH Zürich — Computer vision (home of ETH-XGaze)
- University of Cambridge — Eye movement neuroscience

---

## 6. Patent Strategy vs. Open Science

**Principle:** Core algorithms (intent inference, safety filter design) should be patented to protect commercial IP. Non-core contributions (dataset, evaluation benchmarks) should be published openly.

| Contribution | Strategy | Reason |
|---|---|---|
| Intent recognition architecture | Patent | Core commercial IP |
| Safety filter design | Patent | Core commercial IP |
| Zero-shot calibration | Patent (if novel) | High commercial value |
| EPID Dataset | Open science | Community goodwill, citations |
| Evaluation benchmarks | Open science | Industry adoption |
| Gaze estimation improvements | Selective | Depends on novelty |
