# EyeNav — Accessibility Research Report

**Document Version:** 1.0  
**Status:** Approved  
**Owner:** Accessibility Team + HCI Research  
**Last Updated:** 2024-Q4  

---

## 1. Executive Summary

EyeNav's primary value proposition is accessibility. This document synthesizes the research underpinning that claim: the scale of the problem, the limitations of current solutions, the specific user groups EyeNav serves, and the evidence base for eye-based interaction as a viable modality.

**Key Finding:** Approximately 2.5 billion people worldwide live with some form of disability. Of these, an estimated 200+ million have upper limb motor impairments that make traditional touch/pointer interfaces difficult or impossible. Existing eye-tracking solutions are either cost-prohibitive (Tobii: $2,000–$15,000) or insufficiently accurate for reliable navigation. EyeNav's mission is to make intent-driven gaze navigation universally accessible via commodity webcams.

---

## 2. Disability Demographics

### 2.1 Global Scale

| Condition Category | Global Prevalence | Relevance to EyeNav |
|---|---|---|
| Upper limb motor impairment | ~190M | Primary — cannot use mouse/touch |
| ALS / Motor Neuron Disease | ~450,000 | Critical — often fully locked-in |
| Cerebral Palsy | ~17M | Primary — motor control impaired |
| Multiple Sclerosis | ~2.8M | Primary — hand tremor, weakness |
| Spinal Cord Injury | ~5.4M | Primary — paralysis |
| Stroke survivors (motor) | ~80M annually | Primary — hemiplegia |
| Parkinson's Disease | ~10M | Secondary — tremor, rigidity |
| RSI / Chronic Pain | ~100M+ | Secondary — painful typing |
| Fatigue conditions (ME/CFS) | ~17M | Secondary — cognitive/physical fatigue |
| Blindness (legal) | ~43M | Out of scope (audio-first) |

**Total primary target population: ~300 million users globally.**

### 2.2 Age Demographics

| Age Group | Disability Prevalence | Digital Device Usage |
|---|---|---|
| Under 18 | 5.1% (UNICEF) | High (tablets, school) |
| 18–44 | 8.9% (WHO) | Very High (work, social) |
| 45–64 | 24.7% (CDC) | High (work, banking) |
| 65+ | 40.0% (WHO) | Medium (growing rapidly) |

**Key Insight:** Accessibility need grows with age, and digital dependency in older adults is growing. EyeNav serves an expanding market as the global population ages.

---

## 3. Current Solutions & Limitations

### 3.1 Tobii Eye Trackers

**Product:** Tobii Dynavox Eye Gaze (PCEye)  
**Price:** $2,000–$15,000 USD  
**Mechanism:** Near-infrared illumination + dedicated camera  
**Accuracy:** ~0.5° (hardware advantage)  
**Latency:** 8ms  
**Limitations:**
- Cost prohibitive for most users
- Requires dedicated hardware installation
- Limited to desktop
- No intent understanding — simple gaze cursor
- Requires specialist setup

### 3.2 Windows Eye Control (Microsoft)

**Price:** Free (Windows 10+)  
**Mechanism:** Webcam-based (Tobii SDK)  
**Accuracy:** ~2–4° (uncalibrated)  
**Latency:** ~150–300ms  
**Limitations:**
- Gaze cursor only — no intent
- High false positive rate
- Fatiguing to use for long sessions
- No platform support beyond Windows

### 3.3 Switch Access / Scanning

**Mechanism:** Single or multiple button switches to navigate menus  
**Cost:** $20–$200  
**Speed:** Very slow (5–30 seconds per action)  
**Cognitive Load:** High — requires sustained attention  
**Limitations:**
- Extremely slow interaction
- Users with severe fatigue cannot sustain
- Not suitable for complex navigation

### 3.4 Voice Control (Siri, Dragon, Voice Access)

**Mechanism:** Speech recognition to commands  
**Cost:** Free to $250  
**Limitations:**
- Requires speech capability (excludes dysarthria, aphasia, tracheotomy)
- Privacy issues in public
- Noisy environments reduce accuracy
- Cannot be used silently

### 3.5 EyeNav's Differentiation

| Feature | Tobii | Windows Eye Control | Switch | Voice | EyeNav |
|---|---|---|---|---|---|
| Cost | $2,000+ | Free | $20+ | Free | Free |
| Hardware required | Dedicated device | Webcam (some) | Switch | Mic | Standard webcam |
| Intent understanding | None | None | None | Partial | Full |
| False positive rate | Low | High | Low | Medium | Targets ≤ 0.1% |
| Latency | 8ms | 150ms+ | N/A | 500ms+ | ≤ 200ms |
| Platform coverage | Windows | Windows | OS-specific | Wide | Windows, macOS, Linux |
| Reading suppression | No | No | No | No | Yes |

---

## 4. Eye Tracking for HCI — Evidence Base

### 4.1 Foundational Research

**Fitts' Law and Eye Tracking:**  
Ware & Mikaelian (1987) demonstrated that eye movements follow Fitts' Law — acquisition time correlates with target size and distance. This validates gaze as a motor channel for pointing, not merely viewing.

**Midas Touch Problem:**  
Jacob (1990) identified the core challenge of gaze interfaces: every involuntary fixation triggers a command. This is the problem EyeNav's Intent Engine solves. Standard gaze-to-point systems cannot distinguish reading fixations from selecting fixations.

**Dwell Time Solutions:**  
Majaranta & Räihä (2002) surveyed dwell-time selection methods. Minimum effective dwell: 300ms for expert users, 600ms for novice. EyeNav's configurable dwell (200–1000ms) accommodates both.

**Blink as Input:**  
Sibert & Jacob (2000) showed voluntary blinks are distinguishable from involuntary blinks with 90%+ accuracy using timing alone. EyeNav extends this with pattern-based classification (single, double, long, triple).

