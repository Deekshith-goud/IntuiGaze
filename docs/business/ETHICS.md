# EyeNav — Ethics Assessment

**Document Version:** 1.0  
**Status:** Draft — Pending External Review  
**Owner:** Ethics Committee  
**Last Updated:** 2024-Q4  
**Classification:** Public  

---

## 1. Purpose

This document provides a systematic ethical assessment of EyeNav — its technology, data practices, deployment contexts, and potential harms. It is intended to be reviewed by an external ethics board before any public deployment.

---

## 2. Ethical Framework

EyeNav's ethics framework is grounded in:

1. **ACM Code of Ethics and Professional Conduct** (2018)
2. **IEEE Ethically Aligned Design** (2019)
3. **EU AI Act** principles (high-risk AI requirements)
4. **GDPR** and global biometric data regulations
5. **Disability Rights Framework** (UN CRPD, ADA, EAA)

---

## 3. Benefit Analysis

### Primary Benefits

| Benefit | Beneficiary | Magnitude |
|---|---|---|
| Digital independence for motor-impaired users | Accessibility users | Very High |
| Hands-free control in safety-critical contexts | Surgeons, pilots, industrial workers | High |
| Cost reduction for assistive technology | Low-income users | Very High |
| Novel interaction paradigm for AR/VR | General consumers | Medium |
| Research advancement in gaze/HCI | Research community | High |

### Potential for Positive Impact

EyeNav has the potential to provide meaningful digital access to millions of people globally who currently cannot fully use digital devices due to motor impairment. This aligns with:
- UN Sustainable Development Goal 10: Reduced Inequalities
- UN SDG 3: Good Health and Well-Being
- UN CRPD Article 9: Accessibility

---

## 4. Risk and Harm Analysis

### 4.1 Privacy Risks

**Risk: Eye movement data reveals cognitive and medical information**

Eye movements reveal:
- Reading patterns and comprehension
- Emotional states (arousal, attention, stress)
- Neurological conditions (Parkinson's, ALS progression, early Alzheimer's markers)
- Fatigue and intoxication
- Covert attention (what you look at, not just click on)
- Potential deception detection in research contexts

This is **highly sensitive biometric data** — potentially more sensitive than fingerprints because it cannot be changed.

**Mitigation:**
- Process entirely on-device by default
- Never transmit gaze data to servers without explicit, informed, granular consent
- Do not store raw gaze data to disk (process and discard)
- Make it technically impossible for third-party apps using EyeNav SDK to receive raw gaze
- Provide data subject rights (access, portability, deletion)
- Annual privacy audit

**Risk Level: CRITICAL — requires maximum protection**

---

### 4.2 Accessibility Harm Risks

**Risk: System that is supposed to help accessibility users harms them instead**

Specific harms:
- **False positives** trigger unwanted actions → data loss, navigation errors, frustration
- **Calibration failure** leaves user unable to interact at all → lock-out
- **Fatigue-induced degradation** → system becomes unreliable precisely when user needs it most
- **Failure in high-stakes moment** (e.g., emergency communication) → safety failure

**Mitigation:**
- False positive rate: ≤ 0.1% (safety-critical target)
- Graceful degradation: never fail completely — provide fallback modes
- Emergency stop: always available, works even if main system fails
- Keyboard fallback: never lock user out from non-eye input methods
- Extensive accessibility user testing before release
- Users control all thresholds

**Risk Level: HIGH — core engineering priority**

---

### 4.3 Misuse Risks

**Risk: Technology repurposed for surveillance**

Eye tracking can be used for:
- Monitoring employee attention and productivity
- Detecting deception in interrogation
- Advertising attention tracking without consent
- Covert tracking in public spaces

**Mitigation:**
- Prohibited Uses Policy in license and Terms of Service
- SDK contracts prohibit surveillance applications
- Technical constraints: no raw gaze export API
- Transparency requirement: users must be informed when EyeNav is active
- No server-side gaze storage possible in default configuration
- Report mechanism for misuse

**Risk Level: HIGH — requires legal and technical countermeasures**

---

### 4.4 Algorithmic Bias Risks

**Risk: System performs differently across demographic groups**

Known bias sources in gaze/face models:
- Training datasets over-represent Western subjects (lighter skin tones, rounder eye shapes)
- IR-based datasets have worse performance for darker skin tones (known melanin absorption issue)
- Age-related bias: children's and elderly gaze patterns differ from training data
- Disability-related bias: abnormal eye movement patterns (nystagmus, strabismus, ptosis) not in training data

