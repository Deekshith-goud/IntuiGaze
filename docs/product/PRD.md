# EyeNav — Product Requirements Document (PRD)

**Document Version:** 1.0  
**Status:** Draft — Pending Engineering Review  
**Owner:** Product Team  
**Last Updated:** 2024-Q4  
**Classification:** Internal  

---

## 1. Executive Summary

EyeNav is an intent-first, vision-based Human Computer Interaction platform. It enables complete hands-free device navigation through eye movements, blink patterns, and eyebrow gestures. This PRD defines all functional requirements, non-functional requirements, constraints, and acceptance criteria for the EyeNav platform v1.0.

---

## 2. Background

Refer to: [VISION.md](VISION.md)

---

## 3. Stakeholders

| Stakeholder | Role | Interest |
|---|---|---|
| Accessibility Users | Primary Users | Core interaction modality |
| General Users | Secondary Users | Hands-free convenience |
| OEM Partners | Integration Partners | Embedded SDK |
| Healthcare Providers | Distribution Partners | Rehabilitation use |
| AR/VR Developers | Third-party Developers | Platform SDK |
| Regulators | Compliance | Privacy, medical device classification |
| Research Community | Collaborators | Open dataset, papers |
| Investors | Funding | Commercial viability |

---

## 4. Target Users

### 4.1 Primary Users — Accessibility

1. **Motor-Impaired Users**: ALS patients, quadriplegics, spinal cord injury, cerebral palsy, and other conditions preventing hand use
2. **Tremor Users**: Parkinson's disease, essential tremor — reducing false inputs from involuntary movement
3. **Prosthetic Users**: Single or double limb amputees
4. **Temporary Mobility Loss**: Post-surgical recovery, fractures, burns

### 4.2 Secondary Users — Contextual Hands-Free

1. **Medical Professionals**: Surgeons, radiologists reviewing imaging
2. **Industrial Workers**: Assembly line, manufacturing, cleanroom
3. **Transportation**: Pilots, truck operators (dashboard interaction)
4. **AR/VR Users**: Interaction within immersive environments
5. **General Consumers**: Power users wanting touch augmentation

---

## 5. Functional Requirements

### FR-001: Camera Acquisition
**Description:** The system must acquire video frames from any V4L2/DirectShow/AVFoundation-compatible camera.  
**Priority:** P0 (Critical)  
**Acceptance Criteria:**
- Supports any USB webcam, built-in laptop webcam, phone front camera
- Minimum resolution: 640×480 @ 15fps
- Preferred resolution: 1280×720 @ 30fps
- Must handle device disconnection gracefully
- Must recover from camera errors without crashing

### FR-002: Face Detection
**Description:** The system must detect one or more faces in each frame.  
**Priority:** P0 (Critical)  
**Acceptance Criteria:**
- Detects faces at distances 30cm – 2m from camera
- Works with multiple faces (returns highest confidence or tracked face)
- Handles partial occlusion (glasses, masks covering mouth)
- Handles varying head poses: ±45° yaw, ±30° pitch, ±20° roll
- Latency ≤ 10ms on Intel Core i5 8th gen

### FR-003: Facial Landmark Extraction
**Description:** Extract 468 facial landmarks per detected face.  
**Priority:** P0 (Critical)  
**Acceptance Criteria:**
- Provides 468 3D landmarks (x, y, z) from MediaPipe Face Mesh or equivalent
- Normalizes landmarks to a canonical face space
- Stable across frames (temporal smoothing applied)
- Latency ≤ 8ms on target hardware

### FR-004: Eye Region Extraction
**Description:** Extract left and right eye regions as normalized image patches.  
**Priority:** P0 (Critical)  
**Acceptance Criteria:**
- Eye region crop: 64×64 pixels minimum, 128×128 preferred
- Normalization: zero-mean, unit variance
- Handles glasses with minimal degradation
- Handles contact lenses
- Handles various iris colors
- Works in ambient light 50–10,000 lux

### FR-005: Blink Detection
**Description:** Detect voluntary and involuntary blinks and classify their type.  
**Priority:** P0 (Critical)  
**Acceptance Criteria:**
- Detects: single blink, double blink, triple blink, long blink (>500ms), very long blink (>2000ms)
- Distinguishes voluntary blinks from involuntary (reflex) blinks
- False positive rate ≤ 0.5% (max 1 false blink detection per 200 frames at 30fps = ~1 per 7 seconds)
- Latency ≤ 5ms
- Works with glasses (including thick frames)

### FR-006: Gaze Estimation
**Description:** Estimate the user's gaze direction in screen coordinates.  
**Priority:** P0 (Critical)  
**Acceptance Criteria:**
- Accuracy ≤ 3° mean angular error (uncalibrated, appearance-based)
- Accuracy ≤ 1° mean angular error (after 30-second calibration)
- Outputs: (x, y) in screen-normalized coordinates [0,1]
- Temporal smoothing: Kalman or one-euro filter applied
- Provides confidence score per estimate

