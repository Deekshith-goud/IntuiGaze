# EyeNav — Release Notes

---

## v1.0.0-alpha (2024-Q4) — Initial Research Preview

**Status:** Internal / Research Preview  
**Intended Audience:** Research partners, accessibility pilot users, early adopters  
**Not for:** General public distribution  

---

### What's New

This is the first documented release of EyeNav. It establishes the complete foundational architecture for intent-driven eye navigation.

#### Core Pipeline

- **Face Detection** — BlazeFace with MobileNetV3 backbone. Detects faces in < 3ms on CPU.
- **Landmark Extraction** — MediaPipe FaceMesh, 468-point landmarks at 30fps.
- **Gaze Estimation** — L2CS-Net with MobileNetV3. Achieves < 3° MAE uncalibrated on ETH-XGaze.
- **Blink Detection** — EAR-based geometric + CNN classifier. 9 blink types supported.
- **Eyebrow Detection** — Landmark-based MLP. 5 eyebrow states.
- **Intent Recognition** — Tiny Temporal Transformer (320k parameters). 1.5-second window. 13 intent classes.

#### Safety System

- 6-layer safety filter: Confidence → Cooldown → Context → Dwell → Anti-Pattern → Emergency Stop
- Fail-safe: all exceptions result in command BLOCKED
- Emergency stop on 3-second eye closure
- All safety parameters configurable

#### Configuration

- YAML-based configuration with Pydantic validation
- Per-user calibration profiles
- Full config documentation in `configs/defaults.yaml`

#### API (Server Mode)

- FastAPI REST + WebSocket server
- Python SDK (alpha)
- OpenAPI documentation at `/docs`

---

### Known Limitations (Alpha)

1. **No OS integration yet** — Commands are classified but not executed. OS integration (SendInput, CGEvent) is v1.0 GA scope.
2. **No UI** — Configuration via YAML only. Dashboard UI is v1.0 GA scope.
3. **Models not trained** — Model files must be sourced separately (see `models/README.md`). Training pipeline is documented but models need training on full EPID dataset.
4. **Calibration not polished** — Calibration works programmatically but no GUI wizard yet.
5. **Linux only tested** — Windows and macOS CI is set up but platform-specific edge cases not yet resolved.

---

### Installation (Alpha)

```bash
git clone https://github.com/eyenav/eyenav.git
cd eyenav
pip install -r requirements-dev.txt
dvc pull  # Download model files (requires DVC + access)
pytest tests/ -v  # Run test suite
```

---

### What's Coming in v1.0.0 GA

- OS integration (Windows + macOS + Linux)
- Calibration wizard UI
- Dashboard UI (settings, profiles, status)
- Full EPID dataset training
- Desktop installer packages

---

## v0.9.0-alpha (Internal Only)

Initial documentation and architecture. Not distributed.

---

## Planned Releases

| Version | Target Date | Key Features |
|---|---|---|
| v1.0.0 GA | Q2 2025 | OS integration, installer, full models, dashboard UI |
| v1.1.0 | Q3 2025 | Zero-shot calibration improvements, more intent classes |
| v1.2.0 | Q4 2025 | JavaScript SDK, Electron integration |
| v1.5.0 | Q1 2026 | Android SDK, iOS SDK, mobile deployment |
| v2.0.0 | Q4 2026 | AR/VR support, multimodal fusion, hierarchical intent model |

---

## Reporting Issues

- GitHub Issues: https://github.com/eyenav/eyenav/issues
- Security vulnerabilities: security@eyenav.ai (do NOT use GitHub Issues for security)
- Accessibility feedback: accessibility@eyenav.ai

## Upgrading

No upgrade path from alpha to GA (breaking changes expected). Fresh installation required for v1.0.0 GA.
