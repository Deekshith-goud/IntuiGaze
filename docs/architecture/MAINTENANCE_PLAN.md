# EyeNav — Maintenance Plan

**Document Version:** 1.0  
**Status:** Approved  
**Owner:** Engineering Leadership  
**Last Updated:** 2024-Q4  

---

## 1. Overview

This Maintenance Plan defines:
- How EyeNav is maintained after each release
- Responsibilities for bug triage, patch releases, and dependency updates
- Long-term support (LTS) policies
- Infrastructure maintenance
- Model maintenance and retraining schedules

---

## 2. Versioning Policy

EyeNav uses Semantic Versioning (SemVer 2.0):

```
MAJOR.MINOR.PATCH
  │      │     └── Bug fixes, no API change
  │      └──────── New features, backward compatible
  └─────────────── Breaking changes
```

**Release cadence:**

| Type | Cadence | Example |
|---|---|---|
| Patch release | As needed (critical bugs/security) | 1.0.1 |
| Minor release | Every 3 months | 1.1.0 |
| Major release | Every 12–18 months | 2.0.0 |

---

## 3. Support Policy

| Version | Support Type | Duration |
|---|---|---|
| Current release | Full support (bugs + security) | Until next minor |
| Previous minor | Security fixes only | 6 months |
| Current LTS | Full support | 24 months |
| Older releases | End of life | No support |

**LTS designation:** Every second major version (v2.0, v4.0) receives 24-month full support.

---

## 4. Bug Triage Process

### 4.1 Severity Levels

| Severity | Description | Response Time | Resolution Target |
|---|---|---|---|
| P0 — Critical | Data loss, security vulnerability, safety failure | 4 hours | 24 hours (emergency patch) |
| P1 — High | Feature broken for significant user group | 24 hours | 7 days (patch release) |
| P2 — Medium | Feature partially broken, workaround exists | 72 hours | 30 days (next minor) |
| P3 — Low | Minor cosmetic or edge-case issue | 1 week | Next major or backlog |

### 4.2 Safety-Critical Bug Policy

Any bug affecting the safety system (safety.py, emergency stop, false positive rate) is automatically P0 regardless of apparent scope. Safety bugs:

1. Get reported immediately to safety review lead
2. Require root cause analysis before patch
3. Require regression test addition before merge
4. Require safety lead sign-off before release

### 4.3 Bug Report Channels

- GitHub Issues (public — for non-security bugs)
- security@eyenav.ai (private — for security vulnerabilities)
- Responsible disclosure policy: 90-day embargo before publication

---

## 5. Dependency Maintenance

### 5.1 Automated Dependency Scanning

GitHub Dependabot configured to:
- Check for security updates daily
- Auto-create PRs for patch updates
- Alert on critical CVEs immediately

### 5.2 Dependency Update Policy

| Package Type | Update Approach |
|---|---|
| Security patch | Auto-merge after CI passes |
| Non-breaking patch | Weekly batch merge |
| Minor version | Manual review + test |
| Major version | Planned upgrade cycle |
| ML/ONNX Runtime | Validate model compatibility before upgrade |

### 5.3 Python Version Support

| Python Version | Status |
|---|---|
| 3.11 | Minimum supported |
| 3.12 | Fully supported |
| 3.13+ | Added when stable |

---

## 6. Model Maintenance

### 6.1 Model Performance Monitoring

Production models are monitored continuously:
- Confidence score distribution (drift indicator)
- False positive rate (safety metric)
- Intent classification distribution (concept drift)
- Gaze accuracy sample (periodic manual evaluation)

**Alert thresholds:**
- Confidence mean drops > 10% from baseline → review
- False positive rate > 0.15% → immediate investigation
- Classification distribution shifts > 15% → concept drift review

### 6.2 Model Retraining Schedule

| Model | Retraining Trigger |
|---|---|
| Gaze (L2CS) | New dataset available or MAE regression |
| Blink (EAR-CNN) | Accuracy < 97% on test set |
| Intent (Transformer) | New EPID data (quarterly batch) |
| Eyebrow (MLP) | Manual review every 6 months |

### 6.3 Model Deprecation

When a model is replaced:
1. New model runs in shadow mode (no commands) for 2 weeks
2. A/B test with subset of users
3. Gradual rollout (10% → 25% → 50% → 100%)
4. Old model kept in registry for 6 months (rollback capability)

---

## 7. Infrastructure Maintenance

### 7.1 Monthly Tasks

- [ ] Review and rotate any API keys or secrets
- [ ] Review CI/CD pipeline for failures or slowdowns
- [ ] Update Docker base images to latest security patches
- [ ] Review Grafana dashboards for anomalies
- [ ] Database backup verification

### 7.2 Quarterly Tasks

- [ ] Full dependency audit (`pip-audit`)
- [ ] Security penetration test (API server mode)
- [ ] Load test to verify performance under increased demand
- [ ] Model performance review
- [ ] Documentation review for accuracy

### 7.3 Annual Tasks

- [ ] Full security audit (external pen tester)
- [ ] Privacy policy review (legal counsel)
- [ ] Accessibility audit (external auditor + real users)
- [ ] Business model review

---

## 8. End-of-Life Process

When a version reaches End of Life:

1. 6-month advance notice to users
2. Migration guide published
3. Final security patch release
4. Version archived (source + binaries preserved for 10 years)
5. Documentation archived (accessible, read-only)

---

## 9. On-Call Responsibility

For production server deployments:

| Time | Coverage |
|---|---|
| Business hours (9–6 local) | Full engineering team |
| Evenings/weekends | On-call rotation (P0/P1 only) |
| Holidays | Designated on-call |

Escalation path: On-call → Engineering Lead → CTO (P0 only)

---

## 10. Maintenance Knowledge Base

All maintenance procedures documented at:
- `docs/guides/RUNBOOK.md` — Operational procedures
- `docs/guides/INCIDENT_RESPONSE.md` — Incident management
- GitHub Wiki — Living documentation for ops team