**Intent vs. Gaze:**  
Veldre et al. (2020) showed that gaze behavior differs measurably when users are reading vs. scanning vs. searching. EyeNav's Intent Engine exploits these temporal signatures.

### 4.2 Muscle Fatigue Research

**Asthenopia (Eye Strain):**  
Rosenfield (2011) documented that sustained voluntary gaze control causes fatigue faster than involuntary viewing. EyeNav's reading suppression and idle state detection are designed to minimize required sustained gaze effort.

**Recommendation:** EyeNav sessions should include automatic rest suggestions after 45 minutes of active navigation. This is implemented as a configurable option in SafetyConfig.

### 4.3 Nystagmus and Pathological Eye Movement

**Nystagmus** (involuntary rhythmic eye oscillation) affects 1 in 1,000 people and presents a challenge for gaze-based interfaces. Standard gaze estimators fail entirely for users with nystagmus.

**Mitigation Strategy:**
- Temporal averaging filter (250ms window) smooths oscillations
- User profile flag `nystagmus_mode: true` in config
- Adaptive calibration with nystagmus-aware polynomial mapping
- Wider dwell zones (configurable per user)

**Evidence:** Larsson et al. (2016) showed that temporal smoothing with 200–300ms windows maintains usable gaze cursor accuracy for congenital nystagmus users.

---

## 5. Fatigue as an Accessibility Dimension

Many EyeNav users have fatigue conditions (ME/CFS, multiple sclerosis, long COVID). For these users:

- Interaction must be effortless — no sustained physical effort
- Session length must be adaptive
- Errors (false positives) cause disproportionate distress
- Recovery from errors must be immediate

**Design Responses in EyeNav:**
1. Reading suppression eliminates the need to suppress natural eye movement
2. Idle state → no command: natural rest does not trigger anything
3. Confidence thresholds prevent low-quality detections reaching commands
4. Emergency stop (eye closure) is both natural and effective

---

## 6. Cognitive Load Research

Sweller's Cognitive Load Theory (1988) is directly relevant: any UI that requires users to track system state, remember commands, and control gaze simultaneously overloads working memory.

**EyeNav Design Response:**
- Status indicator: always visible, glanceable
- Sound feedback: optional audio for confirmations
- Predictable behavior: same gesture always produces same outcome
- Undo: all commands undoable
- No mode switching: intent is inferred, not set by user

---

## 7. WCAG 2.2 Applicability to EyeNav

EyeNav itself must be accessible — a tool for accessibility users cannot have accessibility barriers.

| WCAG 2.2 Guideline | EyeNav Application |
|---|---|
| 1.4.3 Contrast (AA): 4.5:1 text | Dashboard UI: ≥ 7:1 target (AAA) |
| 2.1.1 Keyboard: Full keyboard operability | All dashboard controls keyboard accessible |
| 2.4.3 Focus Order: Logical focus | Dashboard: logical tab order |
| 2.4.7 Focus Visible: Visible focus ring | Dashboard: visible focus ring |
| 2.5.3 Label in Name | All buttons: accessible name matches visible label |
| 3.3.1 Error Identification | Config errors: text description |
| 4.1.3 Status Messages | Gaze state changes: announced to screen readers |

---

## 8. Accessibility Testing Protocol

### 8.1 User Recruitment (Phase 1 Pilot)

Recruit participants across:
- ALS (5+)
- Cerebral Palsy (10+)
- Spinal Cord Injury, C4 or higher (10+)
- Multiple Sclerosis, relapsing-remitting (10+)
- RSI / chronic pain (10+)
- Able-bodied control group (20+)

### 8.2 Metrics

| Metric | Method | Target |
|---|---|---|
| Task completion rate | Standardized navigation tasks | ≥ 80% |
| Errors per session | Automated counting | < 3 false positives/hour |
| User satisfaction | SUS (System Usability Scale) | ≥ 80/100 |
| Fatigue self-report | NASA-TLX | Lower than keyboard baseline |
| Setup time | Timed measurement | ≤ 5 minutes to first successful command |

### 8.3 Partner Organizations

Seek partnerships with:
- ALS Association
- United Cerebral Palsy
- National Multiple Sclerosis Society
- Christopher & Dana Reeve Foundation
- ME Association (for fatigue conditions)

---

## 9. Regulatory Landscape

### 9.1 Section 508 (US Federal)

EyeNav as an assistive technology used in federal contexts must meet Section 508 standards. This covers both the tool itself (accessible UI) and its ability to support users accessing Section 508-compliant content.

### 9.2 EN 301 549 (EU)

European accessibility standard for ICT products. EyeNav targets compliance before EU market entry.

### 9.3 Medical Device Classification

Eye-tracking for navigation is generally **not classified as a medical device** in the US or EU, as it does not diagnose, treat, or prevent medical conditions. However:

- If EyeNav markets specific claims about users with ALS or paralysis, FDA may classify it as a Class I medical device (510k exemption likely applicable)
- Legal counsel must review any clinical claims before publication

---

## 10. Accessibility as Product Advantage

Beyond compliance and ethics, accessibility is a business advantage:

1. **Market size:** 300M+ primary users, growing with aging demographics
2. **Loyalty:** Accessibility users have extremely high product loyalty when a tool works
3. **Institutional procurement:** Hospitals, schools, government agencies buy assistive tech at scale
4. **Press/awards:** Accessibility excellence earns consistent recognition (Apple Design Awards, etc.)
5. **Regulatory moat:** WCAG, Section 508, EN 301 549 compliance is a barrier to entry

**Conclusion:** Accessibility is not a feature to add later. It is a core design constraint that shapes every decision from day one.
