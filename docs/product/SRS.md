# EyeNav — System Requirements Specification (SRS)

**Document Version:** 1.0  
**Status:** Approved  
**Owner:** Engineering Team  
**Compliance:** IEEE 830 (adapted)  
**Last Updated:** 2024-Q4  

---

## 1. Introduction

### 1.1 Purpose

This System Requirements Specification defines the requirements for the EyeNav v1.0 software system. It is intended for system architects, software engineers, quality assurance engineers, and technical reviewers.

### 1.2 Document Scope

This SRS covers:
- The EyeNav core pipeline (vision + intent + safety + commands)
- The EyeNav configuration and calibration system
- The EyeNav REST/WebSocket API server
- OS integration layers (Windows, macOS, Linux)
- The EyeNav dashboard frontend (configuration UI)

Out of scope: Mobile apps, AR/VR SDK, cloud services (v2.0).

### 1.3 Definitions

| Term | Definition |
|---|---|
| EAR | Eye Aspect Ratio — geometric ratio of eye landmark distances used for blink detection |
| FPS | Frames Per Second — pipeline processing rate |
| MAE | Mean Angular Error — gaze estimation accuracy metric in degrees |
| ONNX | Open Neural Network Exchange — model format for hardware-agnostic inference |
| Intent | High-level classification of user navigation purpose |
| False Positive | Accidental command execution not intended by user |
| False Negative | Missed command detection (user intended action not executed) |
| Dwell | Sustained gaze at a location for a defined duration |
| Calibration | Per-user mapping from raw gaze estimates to screen coordinates |

---

## 2. Overall Description

### 2.1 Product Perspective

EyeNav is a standalone software system interfacing with:
- **Camera hardware**: via OS camera APIs (DirectShow/V4L2/AVFoundation)
- **Operating system**: via accessibility APIs (UIAutomation/AT-SPI2/CGEvent)
- **Display hardware**: via system screen coordinate APIs
- **User storage**: local filesystem (encrypted profiles)
- **Optional API clients**: external applications via REST/WebSocket

### 2.2 Operating Environment

| Platform | OS Version | Camera | Notes |
|---|---|---|---|
| Windows Desktop | Windows 10 v2004+ | USB/built-in | Primary target |
| Windows Laptop | Windows 10 v2004+ | Built-in 720p | Primary target |
| macOS Desktop | macOS 12 (Monterey)+ | USB/built-in | Primary target |
| macOS Laptop | macOS 12 (Monterey)+ | Built-in FaceTime | Primary target |
| Linux Desktop | Ubuntu 20.04+ | USB | Secondary target |
| Raspberry Pi 4 | Debian Bullseye | USB | Embedded/research |

---

## 3. Specific Requirements

### 3.1 External Interface Requirements

#### 3.1.1 Camera Interface

- **SRS-CAM-001**: System shall support any V4L2-compatible camera on Linux
- **SRS-CAM-002**: System shall support any DirectShow-compatible camera on Windows
- **SRS-CAM-003**: System shall support any AVFoundation-compatible camera on macOS
- **SRS-CAM-004**: System shall support minimum resolution 640×480 at 15fps
- **SRS-CAM-005**: System shall target 1280×720 at 30fps as standard operating mode
- **SRS-CAM-006**: System shall handle camera disconnection without crashing
- **SRS-CAM-007**: System shall recover automatically when camera reconnects
- **SRS-CAM-008**: System shall report camera capabilities on startup

#### 3.1.2 OS Integration Interface

- **SRS-OS-001**: On Windows: use SendInput API for cursor and keyboard events
- **SRS-OS-002**: On Windows: use UIAutomation for accessible focus detection
- **SRS-OS-003**: On macOS: use CGEvent for cursor and keyboard events
- **SRS-OS-004**: On macOS: use Accessibility API for focus detection
- **SRS-OS-005**: On Linux: use AT-SPI2 for accessible event dispatch
- **SRS-OS-006**: System shall not require administrator/root privileges for basic operation
- **SRS-OS-007**: System shall not interfere with other input methods

#### 3.1.3 REST API Interface

- **SRS-API-001**: System shall expose REST API on configurable localhost port
- **SRS-API-002**: All API responses shall be JSON formatted
- **SRS-API-003**: System shall expose WebSocket endpoint for real-time streaming
- **SRS-API-004**: System shall implement API versioning (/api/v1/)
- **SRS-API-005**: API shall be documented with OpenAPI 3.0 specification

### 3.2 Functional Requirements

#### 3.2.1 Vision Pipeline

| ID | Requirement | Priority | Verification |
|---|---|---|---|
| SRS-VP-001 | System shall detect faces in every frame where a face is present | P0 | Test |
| SRS-VP-002 | Face detection shall achieve ≥ 99% detection rate in standard conditions | P0 | Benchmark |
| SRS-VP-003 | System shall extract 468 facial landmarks from detected faces | P0 | Test |
| SRS-VP-004 | System shall estimate gaze direction with MAE ≤ 3° (uncalibrated) | P0 | Benchmark |
| SRS-VP-005 | System shall estimate gaze direction with MAE ≤ 1° (calibrated) | P0 | Benchmark |
| SRS-VP-006 | System shall detect blinks with ≥ 98% accuracy | P0 | Benchmark |
| SRS-VP-007 | System shall classify blink types: single, double, long, triple | P0 | Test |
| SRS-VP-008 | System shall detect eyebrow states: neutral, raised-L, raised-R, raised-both, lowered | P1 | Test |
| SRS-VP-009 | System shall estimate head pose (yaw, pitch, roll) with ≤ 5° MAE | P1 | Benchmark |
| SRS-VP-010 | System shall localize pupils in normalized eye image | P0 | Test |

