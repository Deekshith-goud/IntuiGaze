# EyeNav — Intent-First Eye Navigation Platform

<div align="center">

![EyeNav Logo](assets/branding/eyenav-logo-placeholder.svg)

**A production-grade AI-driven Human Computer Interaction system that understands eye-based intent — not just gaze coordinates.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.2+-orange.svg)](https://pytorch.org)
[![Research Status](https://img.shields.io/badge/Status-Active%20Research-red.svg)]()
[![Docs](https://img.shields.io/badge/Docs-Comprehensive-brightgreen.svg)](docs/)

</div>

---

## What is EyeNav?

EyeNav is not an eye tracker.

EyeNav is an **Intent Recognition Platform** built on top of vision-first Human Computer Interaction research.

It answers the question:
> **"What does the user** ***want*** **to do?"** — not just "where are they looking?"

Traditional eye tracking systems output `(x, y)` gaze coordinates.

EyeNav outputs:
- `"User is reading"` → suppress navigation triggers
- `"User intentionally blinked twice"` → go back
- `"User raised left eyebrow and looked right"` → open menu
- `"User is fatigued"` → reduce sensitivity

This distinction makes EyeNav suitable for:
- **Accessibility users** who cannot use hands
- **AR/VR environments** where hands are busy
- **Automotive HUD navigation**
- **Surgical suites** requiring sterile interaction
- **Space and defense** environments
- **Smart glasses** interaction

---

## Architecture Summary

```
Camera Input
    ↓
Face Detection & Tracking
    ↓
Landmark Extraction (468 points)
    ↓
Eye Region Analysis
    │
    ├── Pupil Localization
    ├── Iris Tracking
    ├── Blink Detection
    ├── Gaze Estimation
    └── Eyebrow Motion
    ↓
Temporal Context Engine
    ↓
Intent Recognition Engine
    ↓
Confidence & Safety Filter
    ↓
Command Execution Layer
    ↓
OS Integration / API Response
```

---

## Repository Structure

```
eyenav/
├── research/           # Literature reviews, paper summaries, findings
├── docs/               # All product, system, architecture documentation
│   ├── product/        # PRD, DRD, Vision, Mission, Market Research
│   ├── architecture/   # ADRs, System Architecture, Diagrams
│   ├── research/       # Dataset docs, ML analysis, research papers
│   ├── business/       # Business model, investor pitch, IP
│   ├── api/            # API reference documentation
│   ├── sdk/            # SDK documentation
│   └── guides/         # Developer, deployment, user guides
├── datasets/           # Dataset registry, preprocessing, versioning
│   ├── registry/       # Metadata for all public datasets
│   ├── custom/         # EyeNav proprietary dataset specification
│   └── preprocessing/  # Normalization, augmentation pipelines
├── annotation/         # Annotation tooling and protocol
├── models/             # Model implementations, weights, exports
│   ├── face_detection/
│   ├── landmarks/
│   ├── eye_segmentation/
│   ├── pupil_localization/
│   ├── blink_detection/
│   ├── gaze_estimation/
│   ├── intent_recognition/
│   └── personalization/
├── training/           # Training scripts, configs, experiments
├── evaluation/         # Evaluation harness, metrics, reports
├── deployment/         # Deployment configs, Docker, Kubernetes
├── frontend/           # Dashboard, calibration UI, demo app
├── backend/            # FastAPI server, inference server
├── sdk/                # Python SDK, JavaScript SDK
├── cli/                # Command-line tools
├── desktop/            # Native desktop app (Electron)
├── mobile/             # Mobile app scaffolding
├── api/                # REST and WebSocket API layer
├── tests/              # All test suites
├── benchmarks/         # Performance benchmarks
├── configs/            # Global configuration files
├── scripts/            # Utility and automation scripts
├── experiments/        # Experiment tracking and results
├── assets/             # Branding, icons, media
├── papers/             # Research paper drafts and summaries
└── .github/            # CI/CD workflows, templates
```

---

## Quick Start

```bash
# Clone repository
git clone https://github.com/eyenav/eyenav.git
cd eyenav

# Set up Python environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run calibration
python cli/eyenav.py calibrate

# Start inference server
python backend/server.py

# Launch dashboard
cd frontend && npm install && npm run dev
```

---

## Key Documents

| Document | Path | Purpose |
|---|---|---|
| Product Vision | [docs/product/VISION.md](docs/product/VISION.md) | Why EyeNav exists |
| PRD | [docs/product/PRD.md](docs/product/PRD.md) | Full product requirements |
| System Architecture | [docs/architecture/SYSTEM_ARCHITECTURE.md](docs/architecture/SYSTEM_ARCHITECTURE.md) | Technical design |
| ML Architecture | [docs/architecture/ML_ARCHITECTURE.md](docs/architecture/ML_ARCHITECTURE.md) | Model selection & design |
| Dataset Registry | [datasets/registry/DATASET_REGISTRY.md](datasets/registry/DATASET_REGISTRY.md) | All public datasets |
| Custom Dataset | [datasets/custom/DATASET_SPEC.md](datasets/custom/DATASET_SPEC.md) | Proprietary dataset |
| API Reference | [docs/api/API_REFERENCE.md](docs/api/API_REFERENCE.md) | API documentation |
| Ethics Assessment | [docs/business/ETHICS.md](docs/business/ETHICS.md) | Ethical review |
| Roadmap | [docs/product/ROADMAP.md](docs/product/ROADMAP.md) | Implementation timeline |

---

## Research Status

| Module | Status | Notes |
|---|---|---|
| Face Detection | ✅ Design Complete | Using MediaPipe + YOLOv8 |
| Landmark Extraction | ✅ Design Complete | 468-point mesh |
| Pupil Localization | 🔬 In Research | EllSeg vs custom CNN |
| Gaze Estimation | 🔬 In Research | ETH-XGaze baseline |
| Blink Detection | ✅ Design Complete | EAR + temporal CNN |
| Intent Recognition | 🔬 In Research | Transformer-based |
| Safety System | ✅ Design Complete | Multi-layer filtering |
| Personalization | 📋 Planned | Continual learning |

---

## License

MIT License — see [LICENSE](LICENSE)

---

## Citation

If you use EyeNav in research, please cite:

```bibtex
@misc{eyenav2024,
  title={EyeNav: Intent-First Eye Navigation Platform},
  author={EyeNav Research Team},
  year={2024},
  url={https://github.com/eyenav/eyenav}
}
```

---

## Contact

- Research inquiries: research@eyenav.ai
- Business inquiries: business@eyenav.ai
- Accessibility partnerships: accessibility@eyenav.ai
