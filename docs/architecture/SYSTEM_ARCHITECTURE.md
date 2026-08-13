# EyeNav — System Architecture

**Document Version:** 1.0  
**Status:** Approved  
**Owner:** Architecture Team  
**Last Updated:** 2024-Q4  
**ADR Reference:** ADR-001, ADR-002, ADR-003  

---

## 1. Architecture Requirements

Before evaluating architectures, the requirements that drive the architecture decision:

| Requirement | Constraint |
|---|---|
| Latency | ≤ 200ms end-to-end |
| Privacy | No data leaves device by default |
| Offline operation | Must work without internet |
| Resource usage | ≤ 30% CPU, ≤ 512MB RAM |
| Platform support | Windows, macOS, Linux, Android, iOS |
| Scalability (server mode) | 1,000 concurrent users |
| Maintainability | Independently upgradeable modules |
| Reliability | MTBF ≥ 8 hours |

---

## 2. Architecture Candidates

### Candidate A — Pure Monolithic (Single Process)

**Description:**  
All pipeline stages run in a single Python process with shared memory.

```
Single Process
├── Camera Acquisition Thread
├── Face Detection
├── Landmark Extraction
├── Eye Analysis
├── Intent Engine
├── Safety Filter
└── Command Executor
```

**Advantages:**
- Lowest IPC overhead
- Simplest deployment (single binary)
- Lowest memory footprint
- Easiest to debug

**Disadvantages:**
- One crash kills entire pipeline
- Cannot independently scale components
- GIL (Global Interpreter Lock) limits parallelism
- Cannot mix languages per component
- Difficult to upgrade individual models in production

**Latency Profile:**
- No serialization overhead
- Shared memory buffers
- Estimated total: ~130ms

**Verdict:** Suitable for embedded/mobile deployment, not for server mode.

---

### Candidate B — Microservices (HTTP/gRPC)

**Description:**  
Each pipeline stage runs as an independent service communicating over HTTP or gRPC.

```
Camera Service ──gRPC──► Face Service ──gRPC──► Landmark Service
                                                      │
                                              Eye Analysis Service
                                                      │
                                             Intent Engine Service
                                                      │
                                              Safety Filter Service
                                                      │
                                             Command Router Service
```

**Advantages:**
- Complete fault isolation
- Independent scaling per service
- Language agnostic (Python, C++, Rust per module)
- Independent deployment and rollback
- Horizontal scalability

**Disadvantages:**
- High serialization overhead (gRPC adds ~5-15ms per hop)
- 6+ hops in pipeline = 30-90ms network overhead alone
- Complex debugging across services
- Resource heavy (each service = independent process + memory)
- Overkill for single-user on-device case

**Latency Profile:**
- Serialization per hop: ~5ms
- 6 hops: ~30ms overhead
- Estimated total: ~200ms (at the limit)

**Verdict:** Too much latency overhead for real-time 30fps pipeline. Better for batch processing.

---

### Candidate C — Edge AI (Single Process, ONNX Runtime)

**Description:**  
All models exported to ONNX and run via a single optimized runtime process. No inter-process communication.

```
ONNX Runtime Process
├── Camera Thread (DirectShow/V4L2)
├── Model Graph:
│   ├── BlazeFace (ONNX)
│   ├── FaceMesh (ONNX)
│   ├── GazeNet (ONNX)
│   ├── BlinkNet (ONNX)
│   └── IntentTransformer (ONNX)
├── Post-Processing
├── Safety Filter (Rule Engine)
└── Command Bus
```

**Advantages:**
- ONNX Runtime is highly optimized (DirectML, CoreML, CUDA)
- Hardware-agnostic (same model file on CPU, GPU, NPU)
- Low latency — all in-process
- TensorRT/CoreML acceleration when available
- WASM deployment possible for browser

**Disadvantages:**
- All models must be ONNX-compatible
- Less flexibility for PyTorch-native research
- Debugging is harder (no Python debugger on ONNX graph)
- ONNX operator support varies by runtime version

**Latency Profile:**
- ONNX Runtime overhead: ~2ms vs PyTorch
- All in-process: no IPC
- Estimated total: ~120ms

**Verdict:** ✅ Best for production edge deployment. Used for primary deployment.

---

### Candidate D — Hybrid Edge + Cloud

**Description:**  
Lightweight models run on-device for real-time operation. Heavy models (personalization, intent reasoning) run on cloud when connected.

```
Edge Device                    Cloud (Optional)
┌─────────────────────┐       ┌─────────────────────┐
│ Camera              │       │ Intent Reasoning     │
│ Face Detection      │       │ Model (Large)        │
│ Lightweight Gaze    │──────►│ Personalization      │
│ Blink Detection     │◄──────│ Profile Sync         │
│ Local Intent        │       │ Model Updates        │
│ (fast, less acc)    │       │ Analytics            │
└─────────────────────┘       └─────────────────────┘
```

**Advantages:**
- Best accuracy (large cloud models)
- Offline fallback (local lightweight models)
- Personalization across devices
- Centralized model updates

