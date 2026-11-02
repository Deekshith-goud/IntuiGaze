# EyeNav — Custom Dataset Specification

**Document Version:** 1.0  
**Status:** Draft — Pending IRB Review  
**Owner:** Dataset Engineering Team  
**Last Updated:** 2024-Q4  
**Classification:** Internal  

---

## 1. Rationale

No existing public dataset contains **navigation intent labels** — the core signal EyeNav needs to train its intent recognition engine.

Specifically, we need labeled examples of:
- Reading vs. Selecting vs. Scrolling (looks similar, different intent)
- Voluntary blinks (command) vs. Involuntary blinks (natural)
- Eyebrow gestures associated with navigation intent
- Complex temporal gesture sequences (double blink → back)

This specification describes the complete protocol for creating the EyeNav Proprietary Intent Dataset (EPID).

---

## 2. Dataset Goals

### Target Scale

| Parameter | Target |
|---|---|
| Total subjects | 1,000+ |
| Total sessions | 3,000+ (3 sessions per subject avg) |
| Total frames | 10,000,000+ |
| Total labeled gestures | 500,000+ |
| Geographic diversity | 5+ continents |
| Age range | 5–85 years |
| Gender balance | ≥ 40% each binary gender |

### Diversity Requirements

| Dimension | Required Representation |
|---|---|
| Ethnicity | 6+ major ethnic groups |
| Skin tone | Fitzpatrick scale 1–6 |
| Iris color | Brown, dark brown, hazel, blue, green, grey |
| Glasses | No glasses, prescription, sunglasses, thick frames |
| Contact lenses | Hard and soft lens wearers |
| Facial hair | Various beard/mustache types |
| Head poses | Natural variation (not forced) |
| Lighting conditions | Low light, bright, mixed, outdoor, indoor |
| Camera quality | Low (VGA), medium (720p), high (1080p+) |
| Screen sizes | 13" laptop to 32" desktop monitor |
| Age range | Children (with consent), young adult, middle age, elderly |
| Fatigue states | Alert, moderately tired, fatigued |
| Disability representation | ALS, CP, Parkinson's, spinal injury (with partners) |

---

## 3. Label Taxonomy

### Level 1 — Eye State

```yaml
eye_state:
  open:
    description: "Both eyes fully open, sclera visible"
    EAR_range: [0.25, 0.45]
  
  half_open:
    description: "Eyes partially closed, 30-70% open"
    EAR_range: [0.12, 0.25]
    note: "Common during fatigue"
  
  closed:
    description: "Eyes fully closed, no sclera visible"
    EAR_range: [0.0, 0.12]
```

### Level 2 — Blink Type

```yaml
blink_type:
  involuntary:
    description: "Natural reflex blink (not intentional)"
    duration_ms: [80, 300]
    classification: "NOT a command"
  
  single_voluntary:
    description: "Deliberate single blink held slightly longer than natural"
    duration_ms: [200, 400]
    classification: "Command trigger"
  
  double_blink:
    description: "Two consecutive voluntary blinks within 600ms"
    inter_blink_ms: [150, 600]
    classification: "Command: Back"
  
  triple_blink:
    description: "Three consecutive voluntary blinks within 1200ms"
    inter_blink_ms: [150, 600]
    classification: "Command: Custom"
  
  long_blink:
    description: "Single blink held longer than natural (500ms–2000ms)"
    duration_ms: [500, 2000]
    classification: "Command: Confirm"
  
  very_long_blink:
    description: "Sustained eye closure > 2000ms"
    duration_ms: [2000, 5000]
    classification: "Emergency stop trigger"
```

### Level 3 — Gaze Direction

```yaml
gaze_direction:
  center: "Gaze within 5° of screen center"
  left: "Gaze 5–30° left of center"
  right: "Gaze 5–30° right of center"
  up: "Gaze 5–20° above center"
  down: "Gaze 5–20° below center"
  top_left: "Gaze upper-left quadrant"
  top_right: "Gaze upper-right quadrant"
  bottom_left: "Gaze lower-left quadrant"
  bottom_right: "Gaze lower-right quadrant"
  off_screen: "Gaze outside screen bounds"
```

### Level 4 — Eyebrow State

```yaml
eyebrow_state:
  neutral: "Both eyebrows in resting position"
  raised_left: "Left eyebrow raised >15% from neutral"
  raised_right: "Right eyebrow raised >15% from neutral"
  raised_both: "Both eyebrows raised >15% from neutral"
  lowered_left: "Left eyebrow lowered/furrowed"
  lowered_right: "Right eyebrow lowered/furrowed"
  lowered_both: "Both eyebrows lowered/furrowed"
```

### Level 5 — Intent

