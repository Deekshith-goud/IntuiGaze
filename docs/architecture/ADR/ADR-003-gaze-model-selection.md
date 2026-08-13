# ADR-003 — Gaze Estimation: L2CS-Net (MobileNetV3) vs Alternatives

**Status:** Accepted  
**Date:** 2024-Q4  
**Deciders:** ML Team  
**Tags:** model, gaze, accuracy  

---

## Context

Gaze estimation is the core sensing capability of EyeNav. The model must balance accuracy (≤ 3° uncalibrated MAE on ETH-XGaze) with inference latency (≤ 6ms on CPU).

## Decision Drivers

- Accuracy: ≤ 3° uncalibrated, ≤ 1° calibrated
- Latency: ≤ 6ms on Intel Core i5 CPU (no GPU)
- Input: Eye region patches (128×128) + head pose
- ONNX exportable

## Considered Options

| Model | MAE (ETH-XGaze) | CPU Latency | ONNX | Notes |
|---|---|---|---|---|
| iTracker (GazeCapture) | 4.8° | ~5ms | ✅ | 2016, outdated |
| L2CS-Net (ResNet-50) | 2.1° | ~18ms | ✅ | Too slow |
| L2CS-Net (MobileNetV3) | 2.9° | ~6ms | ✅ | ✅ Best tradeoff |
| GazeTR (ViT) | 1.8° | ~25ms | ✅ | Too slow on CPU |
| ETH-XGaze ResNet-18 | 3.1° | ~8ms | ✅ | Slightly over budget |
| Custom EfficientNet-B0 | 2.7° | ~5ms | ✅ | Future candidate |

## Decision Outcome

**Chosen: L2CS-Net with MobileNetV3-Large backbone**

L2CS-Net (2023, Abdelrahman et al.) achieves state-of-the-art accuracy for appearance-based gaze estimation. Using MobileNetV3-Large backbone:
- Reduces latency from 18ms (ResNet-50) to 6ms
- Accuracy drops from 2.1° to 2.9° — still within 3° target
- MobileNetV3 is ONNX-stable and well-supported

Post-calibration improvement (historical data from ETH-XGaze paper): calibration reduces error by 65-75%, bringing 2.9° → ~1.0° — meeting the calibrated target.

## Consequences

### Positive
- Strong benchmark numbers support the accuracy claim
- MobileNetV3 is designed for edge deployment
- Pre-trained weights available from ETH-XGaze training

### Negative
- 2.9° uncalibrated is at the acceptable limit — any degradation (lighting, glasses) could exceed 3°
- MobileNetV3 accuracy is below ResNet-50 quality

### Risks
- Performance degrades with glasses or strong reflections → Mitigation: test camera with glasses, data augment with glasses
- Accuracy on non-Western eye shapes may differ → Mitigation: ensure dataset diversity, cross-ethnic evaluation

## Validation

- [ ] MAE ≤ 3° on ETH-XGaze test split
- [ ] MAE ≤ 1° after 5-point calibration
- [ ] Latency ≤ 6ms on i5-8250U
- [ ] Works with glasses (separate benchmark)

## References

- Abdelrahman et al. (2023). L2CS-Net: Fine-Grained Gaze Estimation in Unconstrained Environments.
- Zhang et al. (2020). ETH-XGaze: A Large Scale Dataset for Gaze Estimation Under Extreme Head Pose.