**Mitigation:**
- Diverse dataset recruitment (EPID specification mandates diversity)
- Stratified evaluation: always report performance by demographic group
- Bias threshold: no group may be >5% worse than overall accuracy before release
- Partner with disability organizations for specialized testing
- Publish bias evaluation results publicly

**Risk Level: HIGH — core research priority**

---

### 4.5 Dependency and Abandonment Risks

**Risk: Accessibility users become dependent, then EyeNav is discontinued**

**Mitigation:**
- Open source core model ensures survival even if EyeNav company dissolves
- Model weights publicly released
- SDK documented for community continuation
- No lock-in to EyeNav infrastructure

**Risk Level: MEDIUM**

---

### 4.6 Medical Device Classification Risk

**Risk: EyeNav's accessibility features may trigger medical device regulation (FDA, MDR)**

In some jurisdictions, software intended to compensate for disability may be classified as a medical device, requiring clinical trials and regulatory approval.

**Mitigation:**
- EyeNav is positioned as an assistive technology, not a medical device
- Marketing materials must not make medical claims
- Legal counsel engaged to assess regulatory status per jurisdiction
- If medical device classification triggered, initiate regulatory pathway

**Risk Level: MEDIUM — requires legal monitoring**

---

## 5. AI Transparency

### What is transparent to users:

- When EyeNav is active (always visible indicator)
- What commands have been executed (accessible command history)
- Why a command was or was not executed (explainability view)
- What data is collected (settings panel)
- Which model made which decision (optional technical view)

### What is NOT hidden:

- The system's limitations and known failure modes
- The approximate false positive rate
- When the system is uncertain (low confidence displayed)

---

## 6. Consent Architecture

### Informed Consent Layers

**Level 0 — Basic Use (no consent required beyond terms):**
- Local gaze processing only
- No data storage

**Level 1 — Calibration Storage:**
- Calibration data stored locally
- Explicit acceptance required

**Level 2 — Improvement Contribution (opt-in):**
- Anonymized performance metrics shared
- Differential privacy applied
- Clear opt-in with explanation

**Level 3 — Research Participation (separate consent):**
- Structured session participation
- Full ethics review process
- Compensation provided

---

## 7. Accessibility Rights Statement

EyeNav is committed to the following:

1. **Users control their technology** — all thresholds, behaviors, and data practices are controllable by the user
2. **No paternalism** — the system does not override user preferences
3. **Transparency about failure** — when the system fails, it fails informatively
4. **No extraction** — users' gaze data is not extracted or monetized
5. **Community governance** — disability advocacy organizations will have advisory roles in product decisions

---

## 8. Responsible AI Checklist

- [ ] Privacy Impact Assessment completed
- [ ] Bias evaluation completed across demographic groups
- [ ] Accessibility user testing completed (≥ 100 users)
- [ ] Third-party ethics review completed
- [ ] Legal review for jurisdiction-specific compliance
- [ ] Prohibited uses policy published
- [ ] Transparency documentation published
- [ ] Incident response plan documented
- [ ] Post-deployment monitoring plan active
- [ ] Annual ethics review scheduled

---

## 9. Future Ethical Considerations

### Emotion Recognition
EyeNav will explicitly NOT implement emotion recognition from eye movements in any commercial product. This is reserved for research only, with separate ethics review required.

### Neurological Condition Detection
EyeNav's system may, over time, accumulate data that could theoretically detect neurological conditions (early Alzheimer's markers, Parkinson's progression). This capability will:
- Never be implemented without medical ethics review
- Never be implemented without IRB approval
- Never be implemented without separate, explicit, fully informed user consent
- Only be developed in partnership with clinical researchers

### Workplace Monitoring
EyeNav SDK licenses will explicitly prohibit use for workplace monitoring, including attention tracking, productivity monitoring, or any form of employee surveillance without individual employee consent.

---

## 10. References

1. ACM. (2018). ACM Code of Ethics and Professional Conduct.
2. IEEE. (2019). Ethically Aligned Design, First Edition.
3. European Commission. (2021). Proposal for an AI Act.
4. Crawford, K., & Schultz, J. (2019). AI Now Report 2019.
5. Jacobs, M., & Wallach, H. (2021). Measurement and Fairness. FAccT 2021.
6. UN CRPD. (2006). Convention on the Rights of Persons with Disabilities.
7. Gebru, T., et al. (2020). Datasheets for Datasets.
8. Eubanks, V. (2018). Automating Inequality.