### FR-007: Eyebrow Motion Detection
**Description:** Detect and classify eyebrow states and movements.  
**Priority:** P1 (High)  
**Acceptance Criteria:**
- Detects: neutral, raised-left, raised-right, raised-both, lowered-both, lowered-left, lowered-right
- Works with/without eyebrows (alopecia, full masks)
- False positive rate ≤ 0.1% per session
- Latency ≤ 5ms

### FR-008: Head Pose Estimation
**Description:** Estimate head pose (yaw, pitch, roll) in degrees.  
**Priority:** P1 (High)  
**Acceptance Criteria:**
- Range: Yaw ±60°, Pitch ±45°, Roll ±30°
- Accuracy ≤ 5° MAE
- Used to normalize gaze direction (head + eye = composite gaze)
- Latency ≤ 3ms

### FR-009: Intent Recognition
**Description:** Classify user intent from temporal gesture sequences.  
**Priority:** P0 (Critical)  
**Acceptance Criteria:**
- Classifies intents: Reading, Selecting, Scrolling, Searching, Idle, Activation, Deactivation, Confirmation, Cancellation
- Accuracy ≥ 95% on held-out test set
- Uses temporal context window of 500ms – 3000ms
- Provides confidence score [0, 1] per prediction
- Latency ≤ 50ms (from gesture completion to intent output)

### FR-010: Command Mapping
**Description:** Map recognized intents to system commands.  
**Priority:** P0 (Critical)  
**Acceptance Criteria:**
- Supports commands: Scroll Up/Down, Back, Forward, Select, Enter, Open Menu, Switch Tab, Volume Up/Down, Brightness Up/Down, Home, App Switch, Notifications, Clipboard, Keyboard Navigation, Cursor Mode
- Commands are configurable per user
- Commands are configurable per application context
- Provides extensible plugin API for custom commands

### FR-011: Safety Filter
**Description:** Multi-layer safety system to prevent false command execution.  
**Priority:** P0 (Critical)  
**Acceptance Criteria:**
- Confidence threshold: Command only executes if confidence ≥ user-configured threshold (default: 0.92)
- Cooldown period: Minimum 800ms between same-command repetitions (configurable)
- Dwell confirmation: Optional dwell-based confirmation for high-risk commands (Back, Delete, etc.)
- Emergency stop: 3-second eye closure disables all commands
- Anti-fatigue: Reduces sensitivity after 2 hours of active use
- See [docs/architecture/SAFETY_SYSTEM.md](../architecture/SAFETY_SYSTEM.md) for full specification

### FR-012: Calibration System
**Description:** Rapid per-user calibration for improved accuracy.  
**Priority:** P1 (High)  
**Acceptance Criteria:**
- Uncalibrated mode: Available immediately, accuracy ≤ 3°
- Rapid calibration: 5-point, < 30 seconds, improves to ≤ 1.5°
- Full calibration: 13-point, < 90 seconds, improves to ≤ 1°
- Calibration profiles: Stored, named, and switchable
- Cross-device sync: Profiles synced via encrypted cloud (opt-in)
- Continuous refinement: Accuracy improves passively during use

### FR-013: User Profile Management
**Description:** Persistent, secure user profiles.  
**Priority:** P1 (High)  
**Acceptance Criteria:**
- Stores: calibration data, threshold preferences, command mappings, gesture vocabulary, fatigue adaptation parameters
- Multi-profile support per device
- Profiles encrypted at rest (AES-256)
- Import/export functionality
- Profile deletion with cryptographic erasure

### FR-014: OS Integration Layer
**Description:** Translate commands to OS-level events.  
**Priority:** P0 (Critical)  
**Acceptance Criteria:**
- Windows: Uses Accessibility API + SendInput + UIAutomation
- macOS: Uses Accessibility API + CGEvent + AppKit
- Linux: Uses AT-SPI2 + X11/Wayland
- Android: Uses AccessibilityService API
- iOS: Uses Switch Control API
- No root/admin privileges required for basic operation

### FR-015: Configuration Management
**Description:** Centralized, version-controlled configuration system.  
**Priority:** P1 (High)  
**Acceptance Criteria:**
- YAML-based configuration files
- Schema validation on load
- Environment variable overrides
- Hot-reload for non-critical parameters
- Default configurations for new users

### FR-016: Telemetry & Monitoring (Privacy-Safe)
**Description:** Performance monitoring with privacy guarantees.  
**Priority:** P2 (Medium)  
**Acceptance Criteria:**
- Opt-in only
- No gaze data transmitted
- Aggregated performance metrics only (FPS, latency, error rates)
- Differential privacy applied to any shared metrics
- Full audit trail of what is collected

---

## 6. Non-Functional Requirements

