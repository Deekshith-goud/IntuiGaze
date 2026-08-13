# EyeNav — Feature Matrix & Prioritization

**Document Version:** 1.0  
**Status:** Approved  
**Owner:** Product Team  
**Last Updated:** 2024-Q4  

---

## Priority Definitions

| Priority | Definition | Milestone |
|---|---|---|
| P0 — Critical | Core product functionality. Without this, product cannot function. | v1.0 Alpha |
| P1 — High | Significant user value. Required for production release. | v1.0 |
| P2 — Medium | Important but not blocking. | v1.1 |
| P3 — Low | Nice to have. Backlog. | v2.0+ |
| P4 — Research | Requires further research before scoping. | Future |

---

## Feature Matrix

### Core Vision Pipeline

| Feature | Priority | Status | Notes |
|---|---|---|---|
| Camera input (USB/built-in) | P0 | Planned | V4L2, DirectShow, AVFoundation |
| Face detection | P0 | Planned | MediaPipe BlazeFace + YOLOv8 fallback |
| Face tracking | P0 | Planned | Kalman filter-based temporal tracking |
| Facial landmark extraction (468 pts) | P0 | Planned | MediaPipe Face Mesh |
| Eye region extraction | P0 | Planned | Normalized 128×128 crops |
| Blink detection (EAR-based) | P0 | Planned | Eye Aspect Ratio + CNN validation |
| Gaze estimation (uncalibrated) | P0 | Planned | Appearance-based model |
| Head pose estimation | P1 | Planned | 6-DOF pose from landmarks |
| Pupil localization | P0 | Planned | EllSeg-style segmentation |
| Iris localization | P1 | Planned | Circle fit + segmentation |
| Eyebrow motion detection | P1 | Planned | Landmark-based ratio features |

### Intent Recognition

| Feature | Priority | Status | Notes |
|---|---|---|---|
| Temporal feature construction | P0 | Planned | Sliding window, 500ms–3s |
| Gesture classification | P0 | Planned | CNN + LSTM hybrid |
| Intent recognition engine | P0 | Planned | Transformer-based |
| Context memory | P1 | Planned | Short-term action history |
| Reading detection | P0 | Planned | Suppress commands during reading |
| Idle detection | P0 | Planned | No command when user isn't interacting |
| Confidence scoring | P0 | Planned | Per-prediction uncertainty |
| Uncertainty estimation | P1 | Planned | Monte Carlo Dropout |
| Intent conflict resolution | P1 | Planned | Priority queue + cooldown |

### Command Engine

| Feature | Priority | Status | Notes |
|---|---|---|---|
| Scroll Up / Down | P0 | Planned | Gaze-to-edge + blink |
| Back / Forward | P0 | Planned | Double blink + direction |
| Select / Click | P0 | Planned | Dwell + confirmation blink |
| Enter / Confirm | P0 | Planned | Deliberate long blink |
| Open Menu | P1 | Planned | Eyebrow raise + gaze |
| Switch Tab | P1 | Planned | Multi-gesture |
| Volume Up/Down | P2 | Planned | — |
| Brightness Up/Down | P2 | Planned | — |
| Home | P1 | Planned | — |
| App Switch | P1 | Planned | — |
| Notifications | P2 | Planned | — |
| Clipboard | P2 | Planned | — |
| Keyboard Navigation | P1 | Planned | Gaze keyboard |
| Cursor Mode | P1 | Planned | Continuous gaze cursor |
| Custom commands | P2 | Planned | Plugin API |

### Safety System

| Feature | Priority | Status | Notes |
|---|---|---|---|
| Confidence threshold gate | P0 | Planned | Default: 0.92 |
| Cooldown period | P0 | Planned | Default: 800ms |
| Dwell confirmation | P1 | Planned | For high-risk commands |
| Multi-gesture confirmation | P1 | Planned | For destructive actions |
| Emergency stop (3s eye closure) | P0 | Planned | Safety-critical |
| Anti-fatigue sensitivity reduction | P1 | Planned | After 2h use |
| False activation detection | P1 | Planned | Pattern analysis |

