# EyeNav — Product Roadmap

**Document Version:** 1.0  
**Status:** Approved  
**Owner:** Product Team  
**Last Updated:** 2024-Q4  

---

## Roadmap Philosophy

EyeNav follows an evidence-driven roadmap. Each milestone must be:
1. **Research-validated** before engineering begins
2. **Benchmarked** before release
3. **Accessibility-tested** with real users before production
4. **Documented** before shipping

We do not ship features; we ship validated, production-grade capabilities.

---

## Milestone Overview

```
Q4 2024 ─── Research & Foundation
    │
Q1 2025 ─── Core Pipeline (Alpha)
    │
Q2 2025 ─── Intent Engine + Safety (Beta)
    │
Q3 2025 ─── Platform Integration (RC)
    │
Q4 2025 ─── v1.0 Production Release
    │
Q1-Q2 2026 ─ v1.1 SDK + Android
    │
Q3-Q4 2026 ─ v2.0 AR/VR + Enterprise
    │
2027+ ────── Clinical + Automotive Research
```

---

## Phase 1 — Research & Foundation (Q4 2024)

### Goals
- Complete all documentation (product, architecture, research)
- Establish dataset strategy
- Identify and acquire all public datasets
- Complete ML architecture decision

### Milestones
- [x] Repository scaffold and structure complete
- [x] Product Vision, PRD, DRD complete
- [x] Market Research complete
- [x] ML Architecture document complete
- [x] Dataset registry complete
- [x] Custom dataset specification complete
- [ ] Ethics review passed
- [ ] Privacy assessment complete
- [ ] Architecture review complete (ADRs finalized)
- [ ] Dataset acquisition scripts ready
- [ ] Development environment setup documented

### Exit Criteria
- All documentation complete
- Architecture Decision Records finalized (ADR-001 through ADR-020)
- Dataset acquisition confirmed (all public datasets accessible)
- Engineering environment reproducible on clean machine

---

## Phase 2 — Core Vision Pipeline (Q1 2025, Alpha)

### Goals
- Working end-to-end pipeline from camera to gaze coordinates
- All individual model modules functional
- Performance benchmarks established

### Milestones
- [ ] Camera acquisition module (FR-001) — complete + tested
- [ ] Face detection module (FR-002) — ≥ 99% detection rate in benchmark
- [ ] Facial landmark module (FR-003) — 468 landmarks at ≥ 30fps
- [ ] Eye region extraction (FR-004) — normalized crops at ≥ 30fps
- [ ] Blink detection (FR-005) — ≥ 98% accuracy
- [ ] Gaze estimation (FR-006) — ≤ 3° uncalibrated error
- [ ] Head pose estimation (FR-008) — ≤ 5° MAE
- [ ] Calibration system (5-point, FR-012)
- [ ] Basic desktop application for testing
- [ ] Unit tests: ≥ 80% coverage on all modules
- [ ] Integration test: full pipeline end-to-end

### Performance Targets (Alpha)
- Pipeline FPS: ≥ 25fps on i5-8250U, no GPU
- Total latency: ≤ 250ms
- RAM: ≤ 512MB

### Exit Criteria
- Pipeline benchmark report produced
- All P0 modules passing tests
- Gaze accuracy meets specification

---

## Phase 3 — Intent Engine + Safety System (Q2 2025, Beta)

### Goals
- Intent recognition engine functional
- Safety system fully implemented
- Command execution for core command set

### Milestones
- [ ] Temporal feature construction complete
- [ ] Initial intent recognition model trained (first dataset pass)
- [ ] Safety filter: confidence gate, cooldown, emergency stop
- [ ] Core commands implemented (Scroll, Select, Back, Forward, Enter)
- [ ] OS integration: Windows and macOS
- [ ] Eyebrow motion detection (FR-007)
- [ ] User profile system (FR-013)
- [ ] Configuration management (FR-015)
- [ ] FastAPI inference server
- [ ] Basic calibration UI

### Beta Testing
- Internal testing: 20 users (including 5 accessibility users)
- Structured usability sessions
- False positive rate measured and reported
- Feedback incorporated before RC

### Exit Criteria
- Intent accuracy ≥ 92% (target ≥ 95% for v1.0)
- False positive rate ≤ 0.5% per session
- Zero crash-to-desktop in 8-hour sessions
- Accessibility users can complete standard navigation tasks

---

## Phase 4 — Platform Integration (Q3 2025, Release Candidate)