### NFR-001: Latency
- Camera to command execution: ≤ 200ms (p95)
- Camera to gaze estimate: ≤ 33ms (1 frame at 30fps)
- Intent classification: ≤ 50ms from gesture completion
- OS command execution: ≤ 10ms

### NFR-002: Throughput / Frame Rate
- Minimum: 15 FPS (functional but degraded)
- Target: 30 FPS (full feature set)
- Ideal: 60 FPS (smoothest tracking, for AR/VR)

### NFR-003: Resource Constraints
- CPU: ≤ 30% sustained CPU on Intel Core i5 8th gen (single core budget: 20%)
- RAM: ≤ 512MB working set
- GPU: Optional — system MUST function without GPU
- Battery: ≤ 15% additional battery drain per hour on laptop
- Startup time: ≤ 3 seconds to first frame

### NFR-004: Accuracy
- Gaze accuracy (uncalibrated): ≤ 3° angular error
- Gaze accuracy (calibrated): ≤ 1° angular error
- Intent accuracy: ≥ 95% precision and recall
- False positive rate: ≤ 0.1% per session
- False negative rate: ≤ 5% per session (acceptable — user can retry)

### NFR-005: Reliability
- Mean time between failures: ≥ 8 hours continuous operation
- Crash rate: ≤ 0.01% per session
- Graceful degradation: System must continue operating at reduced capability, not crash, when individual modules fail

### NFR-006: Privacy
- No gaze data stored to disk by default
- No gaze data transmitted to any server by default
- All processing local (on-device)
- GDPR compliant
- CCPA compliant
- SOC 2 Type II (future milestone)
- Privacy audit every 6 months

### NFR-007: Security
- No external network connections by default
- Configuration files: integrity-checked via HMAC
- Model files: signature-verified before loading
- API endpoints: authenticated (JWT), rate-limited
- No shell injection possible through any input

### NFR-008: Accessibility
- System must be operable by the user it serves (accessible UI)
- Calibration UI: Compatible with screen readers
- All visual indicators: Color-blind safe
- All alerts: Audio alternatives available
- Keyboard navigation: Full keyboard operability for setup and configuration
- WCAG 2.2 AA compliance for all web-facing interfaces

### NFR-009: Portability
- Must run without modification on: Windows 10+, macOS 12+, Ubuntu 20.04+
- Must run without GPU on all platforms
- Docker containerized deployment option for server mode
- Python 3.11+ required
- No system-level library dependencies beyond OpenCV and camera drivers

### NFR-010: Maintainability
- Test coverage ≥ 80% for all core modules
- Type annotations: 100% for public APIs
- Documentation: Docstrings for all public functions and classes
- Linting: ruff, mypy, no suppressed warnings
- Cyclomatic complexity: ≤ 10 per function

### NFR-011: Scalability
- Server mode: Must handle 1,000 concurrent sessions
- Model serving: Horizontal scaling via Kubernetes
- Dataset pipeline: Must handle 10M+ frames without rewriting

---

## 7. Constraints

### Technical Constraints
- Must work with standard webcams (no IR required for basic operation)
- Must not require GPU for v1.0 deployment
- Must not require internet connectivity for core function
- Python 3.11+ primary implementation language

### Legal / Compliance Constraints
- GDPR: Eye data is biometric — highest protection category
- HIPAA: Must be auditable for healthcare deployments (future)
- European Accessibility Act: Target compliance by 2025
- No collection of minors' biometric data without verifiable parental consent

### Business Constraints
- v1.0 must run on existing hardware (no new device requirement)
- First deployment target: Windows + macOS
- Open source core, commercial SDK

---

## 8. Assumptions

1. Users will primarily use front-facing cameras at 50–80cm distance
2. Lighting conditions are typical office/home environments (not pitch dark without IR)
3. Users can hold their head relatively stable (±30cm movement during use)
4. Single user per session (multi-user future scope)
5. Screen size ranges from 13" laptop to 32" external monitor

---

## 9. Out of Scope (v1.0)

- Emotion detection from eye behavior
- Medical diagnosis features
- Real-time cloud gaze processing
- Smart TV integration
- Automotive embedded system
- iOS app (Switch Control integration only via desktop companion)
- Full AR/VR SDK (design complete, implementation v2.0)

---

## 10. Open Questions

| # | Question | Owner | Priority |
|---|---|---|---|
| OQ-001 | Should we support IR cameras for nighttime use in v1.0? | Engineering | P1 |
| OQ-002 | What is the minimum screen size we guarantee support for? | Product | P2 |
| OQ-003 | How do we handle multi-monitor setups? | Engineering | P1 |
| OQ-004 | What jurisdiction governs biometric data? (EU vs US) | Legal | P0 |
| OQ-005 | Can we partner with Tobii for hardware-accelerated fallback? | Business | P3 |

---

## 11. Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 0.1 | 2024-Q3 | Research Team | Initial draft |
| 1.0 | 2024-Q4 | Product Team | Full PRD |
