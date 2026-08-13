# ADR-001 — Primary Deployment Architecture: Edge AI

**Status:** Accepted  
**Date:** 2024-Q4  
**Deciders:** Architecture Team  
**Tags:** infrastructure, deployment, privacy  

---

## Context

EyeNav requires a real-time vision pipeline capable of processing 30fps video, performing ML inference across 7 models, and dispatching OS commands — all within 200ms.

Four architectural candidates were evaluated (see [SYSTEM_ARCHITECTURE.md](../SYSTEM_ARCHITECTURE.md)):
- Monolithic single-process
- Microservices (HTTP/gRPC)
- Edge AI (ONNX Runtime, single process)
- Hybrid Edge + Cloud

The choice determines: latency profile, privacy guarantees, resource usage, and offline capability.

## Decision Drivers

- **Latency**: ≤ 200ms end-to-end is non-negotiable for usable eye navigation
- **Privacy**: GDPR compliance + user trust requires no gaze data leaving device
- **Offline**: System must work without internet in all accessibility contexts
- **Resource**: ≤ 30% CPU without GPU

## Considered Options

| Option | Latency | Privacy | Offline | Resources |
|---|---|---|---|---|
| Monolithic | ~130ms ✅ | Full ✅ | Full ✅ | Low ✅ |
| Microservices | ~200ms+ ⚠️ | Full ✅ | Full ✅ | High ❌ |
| Edge AI (ONNX) | ~120ms ✅ | Full ✅ | Full ✅ | Medium ✅ |
| Hybrid (Edge+Cloud) | 120ms edge / 400ms cloud | Partial ⚠️ | Partial ⚠️ | Low ✅ |

## Decision Outcome

**Chosen Option: Edge AI (ONNX Runtime) as Primary**

Edge AI provides:
1. Lowest achievable latency (~120ms) via ONNX Runtime hardware optimization
2. Complete privacy (all processing local)
3. Full offline operation
4. Hardware-agnostic (ONNX runs on CPU, GPU, NPU identically)
5. Same model binary works on Windows, macOS, Linux, mobile

Hybrid Cloud is adopted as **optional secondary mode** for users who explicitly consent to cloud enhancement (personalization sync, model updates).

## Consequences

### Positive
- Users can trust that no gaze data is transmitted
- Works in hospitals, offline environments, restricted networks
- Model binary is portable across all hardware
- ONNX Runtime provides automatic hardware acceleration

### Negative
- Cannot run very large models (>100M params) on CPU
- Model updates require local download rather than server-side

### Risks
- ONNX operator support gaps for novel architectures → Mitigation: validate ONNX export early in model development
- ONNX Runtime version fragmentation → Mitigation: pin version, bundle with application

## Validation

- [ ] Pipeline benchmark: ≥ 30fps on i5-8250U without GPU
- [ ] Pipeline latency: ≤ 200ms p95
- [ ] Zero network calls during standard operation (verified by network monitoring)

## References

- ONNX Runtime Documentation: https://onnxruntime.ai/
- System Architecture Document: ../SYSTEM_ARCHITECTURE.md