### Goals
- Linux support added
- Full feature set from P0 + P1
- Extended user testing
- Documentation complete

### Milestones
- [ ] Linux (Ubuntu 20.04+) OS integration
- [ ] Full settings and configuration UI
- [ ] Extended command set (all P1 commands)
- [ ] Calibration: continuous passive refinement
- [ ] Fatigue adaptation system
- [ ] Python SDK v0.9
- [ ] API documentation complete
- [ ] Security audit
- [ ] Accessibility audit (WCAG 2.2 AA)
- [ ] Pilot with disability organization partners (50 users)
- [ ] Performance regression testing

### Exit Criteria
- Intent accuracy ≥ 95%
- False positive rate ≤ 0.1% per session
- WCAG 2.2 AA audit passed
- Disability pilot: ≥ 80% task completion, ≥ 80% satisfaction
- Zero P0 bugs open

---

## Phase 5 — v1.0 Production Release (Q4 2025)

### Goals
- Production-grade release
- Open source publication
- Research paper submission

### Milestones
- [ ] All v1.0 features complete and tested
- [ ] Production documentation: user guide, developer guide, API reference
- [ ] Benchmark report published
- [ ] Security audit complete — all findings resolved
- [ ] Privacy audit complete
- [ ] Legal review of open source license
- [ ] Research paper submitted to CHI 2026
- [ ] GitHub open source release
- [ ] Community engagement: Discord, forums

### Success Metrics for v1.0
| Metric | Target |
|---|---|
| Gaze accuracy (calibrated) | ≤ 1° angular error |
| Intent accuracy | ≥ 95% |
| False positive rate | ≤ 0.1% per session |
| Pipeline FPS | ≥ 30fps on i5-8250U |
| End-to-end latency (p95) | ≤ 200ms |
| Calibration time | ≤ 30 seconds |
| Setup time (new user) | ≤ 5 minutes |
| User satisfaction (pilot) | ≥ 80% |

---

## Phase 6 — v1.1 SDK & Android (Q1–Q2 2026)

### Features
- Python SDK v1.0 stable
- JavaScript/TypeScript SDK v0.9
- Android AccessibilityService integration
- REST API server stable release
- Docker deployment
- WebSocket API for real-time integration
- Custom command plugin API

---

## Phase 7 — v2.0 Enterprise & AR/VR (Q3–Q4 2026)

### Features
- AR/VR SDK (OpenXR, visionOS)
- Enterprise user management
- SOC 2 Type II certification process
- Flutter mobile app
- Clinical validation study initiation
- Multi-user support

---

## Research Roadmap (2027+)

### Open Research Problems
1. **Appearance-based gaze estimation in unconstrained settings** — Improve uncalibrated accuracy to ≤ 1° without any calibration
2. **Fatigue-robust tracking** — Model that degrades gracefully with eye fatigue and explicitly compensates
3. **Multi-modal intent fusion** — Combining gaze + head motion + micro-expression for richer intent
4. **Continual learning for personalization** — Online adaptation without catastrophic forgetting
5. **Cross-ethnic gaze estimation bias** — Addressing performance gaps across iris colors, skin tones, eye shapes
6. **Pathological gaze patterns** — Models that work with nystagmus, strabismus, ptosis
7. **Privacy-preserving federated gaze learning** — Improve global model from local data without sharing gaze
8. **Cognitive state estimation** — Attention, confusion, cognitive load from eye patterns
9. **Driver monitoring** — Drowsiness, distraction detection for automotive
10. **Low-light operation without IR** — Using computational photography techniques

### Target Publications
- CHI 2026: EyeNav system paper
- ECCV 2026: Novel gaze estimation architecture
- ASSETS 2026: Accessibility user study
- NeurIPS 2026 (workshop): Intent recognition as a new problem formulation

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Accuracy insufficient for accessibility use | Medium | Critical | Extended beta testing; fallback modes |
| False positive rate too high | Medium | Critical | Safety system; conservative thresholds |
| GPU dependency emerges | Low | High | Profile early; ONNX quantization |
| Regulatory classification as medical device | Medium | High | Legal counsel; feature scoping |
| Privacy regulation change | Low | Medium | Privacy-by-design; no data collection |
| Competitor launches superior product | Medium | High | Speed to open source; community moat |
| Model accuracy degrades at low cost webcam | High | High | Test matrix with 20+ camera models |
