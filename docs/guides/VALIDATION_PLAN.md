# EyeNav — Validation Plan

**Document Version:** 1.0  
**Status:** Approved  
**Owner:** QA + Research Team  
**Last Updated:** 2024-Q4  

---

## 1. Purpose

This Validation Plan defines how EyeNav's performance, safety, and accessibility claims will be verified with real evidence — not assumptions. All claims in the PRD, SRS, and marketing materials must be backed by evidence recorded in this plan.

**Validation Principle:** Every claim must be linked to a specific test, measurement, or study. Unverified claims are NOT approved for public communication.

---

## 2. Validation Scope

| Claim | Document | Validation Method |
|---|---|---|
| ≥ 30fps on i5-8250U | SRS-PERF-001 | Automated benchmark |
| ≤ 200ms command latency (p95) | SRS-PERF-002 | Automated benchmark |
| ≤ 3° gaze MAE (uncalibrated) | FR-006 | Dataset evaluation |
| ≤ 1° gaze MAE (calibrated) | FR-006 | Dataset evaluation |
| ≥ 98% blink detection accuracy | FR-005 | Dataset evaluation |
| ≥ 95% intent accuracy | FR-009 | Dataset evaluation |
| ≤ 0.1% false positive rate | FR-011 | User study |
| ≥ 80% task completion (accessibility) | PRD | Accessibility user study |
| ≥ 80/100 SUS score | PRD | Usability study |
| CPU ≤ 30% sustained | SRS-PERF-004 | Resource monitor |
| RAM ≤ 512MB | SRS-PERF-005 | Resource monitor |
| WCAG 2.2 AA compliant | DRD | Accessibility audit |
| GDPR compliant | Privacy Policy | Legal review |

---

## 3. Validation Methods

### 3.1 Automated Benchmark Validation

**Purpose:** Verify performance requirements (SRS-PERF-*) automatically on every release.

**Procedure:**
1. Run on reference hardware: Intel Core i5-8250U, 8GB RAM, Ubuntu 22.04
2. Warm up pipeline: 10 seconds of operation before measurement
3. Measure: 300 seconds (5 minutes) continuous operation
4. Record: FPS (mean, min), latency (mean, p50, p95, p99), CPU, RAM
5. Compare to requirements
6. Pass/fail per requirement

**Evidence file:** `benchmarks/results/v{VERSION}/benchmark_report.json`

**Pass criteria:**
```
FPS mean ≥ 30
Latency p95 ≤ 200ms
CPU mean ≤ 30%
RAM peak ≤ 512MB
```

### 3.2 Dataset Evaluation

**Purpose:** Verify ML accuracy claims on held-out test sets.

**Procedure (Gaze):**
1. Load held-out test split of ETH-XGaze (never seen during training)
2. Run gaze estimator on each sample
3. Compute MAE (mean angular error in degrees)
4. Stratify by: glasses/no-glasses, lighting conditions, head pose
5. Report: overall MAE, per-group MAE, max error (95th percentile)

**Procedure (Blink):**
1. Load Eyeblink8 test split + EPID blink subset
2. Run blink detector on each clip
3. Compute: precision, recall, F1, false positive rate per 100 frames
4. Report: per-class metrics, overall F1

**Procedure (Intent):**
1. Load EPID test split (stratified — all 9 intents represented proportionally)
2. Run intent engine on each sample (full temporal sequence)
3. Compute: per-class precision, recall, F1, confusion matrix
4. Critical: report false positive rate for "selecting" (most dangerous FP)
5. Stratify by: user group, lighting, session duration

**Evidence files:**
```
evaluation/results/v{VERSION}/gaze_eval.json
evaluation/results/v{VERSION}/blink_eval.json
evaluation/results/v{VERSION}/intent_eval.json
```

### 3.3 User Study — Safety Validation

**Purpose:** Verify ≤ 0.1% false positive rate in real use.

**Design:**
- Participants: 50 (25 accessibility users, 25 able-bodied)
- Duration per participant: 2 hours
- Task: Free navigation using EyeNav for natural tasks (browsing, email, documents)
- Measurement: Automated logging of all executed commands vs. intended commands
- Ground truth: Participant marks intended actions; researcher observes

