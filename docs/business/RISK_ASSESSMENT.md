# EyeNav — Risk Assessment & Threat Model

**Document Version:** 1.0  
**Status:** Active  
**Owner:** Security & Safety Teams  
**Last Updated:** 2024-Q4  

---

## 1. Risk Categories

### 1.1 Safety Risks

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| SR-001 | False positive commands cause data loss | Medium | Critical | 6-layer safety filter; ≤ 0.1% FPR target |
| SR-002 | System fails during emergency communication | Low | Critical | Emergency stop always available; keyboard fallback |
| SR-003 | Fatigue causes accuracy degradation | High | High | Fatigue monitoring; adaptive thresholds |
| SR-004 | Medical condition (nystagmus) causes instability | Low | High | Validate with pathological users; graceful fallback |
| SR-005 | Calibration failure locks out user | Medium | High | Uncalibrated fallback mode always available |

### 1.2 Privacy Risks

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| PR-001 | Gaze data intercepted in transit | Low | Critical | On-device processing default; TLS 1.3 if transmitted |
| PR-002 | Model inference reveals health conditions | Low | High | On-device; no data leaves device; no health claims |
| PR-003 | Third-party SDK accesses raw gaze | Medium | High | SDK API does not expose raw gaze |
| PR-004 | Calibration profile used for re-identification | Low | Medium | Profiles are geometric parameters, not biometric templates |
| PR-005 | Regulatory classification as biometric processor | Medium | High | Legal counsel engaged; GDPR Article 9 compliance |

### 1.3 Technical Risks

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| TR-001 | Accuracy degrades on low-quality webcam | High | High | Test matrix with 20+ camera models |
| TR-002 | GPU requirement emerges for production quality | Low | High | Profile CPU usage; ONNX quantization |
| TR-003 | ONNX Runtime incompatibility on target platform | Medium | High | Validate early; pin version; fallback PyTorch |
| TR-004 | Model concept drift in production | Medium | Medium | Monitoring; drift detection; continuous evaluation |
| TR-005 | OS API breaking change breaks integration | Medium | High | Abstract OS layer; version-specific adapters |

### 1.4 Business Risks

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| BR-001 | Competitor launches superior product | Medium | High | Speed to OSS; community moat; patent filing |
| BR-002 | Regulatory classification as medical device | Medium | High | Legal counsel; feature scoping; accessibility positioning |
| BR-003 | Dataset bias causes discriminatory outcomes | Medium | Critical | Diversity requirements; bias evaluation; publish results |
| BR-004 | Key personnel departure | Low | High | Documentation; knowledge transfer; bus factor reduction |
| BR-005 | Funding gap delays development | Medium | Medium | Grant applications; revenue from SDK early |

---

## 2. Threat Model

### 2.1 Threat Actors

| Actor | Motivation | Capability | Concern |
|---|---|---|---|
| Malicious SDK consumer | Surveillance, data extraction | High | Abuse of gaze API |
| Automated exploit | Data exfiltration | Medium | Injection through config/input |
| Insider threat | IP theft, sabotage | Low | Access to model weights |
| Nation-state | Surveillance capability | High | Embedded hardware attacks |

### 2.2 Attack Surface

1. **Configuration files**: YAML injection → Schema validation + HMAC integrity check
2. **ONNX model files**: Malicious model → Signature verification before loading
3. **API endpoints**: Unauthorized access → JWT authentication; rate limiting
4. **OS integration**: Privilege escalation → No admin rights required; limited API surface
5. **Camera input**: Adversarial frames → Input validation; anomaly detection

### 2.3 Security Controls

| Control | Implementation | Covers |
|---|---|---|
| Input validation | Pydantic schemas for all inputs | Config, API requests |
| ONNX signature | SHA256 hash verification | Model loading |
| API authentication | JWT (server mode) | REST + WebSocket endpoints |
| Rate limiting | Per-session limits | API abuse |
| No shell execution | subprocess with allowlist | No arbitrary commands |
| TLS 1.3 | If any network communication | Data in transit |
| AES-256 | Local storage of profiles | Data at rest |
| Audit logging | All command executions | Forensics |

---

## 3. Failure Analysis (FMEA)

### Safety Filter Failure Modes

| Failure | Mode | Effect | Severity | Detection | Mitigation |
|---|---|---|---|---|---|
| Confidence model drift | Silent | FPR increase | Critical | Monitoring dashboard | Recalibration alert |
| EAR threshold mismatch | Silent | Blink FPs | High | Per-session EAR analysis | Auto-recalibration |
| Safety layer exception | Active | BLOCKED (safe) | Low | Error log | Code review |
| Emergency stop miss | Silent | No stop on closure | Critical | Test suite | Formal verification |

### Pipeline Failure Modes

| Failure | Mode | Effect | Severity | Detection | Mitigation |
|---|---|---|---|---|---|
| Camera disconnect | Active | Pipeline pauses | Medium | Frame timeout | Reconnection loop |
| Face not detected | Silent | No commands | Low | Metric alert | Last-known-pose (500ms) |
| Model load failure | Active | Startup fails | High | Error log | Config validation |
| ONNX runtime crash | Active | Pipeline stops | High | Process monitor | Automatic restart |

---

## 4. Risk Acceptance

| Risk Level | Criteria | Action Required |
|---|---|---|
| Critical | Safety, privacy violations | Must mitigate before any release |
| High | Significant user harm possible | Must mitigate before production |
| Medium | Moderate impact, recoverable | Mitigate before GA |
| Low | Minor impact | Document and monitor |

All Critical risks in this document have mitigations. No Critical risk may be accepted without safety team approval.
