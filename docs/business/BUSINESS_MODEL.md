# EyeNav — Business Model, Investor Pitch & Patent Opportunities

**Document Version:** 1.0  
**Status:** Internal Strategy Document  
**Owner:** Business Team  
**Last Updated:** 2024-Q4  
**Classification:** Confidential  

---

## PART 1 — Business Model

### 1.1 Revenue Streams

#### Stream 1 — Open Core (Free + Commercial SDK)

**Free Tier (Open Source):**
- Core EyeNav library (MIT)
- Basic command set
- Community support
- Self-hosted only

**Commercial SDK License:**
- Target: Software companies embedding EyeNav
- Pricing: $X/device/year or enterprise flat fee
- Includes: Priority support, advanced features, SLA, usage analytics

**Commercial SDK Revenue (5-year projection):**
| Year | SDK Customers | Average ARR | Total SDK Revenue |
|---|---|---|---|
| Y1 | 5 | $20K | $100K |
| Y2 | 25 | $30K | $750K |
| Y3 | 80 | $40K | $3.2M |
| Y4 | 200 | $50K | $10M |
| Y5 | 500 | $60K | $30M |

#### Stream 2 — OEM Hardware Licensing

**Target:** Laptop manufacturers (Dell, HP, Lenovo, ASUS), AR/VR headset makers (Meta, HTC, Pico)

**Model:** Per-device royalty ($1–5 per device shipped with EyeNav enabled)

**Revenue Projection (Y3+):**
- If 1 OEM ships 5M devices/year at $2/device = $10M/year from one OEM

**This is the primary scale mechanism.** One OEM deal transforms the revenue model.

#### Stream 3 — Healthcare / Enterprise SaaS

**Target:** Hospitals (surgical suite integration), rehabilitation centers, VA hospitals

**Model:** Per-facility annual subscription ($5K–$50K/facility/year)

**Revenue (Y3+):**
- 100 facilities × $20K = $2M/year

#### Stream 4 — Research Licensing

**Target:** Universities, research labs, corporate R&D

**Model:** Annual academic license ($2K/year), commercial research ($20K/year)

**Revenue (Y2+):** Modest but builds relationships and validation

---

### 1.2 Cost Structure

**Year 1 Budget Estimate:**

| Category | Annual Cost |
|---|---|
| Engineering (5 FTE) | $750K |
| Research (2 FTE) | $280K |
| Infrastructure (cloud, compute) | $60K |
| Dataset collection | $100K |
| Legal (IP, privacy, contracts) | $80K |
| Operations | $50K |
| Marketing | $30K |
| **Total** | **~$1.35M** |

**Burn Rate:** ~$112K/month

**Runway needed (18 months):** ~$2M seed + $1M grant funding

---

### 1.3 Funding Strategy

| Round | Amount | Timeline | Use |
|---|---|---|---|
| Pre-seed / Angels | $500K | Q1 2025 | 6-month runway, MVP |
| Seed | $2M | Q3 2025 | 18-month runway, v1.0 |
| Series A | $10M | 2026 | Scale, OEM deals, enterprise |
| Grant (NSF, NIH, DARPA) | $1M+ | 2025 | Research + dataset |
| EU Horizon Europe | €2M+ | 2025 | Accessibility research |

---

## PART 2 — Investor Pitch Outline

### Slide 1 — The Problem (30 seconds)

> "1 billion people worldwide have motor disabilities. They interact with computers through expensive ($5,000–$15,000) specialized hardware. We're going to change that."

**Hook:** Show Marcus's (ALS patient persona) daily struggle vs. EyeNav demo.

---

### Slide 2 — The Bigger Picture

> "But this isn't just about disability. We're at the beginning of an era where your eyes become your cursor. AR glasses, surgical suites, cars, smart TVs — none of them have an intelligent eye navigation layer."

**Market:** $4.3B eye tracking market growing at 22% CAGR. $461B AR/VR market where EyeNav is the intent layer.

---

### Slide 3 — Why Now?

1. Webcams hit 1080p standard (hardware ready)
2. Edge AI models run at 30fps on CPU (compute ready)
3. Apple ships Eye Tracking on iOS 18 (market validated)
4. EU Accessibility Act 2025 creates compliance urgency
5. AR/VR adoption accelerating (platform ready)

---

### Slide 4 — The Product

> "EyeNav is not an eye tracker. It understands what you *want* to do."

Show the pipeline: Camera → Intent → Command

Key differentiator: **Intent Recognition** — not just coordinates

Demo: Marcus uses EyeNav to write code.

---

### Slide 5 — Technical Moat

- **Intent Recognition Engine**: No competitor has this
- **Privacy Architecture**: On-device-first is our moat with privacy-conscious customers
- **Open Source Community**: Faster adoption than any proprietary competitor
- **Dataset**: Largest labeled navigation intent dataset (proprietary)
- **Calibration-free**: Goal competitors haven't achieved

