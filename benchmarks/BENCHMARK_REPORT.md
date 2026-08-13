# EyeNav — Benchmark Report Template

**Version:** 1.0  
**Status:** Template (Results Pending Implementation)  
**Owner:** Engineering Team  
**Last Updated:** 2024-Q4  

---

## Executive Summary

This document records all performance benchmark results for EyeNav against the requirements specified in SRS and PRD.

---

## Test Environment

| Parameter | Value |
|---|---|
| CPU | Intel Core i5-8250U @ 1.6GHz (4 cores) |
| RAM | 8GB DDR4 |
| GPU | None (integrated graphics only) |
| OS | Ubuntu 22.04 LTS / Windows 11 22H2 |
| Camera | Logitech C920 (1080p @ 30fps) |
| Python | 3.11.x |
| ONNX Runtime | 1.17.x |
| Date | [To be filled on first run] |

---

## 1. Pipeline Frame Rate

**Requirement (SRS-PERF-001):** ≥ 30fps on i5-8250U, no GPU

| Platform | Resolution | FPS (mean) | FPS (min) | Passes? |
|---|---|---|---|---|
| Ubuntu 22.04 | 1280×720 | [TBD] | [TBD] | [TBD] |
| Windows 11 | 1280×720 | [TBD] | [TBD] | [TBD] |
| macOS 12 | 1280×720 | [TBD] | [TBD] | [TBD] |

---

## 2. End-to-End Latency

**Requirement (SRS-PERF-002):** ≤ 200ms (p95)

| Measurement | p50 | p95 | p99 | Passes? |
|---|---|---|---|---|
| Camera → Gaze estimate | [TBD] | [TBD] | [TBD] | [TBD] |
| Camera → Intent classification | [TBD] | [TBD] | [TBD] | [TBD] |
| Camera → Command execution | [TBD] | [TBD] | [TBD] | [TBD] |

---

## 3. Per-Module Latency

**Requirement (SRS-PERF-003):** Gaze estimate ≤ 33ms (one frame at 30fps)

| Module | Mean Latency | p95 Latency | Budget | Passes? |
|---|---|---|---|---|
| Face Detection (BlazeFace) | [TBD] | [TBD] | 5ms | [TBD] |
| Landmark Extraction (FaceMesh) | [TBD] | [TBD] | 8ms | [TBD] |
| Gaze Estimation (L2CS-MobileNetV3) | [TBD] | [TBD] | 6ms | [TBD] |
| Blink Detection (EAR + CNN) | [TBD] | [TBD] | 4ms | [TBD] |
| Head Pose (SolvePnP) | [TBD] | [TBD] | 2ms | [TBD] |
| Eyebrow Detection (MLP) | [TBD] | [TBD] | 2ms | [TBD] |
| Intent Recognition (Transformer) | [TBD] | [TBD] | 8ms | [TBD] |
| Safety Filter | [TBD] | [TBD] | 1ms | [TBD] |
| **Total Pipeline** | **[TBD]** | **[TBD]** | **30ms** | **[TBD]** |

---

## 4. Resource Usage

**Requirements:** CPU ≤ 30% (SRS-PERF-004), RAM ≤ 512MB (SRS-PERF-005)

| Resource | Idle | Active | Peak | Passes? |
|---|---|---|---|---|
| CPU (all cores) | [TBD] | [TBD] | [TBD] | [TBD] |
| RAM | [TBD] | [TBD] | [TBD] | [TBD] |
| GPU VRAM (if available) | N/A | N/A | N/A | N/A |

---

## 5. Gaze Accuracy

**Requirements:** ≤ 3° uncalibrated (FR-006), ≤ 1° calibrated

| Dataset | Mode | MAE (°) | Max Error (°) | Passes? |
|---|---|---|---|---|
| ETH-XGaze (test split) | Uncalibrated | [TBD] | [TBD] | [TBD] |
| ETH-XGaze (test split) | After 5-point calibration | [TBD] | [TBD] | [TBD] |
| MPIIGaze (test split) | Uncalibrated | [TBD] | [TBD] | [TBD] |
| EyeNav internal test | Uncalibrated | [TBD] | [TBD] | [TBD] |
| Glasses sub-group | Uncalibrated | [TBD] | [TBD] | [TBD] |

---

## 6. Blink Detection Accuracy

**Requirement:** ≥ 98% accuracy (FR-005)

| Dataset | Precision | Recall | F1 | False Positive Rate | Passes? |
|---|---|---|---|---|---|
| Eyeblink8 | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| EPID test set | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |

---

## 7. Intent Recognition Accuracy

**Requirement:** ≥ 95% accuracy (FR-009)

| Intent Class | Precision | Recall | F1 | Notes |
|---|---|---|---|---|
| Reading | [TBD] | [TBD] | [TBD] | Critical — false positives suppress commands |
| Selecting | [TBD] | [TBD] | [TBD] | Primary command intent |
| Scrolling Up | [TBD] | [TBD] | [TBD] | |
| Scrolling Down | [TBD] | [TBD] | [TBD] | |
| Idle | [TBD] | [TBD] | [TBD] | Must not trigger commands |
| Nav Back | [TBD] | [TBD] | [TBD] | |
| Confirmation | [TBD] | [TBD] | [TBD] | High risk |
| **Overall** | **[TBD]** | **[TBD]** | **[TBD]** | **Target ≥ 95%** |

---

## 8. Safety Metrics

**Requirement:** False positive rate ≤ 0.1% per session (FR-011)

| Session Type | Duration | Commands | False Positives | FPR | Passes? |
|---|---|---|---|---|---|
| Standard use (50 users) | 1 hour | [TBD] | [TBD] | [TBD] | [TBD] |
| Reading session (20 users) | 1 hour | 0 target | [TBD] | [TBD] | [TBD] |
| Fatigue state (20 users) | 2 hours | [TBD] | [TBD] | [TBD] | [TBD] |

---

## 9. Bias Evaluation

All metrics stratified by demographic group. Required: No group >5% below overall.

| Group | Gaze MAE (°) | Intent Accuracy | Within 5%? |
|---|---|---|---|
| Overall | [TBD] | [TBD] | N/A |
| Age < 18 | [TBD] | [TBD] | [TBD] |
| Age 18-35 | [TBD] | [TBD] | [TBD] |
| Age 36-55 | [TBD] | [TBD] | [TBD] |
| Age 55+ | [TBD] | [TBD] | [TBD] |
| Glasses wearers | [TBD] | [TBD] | [TBD] |
| Dark iris | [TBD] | [TBD] | [TBD] |
| Light iris | [TBD] | [TBD] | [TBD] |

---

## 10. Benchmark Execution

```bash
# Run complete benchmark suite
python benchmarks/run_benchmarks.py \
  --camera 0 \
  --duration 60 \
  --output-dir benchmarks/results/ \
  --platforms cpu \
  --report-format json html

# Run specific benchmark
pytest benchmarks/benchmark_pipeline.py --benchmark-only -v
```

---

## Benchmark History

| Date | Version | Overall Result | Notes |
|---|---|---|---|
| [TBD] | 0.1.0-alpha | [TBD] | First measurement |
