# EyeNav — Product Vision, Mission & Problem Statement

**Document Version:** 1.0  
**Status:** Approved  
**Owner:** Product Team  
**Last Updated:** 2024-Q4  

---

## 1. Mission

> **Enable complete hands-free digital interaction for every human being, regardless of physical ability, environment, or device — using only the natural movements of their eyes.**

---

## 2. Vision

EyeNav will become the universal intent layer between human cognition and digital systems.

In the next decade, the way humans interact with computers will fundamentally change. Touch interfaces will be augmented — and in many contexts, replaced — by gaze-based intent systems.

The dominant paradigm shift will not be voice (which suffers from privacy concerns and social awkwardness) and not gesture (which requires physical movement).

**The paradigm shift will be gaze.**

EyeNav is positioned to become the platform that powers this transition — analogous to what touch did for mobile in 2007.

---

## 3. Problem Statement

### 3.1 The Hands Problem

Humans increasingly interact with digital systems in contexts where hands are unavailable:

| Context | Why Hands Are Unavailable |
|---|---|
| Surgery | Sterile field |
| Driving | Safety-critical |
| Manufacturing | Holding tools |
| AR/VR | Physical world engagement |
| Mobility impairment | Motor disability |
| Sports | Equipment handling |
| Space/Defense | Suit/equipment constraints |
| Cooking | Food contamination |
| Rehabilitation | Recovery exercises |

Current solutions — voice commands, head tracking, switch access — are either socially stigmatizing, cognitively demanding, low precision, or latency-sensitive.

### 3.2 The Intent Gap

Existing eye tracking systems are fundamentally limited by their design:

**Current Systems Output:**
```
Gaze = (x: 1240, y: 847)
```

**What Systems Actually Need:**
```
Intent = "User wants to scroll down in the document they are reading"
```

This gap — from coordinates to intent — is the core problem EyeNav solves.

### 3.3 The False Positive Problem

Natural eye movement during reading, searching, and general exploration constantly crosses UI elements.

A system that fires commands on gaze contact with buttons would be **unusable**.

False positive commands in eye navigation are not bugs — they are **safety failures** that cause:
- Data loss
- Navigation errors
- User frustration
- Abandonment of the technology
- Accessibility harm to the most vulnerable users

No production eye navigation product has adequately solved this problem. EyeNav's primary engineering priority is solving it.

### 3.4 The Calibration Problem

Every existing eye tracking system requires per-session, per-device calibration — often taking 1–5 minutes. This is unacceptable for:
- First-time users
- Users with motor impairments who find calibration difficult
- Consumer devices where users expect instant usability
- AR/VR where head position constantly changes

EyeNav must solve calibration through:
- Appearance-based gaze estimation (no calibration required for basic function)
- Rapid adaptive calibration (< 30 seconds)
- Persistent calibration profiles synced across devices

---

## 4. Why Now?

Several converging trends make 2024–2026 the optimal window for EyeNav:

1. **Hardware maturity**: Laptop webcams now deliver 1080p 60fps standard. Front cameras on phones hit 12MP+. AR headsets (Apple Vision Pro, Meta Quest 3) include dedicated eye tracking cameras.

2. **Model efficiency**: Models like MediaPipe Face Mesh run at 30fps on mobile CPU. MobileViT and EfficientFormer enable transformer-quality features at edge speeds.

3. **AR/VR adoption**: The AR/VR headset market will reach ~$450B by 2030 (Grand View Research). All major platforms (visionOS, OpenXR) include gaze API hooks but lack intelligent intent layers.

4. **Accessibility legislation**: The European Accessibility Act (EAA) 2025 mandates digital accessibility for all products sold in the EU. EyeNav creates compliance opportunities for device makers.

5. **AI commoditization**: Foundation models and training infrastructure are now accessible. A lean team can build what required 50 researchers 5 years ago.

---

## 5. Positioning