**Disadvantages:**
- Network dependency for best performance
- Privacy concern — gaze data to cloud (even encrypted)
- Latency spike when cloud path used (+50-200ms)
- Cost of cloud inference infrastructure
- Compliance complexity (GDPR biometric data)

**Latency Profile:**
- Edge path: ~120ms (same as Candidate C)
- Cloud path: ~300-500ms (unacceptable for real-time)

**Verdict:** ⚠️ Viable for offline/online hybrid with explicit user consent. Secondary deployment mode only.

---

## 3. Architecture Decision

### Selected: Candidate C (Edge AI) as Primary + Candidate D (Hybrid) as Optional Server Mode

**Rationale:**
1. Latency: Only edge AI meets the 200ms requirement consistently
2. Privacy: No data leaves device in primary mode
3. Offline: Always works without network
4. Optimization: ONNX Runtime provides hardware acceleration transparently
5. Flexibility: Server mode (Candidate D) is additive, not a replacement

**How They Coexist:**
```
┌─────────────────────────────────────────────────────────┐
│                    EyeNav Runtime                        │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │             EDGE MODE (Default)                  │    │
│  │  Camera → ONNX Pipeline → Safety → Command       │    │
│  └─────────────────────────────────────────────────┘    │
│                         ↕ (opt-in)                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │           CLOUD ENHANCEMENT (Optional)            │    │
│  │  Profile Sync + Model Updates + Large Intent      │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## 4. Component Architecture (Selected Design)

```
┌────────────────────────────────────────────────────────────────────┐
│                         EyeNav Process                              │
│                                                                      │
│  ┌──────────────┐   ┌──────────────────────────────────────────┐   │
│  │ Camera       │   │              Vision Pipeline              │   │
│  │ Acquisition  │──►│  BlazeFace → FaceMesh → EyeExtract       │   │
│  │ Thread       │   │  ↓           ↓           ↓                │   │
│  │ (V4L2/DS/   │   │  HeadPose    GazeEst    Blink/Pupil/Brow  │   │
│  │  AVF)        │   └──────────────────────────────────────────┘   │
│  └──────────────┘                     │                             │
│                                       ▼                             │
│                          ┌─────────────────────┐                   │
│                          │   Temporal Engine    │                   │
│                          │   (500ms window)     │                   │
│                          │   Feature Buffer     │                   │
│                          └─────────────────────┘                   │
│                                       │                             │
│                                       ▼                             │
│                          ┌─────────────────────┐                   │
│                          │   Intent Recognizer  │                   │
│                          │   (Transformer)      │                   │
│                          │   + Context Memory   │                   │
│                          └─────────────────────┘                   │
│                                       │                             │
│                                       ▼                             │
│                          ┌─────────────────────┐                   │
│                          │   Safety Filter      │                   │
│                          │   Multi-Layer Gate   │                   │
│                          └─────────────────────┘                   │
│                                       │                             │
│                                       ▼                             │
│  ┌──────────────┐   ┌─────────────────────┐   ┌───────────────┐   │
│  │  Config Mgr  │   │   Command Router    │   │  API Server   │   │
│  │  (YAML)      │   │   (Plugin System)   │   │  (FastAPI)    │   │
│  └──────────────┘   └─────────────────────┘   └───────────────┘   │
│                               │                                      │
│  ┌──────────────┐            ▼                                      │
│  │  Profile Mgr │   ┌─────────────────────┐                        │
│  │  (AES-256)   │   │    OS Integration   │                        │
│  └──────────────┘   │  Win/Mac/Linux/And  │                        │
│                      └─────────────────────┘                        │
└────────────────────────────────────────────────────────────────────┘
```

---

## 5. Data Flow

### Frame Processing Flow (per frame, 33ms budget)

```
t=0ms   Camera frame captured (1280×720 @ 30fps)
t=2ms   Frame decoded, RGBA→BGR, resize to 640×480
t=5ms   Face detection inference (BlazeFace, ~3ms)
t=8ms   Face bounding box → landmark extraction (FaceMesh, ~8ms)
t=12ms  Eye region crops extracted (2 patches, ~2ms)
t=18ms  Parallel:
         - Gaze estimation (~6ms)
         - Blink detection (~4ms)
         - Pupil localization (~3ms)
         - Eyebrow detection (~3ms)
         - Head pose estimation (~2ms)