### Calibration

| Feature | Priority | Status | Notes |
|---|---|---|---|
| Uncalibrated mode | P0 | Planned | Immediate use |
| 5-point rapid calibration | P0 | Planned | < 30 seconds |
| 13-point full calibration | P1 | Planned | < 90 seconds |
| Calibration profile storage | P0 | Planned | Named profiles |
| Continuous passive calibration | P1 | Planned | Background refinement |
| Cross-device profile sync | P2 | Planned | Encrypted cloud |

### Personalization

| Feature | Priority | Status | Notes |
|---|---|---|---|
| User profiles | P0 | Planned | Local storage |
| Threshold personalization | P1 | Planned | Per-user tuning |
| Gesture vocabulary customization | P2 | Planned | User-defined gestures |
| Fatigue adaptation | P1 | Planned | Dynamic threshold adjustment |
| Application context profiles | P2 | Planned | Different settings per app |
| Preference learning | P3 | Planned | Reinforcement learning |

### OS Integration

| Feature | Priority | Status | Notes |
|---|---|---|---|
| Windows 10/11 | P0 | Planned | SendInput + UIAutomation |
| macOS 12+ | P0 | Planned | CGEvent + Accessibility API |
| Ubuntu 20.04+ | P1 | Planned | AT-SPI2 + X11 |
| Android | P2 | Planned | AccessibilityService |
| iOS | P3 | Planned | Switch Control |

### Infrastructure

| Feature | Priority | Status | Notes |
|---|---|---|---|
| FastAPI inference server | P0 | Planned | Local REST/WebSocket |
| ONNX model export | P0 | Planned | Runtime independence |
| Docker deployment | P1 | Planned | Server mode |
| Python SDK | P1 | Planned | Developer integration |
| JavaScript SDK | P2 | Planned | Web integration |
| MLFlow experiment tracking | P1 | Planned | Training pipeline |
| Weights & Biases integration | P1 | Planned | Model monitoring |
| Kubernetes scaling | P2 | Planned | Multi-user server |

### Dashboard & Configuration UI

| Feature | Priority | Status | Notes |
|---|---|---|---|
| Calibration wizard | P0 | Planned | Next.js UI |
| Status visualization | P1 | Planned | Live camera + gaze overlay |
| Settings panel | P1 | Planned | All parameters exposed |
| Profile manager | P1 | Planned | CRUD profiles |
| Benchmark runner | P2 | Planned | Self-test UI |
| Accessibility audit | P2 | Planned | Self-assessment |

### Research & Dataset

| Feature | Priority | Status | Notes |
|---|---|---|---|
| Dataset recording application | P1 | Planned | Desktop app |
| Annotation tool | P1 | Planned | Frame-level labeling |
| Dataset versioning | P1 | Planned | DVC integration |
| Quality assurance pipeline | P1 | Planned | Automated checks |
| Bias assessment tools | P1 | Planned | Distribution analysis |

---

## Release Planning

### v1.0 Alpha — Core Functionality
- All P0 features
- Windows + macOS only
- Not recommended for production accessibility use yet
- Developer preview

### v1.0 — Production Release
- All P0 + P1 features
- Windows, macOS, Linux
- Accessibility-validated (disability org pilot)
- Full documentation

### v1.1 — Expanded Platform
- P2 features
- Android beta
- REST API server stable
- SDK v1.0

### v2.0 — Enterprise + AR/VR
- P3 features
- AR/VR SDK
- Enterprise features
- Clinical validation study

---

## Dependency Graph

```
Camera Input
    └── Face Detection
            └── Landmark Extraction
                    ├── Eye Region Extraction
                    │       ├── Blink Detection
                    │       ├── Pupil Localization
                    │       └── Gaze Estimation
                    ├── Head Pose Estimation
                    └── Eyebrow Motion Detection
                            └── Temporal Feature Construction
                                    └── Intent Recognition
                                            └── Safety Filter
                                                    └── Command Engine
                                                            └── OS Integration
```