| Dimension | EyeNav | Tobii | Apple Eye Tracking | Mouse/Touch |
|---|---|---|---|---|
| Intent understanding | ✅ Core feature | ❌ Coordinates only | ❌ Limited | ❌ No |
| Calibration-free | ✅ Near-term goal | ❌ Required | ⚠️ Partial | ✅ N/A |
| Edge inference | ✅ Primary mode | ⚠️ Partial | ✅ On-device | ✅ N/A |
| Open platform | ✅ SDK/API | ❌ Proprietary | ❌ Locked | ✅ OS-level |
| Accessibility-first | ✅ Core design | ⚠️ Secondary | ⚠️ Secondary | ❌ Not designed |
| Price point | ✅ Software-only | ❌ $300+ hardware | ❌ Apple-locked | ✅ Free |

---

## 6. Guiding Principles

### P1 — Intent, Not Coordinates
EyeNav outputs user intent classifications, not raw gaze data. This distinction is the product's fundamental differentiator.

### P2 — False Positives Are Critical Failures
The cost of an accidental command is always higher than the cost of a missed command. The system must be designed with extreme false-positive aversion.

### P3 — Accessibility First
EyeNav exists primarily to serve users who need it most — those with motor impairments, ALS, locked-in syndrome, cerebral palsy, and spinal cord injuries. Every feature is evaluated against this standard first.

### P4 — Privacy by Design
Eye movement data is biometric data. It reveals cognitive load, attention, fatigue, medical conditions, and emotional states. EyeNav processes everything on-device by default. No gaze data leaves the device without explicit informed consent.

### P5 — Edge-First
Cloud inference is fallback only. The primary inference pipeline must run at 30fps on a 2019-era laptop CPU without GPU. This ensures:
- Offline functionality
- Privacy preservation
- Low latency
- Cross-device compatibility

### P6 — Universal Compatibility
EyeNav must work with any standard webcam, phone front camera, or embedded AR sensor. No special hardware requirement. No vendor lock-in.

### P7 — Adaptive by Default
No two users have identical eye movement patterns. Calibration, threshold adjustment, and preference learning must happen continuously and transparently.

---

## 7. Success Criteria

EyeNav v1.0 will be considered successful when:

- [ ] Intent classification accuracy ≥ 95% on held-out test set
- [ ] False positive rate ≤ 0.1% per session (< 1 accidental command per 1000 actions)
- [ ] End-to-end command latency ≤ 200ms (p95)
- [ ] Pipeline runs at ≥ 30 FPS on Intel Core i5 (8th gen) without GPU
- [ ] Works without calibration for 80% of users
- [ ] Rapid calibration (< 30 seconds) for remaining 20%
- [ ] Works with standard 720p webcam
- [ ] Successfully deployed to Windows, macOS, Linux
- [ ] Passes accessibility audit against WCAG 2.2 AA
- [ ] Ethical review passed — zero privacy violations in field testing
- [ ] 100 accessibility user pilot with ≥ 80% satisfaction score

---

## 8. Non-Goals (v1.0)

The following are explicitly out of scope for version 1.0:

- Emotion recognition from eye movement (future research)
- Medical diagnosis from gaze patterns (regulatory scope)
- Full AR/VR integration (v2.0)
- Real-time gaze data monetization (never)
- Cloud gaze processing (opt-in only, future)
- Multilingual gaze vocabulary (v2.0)

---

## 9. References

1. Majaranta, P., & Bulling, A. (2014). Eye Tracking and Eye-Based Human–Computer Interaction. *Advances in Physiological Computing*.
2. Krafka, K., et al. (2016). Eye Tracking for Everyone. *CVPR 2016*.
3. Tonsen, M., et al. (2020). Invisibleeye: Mobile Eye Tracking Using Multiple Low-Resolution Cameras. *ACM IMWUT*.
4. Cheng, Y., et al. (2021). Appearance-Based Gaze Estimation. *IEEE TPAMI*.
5. Webber, A.L. (2016). Amblyopia and its treatment. *Clinical and Experimental Optometry*.
6. Grand View Research. (2023). Augmented and Virtual Reality Market Size Report.
7. European Accessibility Act. (2019). Directive (EU) 2019/882.