```yaml
intent:
  reading:
    description: "User is actively reading text (not commanding)"
    signals: ["left-to-right saccade pattern", "fixations ~250ms", "no blinks"]
    
  selecting:
    description: "User intends to select/click an element"
    signals: ["fixation on UI element >600ms", "single voluntary blink", "high confidence"]
    
  scrolling:
    description: "User wants to scroll content"
    signals: ["gaze at screen edge", "sustained downward gaze", "explicit gesture"]
    sub_types: ["scroll_up", "scroll_down"]
    
  searching:
    description: "User is scanning for content (no command intent)"
    signals: ["large saccades", "short fixations <150ms", "rapid scan pattern"]
    
  idle:
    description: "No navigation intent (eyes open but no active task)"
    signals: ["slow drift", "no saccades", "normal blink rate"]
    
  activation:
    description: "User wants to activate EyeNav command mode"
    signals: ["specific activation gesture"]
    
  deactivation:
    description: "User wants to deactivate EyeNav"
    signals: ["specific deactivation gesture or very long blink"]
    
  confirmation:
    description: "User confirms a pending action"
    signals: ["long voluntary blink after dwell"]
    
  cancellation:
    description: "User cancels a pending action"
    signals: ["gaze break or deliberate gesture"]
    
  navigation:
    description: "Directional navigation intent"
    sub_types: ["nav_left", "nav_right", "nav_up", "nav_down", "nav_back", "nav_forward", "nav_home"]
```

---

## 4. Recording Application Design

### Purpose
A cross-platform desktop application that:
1. Prompts subjects with specific gestures to perform
2. Captures video frames with precise timestamps
3. Auto-labels based on prompt + gesture timing
4. Allows session review and manual correction

### Architecture

```
Recording Application (Python + PySide6)
├── Camera Manager
│   ├── Multi-camera support (USB, built-in)
│   ├── Metadata capture (resolution, FPS, camera model)
│   └── Frame timestamp (microsecond precision)
│
├── Prompt Engine
│   ├── Randomized prompt sequence
│   ├── Visual + audio prompts
│   ├── Timing control (prompt duration, inter-prompt interval)
│   └── Progress tracking
│
├── Auto-Labeler
│   ├── Gesture-to-label mapping
│   ├── Temporal window annotation
│   └── Quality confidence score
│
├── Session Manager
│   ├── Subject metadata capture
│   ├── Consent form display and capture
│   ├── Multi-session tracking
│   └── Data integrity verification (hash)
│
├── Annotation Reviewer
│   ├── Frame-level playback
│   ├── Label correction UI
│   └── Quality rating per sequence
│
└── Export Module
    ├── EyeNav dataset format (HDF5)
    ├── Metadata JSON
    └── Upload to secure storage (optional)
```

### Prompt Sequence Example

```
Session Structure (40 minutes):
├── Calibration (5 min)
│   └── Standard 13-point calibration
├── Passive Phase (10 min)
│   └── Subject reads and browses normally (no prompts)
│   └── Labels: reading, searching, idle
├── Commanded Gesture Phase (20 min)
│   ├── "Please blink once deliberately" × 20
│   ├── "Please blink twice" × 20
│   ├── "Please look left" × 15
│   ├── "Please raise your left eyebrow" × 15
│   ├── "Please scroll down" (using eye nav) × 20
│   └── ... (full gesture set)
└── Validation Phase (5 min)
    └── Full navigation task (evaluates natural use)
```

---

## 5. Recording Protocol

### Equipment Setup
1. Camera positioned at eye level, 60–80cm from subject
2. Background: neutral (not distracting)
3. Lighting: calibrated (photometer reading documented)
4. Subject: seated comfortably
5. Screen: 60–80cm from camera (documentation required)

### Per-Subject Session Protocol

1. **Informed Consent** (10 min)
   - Read consent form
   - Confirm understanding of data use
   - Sign digital consent
   - Copy of consent provided to subject

2. **Demographic Survey** (5 min)
   - Age, gender (self-reported), ethnicity (self-reported)
   - Vision conditions (glasses, contacts, color blindness)
   - Medical conditions relevant to eye movement
   - Prior experience with eye tracking

3. **Equipment Calibration** (5 min)
   - Camera position verified
   - Face detection confirmed
   - Lighting measured

4. **Gaze Calibration** (5 min)
   - 13-point calibration
   - Error reported to subject

5. **Recording Sessions** (3 × 40 min each, different days)
   - Day 1: Alert state (morning)
   - Day 2: Moderately tired (afternoon)
   - Day 3: Varied lighting (one window, one dark room)

6. **Debrief** (5 min)
   - Subject can review/delete their data
   - Payment/compensation provided

---

## 6. Annotation Protocol

### Automated Annotation (Primary)

For prompted sequences:
- Ground truth = prompt content + timing window
- Auto-labeled by Recording Application
- Confidence: based on gesture timing precision

### Manual Annotation (Verification)