#### 3.2.2 Intent Recognition

| ID | Requirement | Priority | Verification |
|---|---|---|---|
| SRS-IR-001 | System shall classify intents from 9 defined intent classes | P0 | Test |
| SRS-IR-002 | Intent classification accuracy shall be ≥ 95% on EPID test set | P0 | Benchmark |
| SRS-IR-003 | System shall provide confidence score per intent prediction | P0 | Test |
| SRS-IR-004 | System shall use 1.5-second temporal context window | P0 | Test |
| SRS-IR-005 | System shall suppress commands when reading intent detected | P0 | Test |
| SRS-IR-006 | Intent classification latency shall be ≤ 50ms from gesture completion | P0 | Benchmark |

#### 3.2.3 Safety System

| ID | Requirement | Priority | Verification |
|---|---|---|---|
| SRS-SS-001 | System shall implement 6-layer safety filter | P0 | Design review + test |
| SRS-SS-002 | False positive rate shall be ≤ 0.1% per session | P0 | User study |
| SRS-SS-003 | System shall trigger emergency stop on 3-second eye closure | P0 | Test |
| SRS-SS-004 | Emergency stop shall block ALL commands | P0 | Test |
| SRS-SS-005 | Safety filter failure (exception) shall result in command BLOCKED | P0 | Test |
| SRS-SS-006 | Each command shall have configurable confidence threshold | P0 | Test |
| SRS-SS-007 | Each command shall have configurable cooldown period | P0 | Test |
| SRS-SS-008 | High-risk commands shall require dwell confirmation | P1 | Test |

#### 3.2.4 Calibration

| ID | Requirement | Priority | Verification |
|---|---|---|---|
| SRS-CAL-001 | System shall function without calibration | P0 | Test |
| SRS-CAL-002 | 5-point calibration shall complete in ≤ 30 seconds | P0 | User test |
| SRS-CAL-003 | Calibration shall improve gaze accuracy to ≤ 1.5° | P0 | Benchmark |
| SRS-CAL-004 | Calibration profiles shall persist across sessions | P0 | Test |
| SRS-CAL-005 | Multiple named calibration profiles shall be supported | P1 | Test |

### 3.3 Performance Requirements

| ID | Requirement | Condition | Target |
|---|---|---|---|
| SRS-PERF-001 | Pipeline FPS | i5-8250U, no GPU | ≥ 30fps |
| SRS-PERF-002 | End-to-end command latency | p95 | ≤ 200ms |
| SRS-PERF-003 | Gaze estimate latency | per frame | ≤ 33ms |
| SRS-PERF-004 | CPU usage | sustained operation | ≤ 30% |
| SRS-PERF-005 | RAM usage | steady state | ≤ 512MB |
| SRS-PERF-006 | Startup time | cold start | ≤ 3 seconds |
| SRS-PERF-007 | MTBF | continuous operation | ≥ 8 hours |

### 3.4 Design Constraints

- **SRS-DC-001**: System shall not require GPU
- **SRS-DC-002**: System shall not require internet connectivity
- **SRS-DC-003**: System shall not collect or transmit raw gaze data
- **SRS-DC-004**: All ML inference shall use ONNX Runtime
- **SRS-DC-005**: Configuration shall be YAML-based with schema validation
- **SRS-DC-006**: System shall be Python 3.11+ compatible

### 3.5 Regulatory Requirements

- **SRS-REG-001**: Privacy: GDPR compliant — no biometric data processing without consent
- **SRS-REG-002**: Accessibility: WCAG 2.2 AA for dashboard UI
- **SRS-REG-003**: Security: No arbitrary code execution through user input
- **SRS-REG-004**: Logging: All command executions logged with audit trail
- **SRS-REG-005**: Data retention: User data deletable on request within 72 hours

---

## 4. Verification and Validation

### 4.1 Test Methods

| Method | Used For |
|---|---|
| Unit Test (pytest) | Individual function correctness |
| Integration Test | Pipeline stage interactions |
| System Test | End-to-end pipeline behavior |
| Performance Benchmark | Latency, FPS, resource usage |
| Accessibility Audit | WCAG compliance |
| User Study | Real-user accuracy, satisfaction |

### 4.2 Acceptance Tests

System is accepted when:
- All P0 requirements verified by automated tests
- All P0 performance requirements met on standard benchmark hardware
- Safety requirements pass 100% (zero failures acceptable)
- Accessibility audit: WCAG 2.2 AA passed
- User study: ≥ 80% task completion, ≥ 80% satisfaction (N≥50 users)