**Protocol:**
1. Participant consents (IRB approved)
2. 5-minute calibration and familiarization
3. 2-hour free navigation session
4. Post-session interview (SUS questionnaire)
5. Data review: classify each command as intended vs. false positive

**Analysis:**
- False positive rate = unintended commands / total commands per participant
- Report: mean FPR, distribution, worst case, by task type
- Stratify: fatigue (first vs. last 30 minutes)

**Pass criteria:** Mean FPR ≤ 0.1% across all participants.

**Evidence file:** `evaluation/studies/safety_validation_v1.0/results.csv`

### 3.4 Accessibility User Study

**Purpose:** Verify accessibility claims with actual disability users.

**Participants:**
- Minimum 50 participants with upper limb motor impairments
- Recruited via accessibility organization partnerships
- Mix: ALS, Cerebral Palsy, SCI, MS, other

**Tasks (standardized):**
1. Open a web browser
2. Navigate to a specific URL
3. Scroll to find target content
4. Click a specific link
5. Go back in browser history
6. Open application menu
7. Trigger emergency stop, then resume

**Metrics:**
- Task completion rate per task
- Time on task (vs. baseline: keyboard+mouse for reference group)
- Error rate (false positives during task)
- SUS score (System Usability Scale)
- NASA-TLX (cognitive and physical load)
- Open-ended feedback

**Evidence file:** `evaluation/studies/accessibility_v1.0/results.xlsx`

### 3.5 WCAG 2.2 Accessibility Audit

**Purpose:** Verify dashboard UI meets WCAG 2.2 AA.

**Procedure:**
1. Automated audit using axe-core (Playwright script)
2. Manual audit by certified accessibility auditor (IAAP CPACC credential)
3. Test with screen readers: NVDA (Windows), VoiceOver (macOS)
4. Test keyboard-only navigation
5. Test with Windows High Contrast mode

**Evidence file:** `evaluation/accessibility/wcag_audit_v1.0.md`

### 3.6 Legal Review (GDPR, Privacy)

**Purpose:** Validate privacy policy and data handling against GDPR requirements.

**Procedure:**
1. External legal counsel reviews Privacy Policy draft
2. Data processing audit: map all data flows
3. DPA (Data Processing Agreement) template reviewed for B2B
4. GDPR Article 9 compliance (biometric data classification) confirmed

**Evidence:** Legal opinion letter from counsel (stored securely, not in repo)

---

## 4. Validation Timeline

| Validation Activity | Required For | Target Date |
|---|---|---|
| Automated benchmarks | Every release | Automated in CI |
| Dataset evaluation | Every model release | Automated in CI |
| Safety user study (N=50) | v1.0 GA | Q2 2025 |
| Accessibility user study (N=50) | v1.0 GA | Q2 2025 |
| WCAG audit | v1.0 GA | Q1 2025 |
| Legal review (GDPR) | v1.0 GA | Q1 2025 |

---

## 5. Validation Evidence Archive

All validation evidence is stored in:
```
evaluation/
├── benchmarks/          # Performance benchmark results
├── datasets/            # Dataset evaluation results
├── studies/             # User study data (anonymized)
│   ├── safety_v1.0/
│   └── accessibility_v1.0/
└── accessibility/       # WCAG audit reports
```

Evidence is version-controlled in Git (reports) and DVC (large datasets). All user study data is anonymized before storage (IRB requirement).

---

## 6. Claim-to-Evidence Traceability

Every public claim must be traceable to a specific evidence file and commit:

| Claim | Evidence File | Version |
|---|---|---|
| "≥ 95% intent accuracy" | evaluation/datasets/intent_eval.json | v1.0.0 |
| "≤ 200ms latency" | benchmarks/results/v1.0.0/benchmark_report.json | v1.0.0 |
| "≤ 0.1% false positives" | evaluation/studies/safety_v1.0/results.csv | v1.0.0 |
| "WCAG 2.2 AA compliant" | evaluation/accessibility/wcag_audit_v1.0.md | v1.0.0 |

Any claim without a corresponding evidence entry in this table is **not approved for use** in product marketing, press releases, or research papers.