t=20ms  All features assembled into feature vector
t=21ms  Feature vector added to 500ms temporal buffer
t=23ms  Intent recognition inference (~2ms, Transformer)
t=25ms  Safety filter evaluation (~1ms, rule engine)
t=26ms  Command routing (~1ms)
t=27ms  OS event dispatch (~3ms)
t=30ms  Frame complete — next frame begins
```

---

## 6. Module Interfaces

### Camera Module → Vision Pipeline
```python
Frame = {
    "timestamp": float,           # Unix timestamp, microsecond precision
    "frame_id": int,              # Monotonic frame counter
    "data": np.ndarray,           # HxWxC, uint8, BGR
    "resolution": Tuple[int,int], # (width, height)
    "fps": float,                 # Actual captured FPS
    "camera_id": str              # Device identifier
}
```

### Vision Pipeline → Temporal Engine
```python
FrameFeatures = {
    "timestamp": float,
    "frame_id": int,
    "face_detected": bool,
    "face_confidence": float,
    "landmarks": np.ndarray,          # (468, 3) float32
    "gaze_vector": np.ndarray,        # (3,) unit vector
    "gaze_screen": np.ndarray,        # (2,) screen-normalized [0,1]
    "gaze_confidence": float,
    "blink_state": str,               # "open|closed|half"
    "blink_type": Optional[str],      # "single|double|long|none"
    "ear_left": float,                # Eye Aspect Ratio
    "ear_right": float,
    "pupil_left": np.ndarray,         # (2,) normalized
    "pupil_right": np.ndarray,
    "head_pose": np.ndarray,          # (3,) yaw,pitch,roll degrees
    "eyebrow_state": str,             # "neutral|raised_l|raised_r|raised_both|..."
    "eyebrow_confidence": float
}
```

### Intent Engine → Safety Filter
```python
IntentPrediction = {
    "intent": str,                    # "reading|selecting|scrolling|..."
    "intent_confidence": float,       # [0, 1]
    "suggested_command": Optional[str],
    "command_confidence": float,
    "context_window_ms": int,
    "temporal_features": np.ndarray   # For explainability
}
```

### Safety Filter → Command Router
```python
VerifiedCommand = {
    "command": str,
    "confidence": float,
    "blocked": bool,
    "block_reason": Optional[str],    # "cooldown|threshold|emergency_stop|..."
    "timestamp": float,
    "execution_id": str               # UUID for audit trail
}
```

---

## 7. Deployment Topology

### Single User (Desktop)
```
Local Machine
├── EyeNav Process (Python + ONNX)
├── Config Files (YAML, encrypted profiles)
└── OS Integration (SendInput/CGEvent/AT-SPI)
```

### Research / Multi-User Server
```
Server
├── EyeNav Inference Service (FastAPI + ONNX)
│   ├── Worker 1 (ONNX Runtime)
│   ├── Worker 2 (ONNX Runtime)
│   └── Worker N
├── Redis (session state, feature cache)
├── PostgreSQL (user profiles, telemetry)
└── MinIO (model storage, dataset storage)

Client
├── EyeNav Thin Client
│   ├── Camera capture
│   ├── Frame streaming (WebRTC/WebSocket)
│   └── Command receiver
```

### Docker Compose (Development)
```yaml
# See deployment/docker-compose.yml
services:
  eyenav-inference:   # Main inference service
  redis:              # Feature cache
  postgres:           # Profiles and telemetry
  minio:              # Object storage
  mlflow:             # Experiment tracking
  prometheus:         # Metrics
  grafana:            # Dashboards
```

---

## 8. Scalability Design

### Vertical Scaling
- ONNX Runtime uses all available CPU cores automatically
- GPU acceleration activated when available (CUDA, DirectML, CoreML)
- NPU support via ONNX Runtime NPU execution provider (future)

### Horizontal Scaling (Server Mode)
- Stateless inference workers (all state in Redis)
- Kubernetes HPA based on queue depth
- Model files served from MinIO (shared across workers)

### Multi-Tenant Isolation
- Per-session context isolation
- No cross-user data leakage possible (verified by design)
- User profiles encrypted with per-user keys

---

## 9. Observability

### Metrics (Prometheus)
- `eyenav_fps` — frames processed per second
- `eyenav_pipeline_latency_ms` — end-to-end pipeline latency
- `eyenav_model_inference_ms{model}` — per-model inference time
- `eyenav_face_detection_rate` — frames with detected face
- `eyenav_intent_confidence` — distribution of confidence scores
- `eyenav_command_count{command}` — commands executed per type
- `eyenav_false_positive_events` — safety-blocked activations
- `eyenav_cpu_percent` — CPU usage
- `eyenav_ram_mb` — RAM usage

### Logging
- Structured JSON logs (loguru)
- No gaze data logged (privacy)
- Command log: command name, timestamp, confidence (anonymous)
- Error log: full exception context, stack trace

### Tracing
- OpenTelemetry integration for distributed tracing (server mode)
- Per-frame trace IDs for debugging pipeline issues

---

## 10. References

1. Howard, A., et al. (2019). Searching for MobileNetV3. *ICCV 2019*.
2. Lugaresi, C., et al. (2019). MediaPipe: A Framework for Perceiving and Processing Reality. *CVPR Workshop*.
3. ONNX Runtime Team. (2023). ONNX Runtime: Cross-platform, high performance ML inferencing and training accelerator.
4. Cheng, Y., et al. (2021). Appearance-Based Gaze Estimation With Deep Learning. *IEEE TPAMI*.
5. Tonsen, M., et al. (2020). InvisibleEye. *ACM IMWUT*.