10% of sessions manually verified by trained annotators:
- Annotator training: minimum 8 hours + certification test
- Inter-annotator agreement: Cohen's κ ≥ 0.85 required
- Disagreement resolution: third annotator + majority vote

### Annotation Tool
See [annotation/README.md](../../annotation/README.md)

---

## 7. Privacy Protection

### Data Minimization
- Full video frames stored only if consent explicitly given
- Default: eye region crops only (40×40 pixels — no face recognizable)
- Metadata: no PII stored in dataset (replaced with anonymous subject ID)

### Consent Levels

| Level | Data Stored | Consent |
|---|---|---|
| Level 1 (Minimum) | Eye crops only, no face | Required |
| Level 2 (Standard) | Face region, eye crops | Informed consent |
| Level 3 (Research) | Full frame + demographics | Enhanced consent |
| Level 4 (Open) | Level 3 + potential publication | Specific publication consent |

### Data Retention
- Data deleted on subject request (within 72 hours)
- Maximum retention: 5 years from collection date
- After retention period: cryptographic deletion (overwrite + verify)

### Storage
- Encrypted at rest: AES-256
- Encrypted in transit: TLS 1.3
- Access control: Role-based, audited
- Geographic storage: Same jurisdiction as subjects (GDPR compliance)

---

## 8. Dataset Versioning

```
EPID (EyeNav Proprietary Intent Dataset)
├── v0.1 — Initial pilot (50 subjects, internal only)
├── v0.2 — Expanded pilot (200 subjects, validation cohort)
├── v1.0 — Production dataset (1000+ subjects, split published)
├── v1.1 — Accessibility supplement (disability cohort)
└── v2.0 — Extended platform (AR/VR + mobile contexts)
```

### DVC (Data Version Control) Integration
- All dataset versions tracked via DVC
- Dataset SHA256 hashes stored in Git
- Preprocessing scripts versioned alongside data
- Experiment results linked to dataset version

---

## 9. Bias Assessment Protocol

### Required Bias Assessments Before Each Release

1. **Demographic Distribution Analysis**
   - Age histogram vs. target distribution
   - Ethnicity distribution vs. target
   - Gender distribution
   - Disability representation

2. **Performance Stratification**
   - Model accuracy by: age group, ethnicity, glasses/no glasses
   - Report any group with >5% accuracy gap vs. overall

3. **Environmental Bias**
   - Lighting condition distribution
   - Camera quality distribution
   - Time-of-day distribution

4. **Annotation Bias**
   - Inter-annotator agreement by annotator
   - Label distribution (class balance)
   - Any annotator with κ < 0.80 is flagged for re-training

### Bias Mitigation Strategies

- Active sampling: When pilot data shows imbalance, actively recruit underrepresented groups
- Weighted training: Inverse frequency weighting for minority groups
- Stratified evaluation: Always report results stratified by demographic group
- Red team testing: Intentionally test failure cases

---

## 10. Dataset Card (Publication Format)

```yaml
dataset_card:
  name: "EyeNav Proprietary Intent Dataset (EPID)"
  version: "1.0"
  created_by: "EyeNav Research Team"
  date: "2025-Q1"
  purpose: "Training and evaluation of eye-based navigation intent recognition"
  
  size:
    subjects: 1000+
    sessions: 3000+
    frames: 10000000+
    labeled_gestures: 500000+
  
  tasks:
    - gaze_estimation
    - blink_classification
    - intent_recognition
    - eyebrow_detection
  
  languages: [en, es, zh, hi, ar]  # instruction languages
  
  license: "Proprietary — see LICENSE"
  
  citation: |
    @dataset{epid2025,
      title={EyeNav Proprietary Intent Dataset},
      author={EyeNav Research Team},
      year={2025}
    }
  
  ethics_review: "IRB Protocol #XXXX"
  consent_mechanism: "Digital informed consent, Level 2 standard"
  
  known_limitations:
    - "Over-represented: 18-35 age group (reflects recruiting bias)"
    - "Under-represented: Children <12, elderly >70"
    - "No subjects with nystagmus or strabismus in v1.0"
    - "Primarily indoor lighting conditions"
  
  prohibited_uses:
    - "Surveillance"
    - "Emotion recognition without consent"
    - "Medical diagnosis without clinical validation"
    - "Cross-referencing with identity databases"
```

---

## 11. References

1. Bender, E.M., et al. (2021). On the Dangers of Stochastic Parrots: Can Language Models Be Too Big? FAccT 2021.
2. Gebru, T., et al. (2020). Datasheets for Datasets. Communications of the ACM.
3. Mitchell, M., et al. (2019). Model Cards for Model Reporting. FAccT 2019.
4. Rayner, K. (1998). Eye Movements in Reading and Information Processing. Psychological Bulletin.
5. European Data Protection Board. (2020). Guidelines on the targeting of social media users.
