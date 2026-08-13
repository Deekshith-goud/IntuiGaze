# EyeNav — Privacy Policy (Draft)

**Version:** 0.1 Draft  
**Status:** Legal Review Required Before Publication  
**Effective Date:** TBD  
**Last Updated:** 2024-Q4  

---

## Introduction

EyeNav ("we," "our," or "the system") is committed to protecting your privacy. This Privacy Policy explains how EyeNav processes data about you, what data we collect, how we use it, and your rights.

**The most important thing to understand:** EyeNav is designed to process eye movement data **entirely on your device** by default. We do not transmit raw eye movement or gaze data to any server.

---

## 1. What Data EyeNav Processes

### 1.1 Data Processed Locally (On Your Device)

The following data is processed in real-time on your device and is **not stored or transmitted**:

| Data Type | Purpose | Retention |
|---|---|---|
| Camera video frames | Pipeline input | 0 seconds — discarded after processing |
| Eye movement coordinates | Gaze estimation | 0 seconds — processed immediately |
| Blink patterns | Blink detection | 0 seconds — processed immediately |
| Facial landmarks | Feature extraction | 0 seconds — discarded after use |

### 1.2 Data Stored Locally (With Your Consent)

| Data Type | Purpose | Location | Encryption |
|---|---|---|---|
| Calibration profile | Improve accuracy | Local device | AES-256 |
| Threshold preferences | Personalization | Local device | AES-256 |
| Command history (aggregated) | Session statistics | Local device | AES-256 |
| Performance metrics | System health | Local device | AES-256 |

Calibration profiles are the only persistent data. They do not contain raw gaze data — only mathematical transformation parameters.

### 1.3 Data We Never Collect

EyeNav **never** collects:
- Raw gaze coordinates or eye movement sequences
- Video recordings or screenshots
- Personal identifiers beyond what you voluntarily provide
- Health information derived from eye patterns
- Emotional state estimates
- Cognitive state estimates
- Browsing or screen content

---

## 2. Legal Basis for Processing (GDPR)

| Processing Activity | Legal Basis | Article |
|---|---|---|
| On-device gaze processing | Legitimate interest (product function) | Art. 6(1)(f) |
| Calibration storage | Consent | Art. 6(1)(a) |
| Opt-in analytics | Consent | Art. 6(1)(a) |
| Research participation | Consent | Art. 9(2)(a) |

As eye movement data may constitute biometric data under GDPR Article 9, we apply the highest level of protection to all processing.

---

## 3. Opt-In Features (Require Explicit Consent)

### 3.1 Anonymous Performance Metrics

With your explicit consent, EyeNav may collect:
- Pipeline frames per second
- Command execution latency (aggregated, no command content)
- Error rates (no personal data)

This data is:
- Differentially private (ε=1.0)
- Never linked to individual users
- Aggregated before transmission
- Transmissible only over TLS 1.3

### 3.2 Research Participation

Participation in EyeNav research sessions is:
- Always voluntary
- Separately consented
- Described in detail before participation begins
- Withdrawable at any time with full data deletion

---

## 4. Your Rights (GDPR / CCPA)

| Right | How to Exercise |
|---|---|
| Access your data | Settings → Privacy → Export My Data |
| Delete your data | Settings → Privacy → Delete All Data |
| Correct your data | Settings → Profile → Edit |
| Data portability | Settings → Privacy → Export My Data (JSON) |
| Opt out of analytics | Settings → Privacy → Toggle Analytics Off |
| Withdraw consent | Settings → Privacy → Consent Management |

All deletion requests completed within 72 hours.

---

## 5. Data Security

- All locally stored data: AES-256 encryption
- Any network transmission: TLS 1.3
- Model files: Cryptographic signature verification
- No server-side gaze storage possible in default configuration

---

## 6. Children's Privacy

EyeNav is not directed at children under 13. We do not knowingly collect data from children under 13 without verified parental consent. If EyeNav is used as an accessibility tool for a child, a parent or guardian must configure the system.

---

## 7. Contact

Privacy inquiries: privacy@eyenav.ai  
Data Protection Officer: dpo@eyenav.ai  
Postal address: [To be completed before publication]

---

## 8. Updates to This Policy

We will notify users of material changes via:
- In-app notification before effective date
- Email to registered users
- GitHub release notes

*This is a draft document. It must be reviewed by qualified legal counsel before public release.*