---

### Slide 6 — Business Model

| Product | Customer | Price | Timeline |
|---|---|---|---|
| Open Core | Developers | Free | Now |
| Commercial SDK | Software companies | $20-60K/year | Y1 |
| OEM License | Hardware makers | $1-5/device | Y2+ |
| Healthcare SaaS | Hospitals, rehab | $5-50K/facility | Y2+ |

---

### Slide 7 — Traction

- [Q4 2024] Repository live, 1,000 GitHub stars (target)
- [Q1 2025] Alpha release, 50 accessibility users in pilot
- [Q2 2025] Research paper submitted to CHI 2026
- [Q3 2025] First paid SDK customer
- [Q4 2025] v1.0 release, 5,000 users

---

### Slide 8 — Team

- [Founder/CEO]: HCI + ML background
- [CTO]: Computer Vision + systems engineering
- [Chief Scientist]: Eye tracking research, published in top venues
- [Head of Accessibility]: Occupational therapist + disability community advocate
- Advisors: [Tobii alumni], [University HCI lab director], [Accessibility fund manager]

---

### Slide 9 — The Ask

**Seed Round: $2M**

Use of funds:
- 40% Engineering (hire 3 additional engineers)
- 25% Dataset collection (1,000 subjects)
- 20% Research (2 researchers)
- 10% Legal/IP
- 5% Operations

---

### Slide 10 — Vision

> "In 5 years, EyeNav is the intent layer in every AR headset sold. In 10 years, it's how billions of people interact with technology — no hands required."

---

## PART 3 — Patent Opportunities

**Note:** Patent claims require patent attorney review. The following are novel technical contributions that warrant patent investigation.

### PA-001 — Multi-Layer Contextual False Positive Prevention System

**Novel Aspect:** The combination of (a) confidence threshold gating, (b) context-aware suppression, (c) anti-pattern detection, and (d) fatigue-adaptive thresholds as an integrated safety system for eye navigation.

**Why Novel:** Existing eye tracking systems use single-threshold gates. The multi-layer contextual approach, particularly the reading detection suppression and fatigue-adaptive dynamic thresholds, appears novel.

**Prior Art to Check:** Tobii patents on gaze interaction filtering, Apple Eye Tracking patents.

---

### PA-002 — Intent Recognition from Eye Gesture Temporal Sequences

**Novel Aspect:** Classifying high-level user intent (reading, selecting, scrolling) from temporal sequences of low-level eye features using a Transformer-based model with attention-based explainability output.

**Why Novel:** Existing systems classify gaze direction, blink type, or simple gestures. Intent-level classification from temporal sequences using attention is not patented (to our knowledge).

---

### PA-003 — Adaptive Confidence Threshold System Based on Real-Time Fatigue State

**Novel Aspect:** Real-time fatigue detection from eye movement patterns (blink rate, EAR mean, saccade amplitude reduction) combined with automatic confidence threshold adjustment to maintain constant false positive rate despite fatigue.

---

### PA-004 — Calibration-Free Gaze Estimation with Online Adaptation

**Novel Aspect:** An appearance-based gaze estimation system that begins uncalibrated and continuously refines a user-specific mapping layer from implicit feedback (where the user successfully interacts), without explicit calibration sessions.

---

### PA-005 — Emergency Stop via Extended Eye Closure Detection

**Novel Aspect:** A reliable emergency stop mechanism for eye navigation systems triggered specifically by sustained voluntary eye closure patterns, distinguishing from natural blinks and sleep/drowsiness through temporal signature analysis.

---

### PA-006 — Reading Pattern Detection for Intent Disambiguation

**Novel Aspect:** A classifier that distinguishes the reading eye movement pattern (horizontal saccades, specific fixation durations, return saccades) from navigation intent patterns, used to suppress navigation commands during active reading — a novel application of reading pattern research to eye navigation safety.

---

## PART 4 — Competitive Defensive Strategy

### IP Strategy

1. **File provisional patents** for PA-001 through PA-006 in Year 1
2. **Open source core** to create prior art that prevents competitors from patenting obvious improvements
3. **Dataset ownership** as key moat — proprietary dataset cannot be replicated
4. **Publish research** in top venues to establish priority and credibility

### Speed Advantage

- Open source community provides faster iteration than any proprietary competitor
- Research publication establishes priority dates
- OEM relationships create switching cost once embedded

---

## References

1. Grand View Research. (2023). Eye Tracking Market Report.
2. PitchBook. (2023). Assistive Technology Investment Landscape.
3. European Commission. (2023). European Accessibility Act Implementation Guide.
4. USPTO. (2023). Software Patent Guidelines.
