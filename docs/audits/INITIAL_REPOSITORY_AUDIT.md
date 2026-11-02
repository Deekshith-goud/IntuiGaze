# IntuiGaze — Initial Repository Audit

**Document Date:** October 29, 2026  
**Auditor:** Antigravity (AI Coding Assistant)  
**Status:** Baseline Established (Read-Only Audit Phase)  

---

## 1. Executive Summary

IntuiGaze is an experimental eye-tracking system designed to translate facial and iris landmarks into real-time OS-level mouse cursor control. The core Python implementation is located under `backend/eyenav/`, featuring MediaPipe landmark extraction, polynomial regression gaze mapping, saccade/fixation detection, One Euro filtering, blink/dwell intent detection, and a multi-layer safety filter.

The repository also contains a Next.js frontend in `frontend/`, extensive architecture documentation in `docs/`, 11 stub directories containing only placeholder `README.md` files, ad-hoc loose files in the root (including a 21.6 GB dataset archive `archive.zip` and a 3.76 MB MediaPipe binary `face_landmarker.task`), and local telemetry data in `data/`.

---

## 2. Git Status and Working Tree Baseline

- **Current Branch:** `main`
- **Tracking:** Ahead of `origin/main` by 1 commit (`68e48c6 docs: improve README structure and project documentation`).
- **Uncommitted User Modifications (MUST BE PRESERVED):**
  - `backend/eyenav/cursor/controller.py`: Implements a fixation gravity well / deadzone (`_FIXATION_DEADZONE_PX = 45.0`) anchoring the cursor during fixation and releasing during saccades.
  - `docs/business/ETHICS.md`: Updated header date to `2026-Q4`.
- **Nested Git Repositories:**
  - `frontend/.git`: Standalone Git repository initialized inside the `frontend/` directory (not tracked as a submodule in `.gitmodules`). Contains Next.js application, build artifacts (`.next/`), and dependencies (`node_modules/`).
- **Root Loose Untracked Files:**
  - `archive.zip` (21,616,790,160 bytes / 20.13 GB): Compressed MIT GazeCapture dataset.
  - `face_landmarker.task` (3,758,596 bytes): Binary MediaPipe Face Landmarker model asset (actively required by `backend/eyenav/vision/landmarks.py`).
  - `exp.py` (1,299 bytes): 33-line exploratory script using OpenCV and PyAutoGUI directly without safety filters.
  - `eyemovement.txt` (60,248 bytes): Raw console log from running `backend.eyenav.desktop` on 2026-07-29.
  - `20260801-0708-37.3171907.mp4` (4,854,051 bytes): Video recording of desktop/gaze tracking.
  - Governance and agent pack files: `AGENTS.md`, `APPLY_PACK_PROMPT.md`, `METRICS_POLICY.md`, `ML_AUDIT.md`, `README_AGENT_PACK.md`, `ROADMAP.md`, `SETUP_AND_ADOPTION.md`, `.gitignore.ml-recommendations`.

---

## 3. Directory Inventory and Categorization

| Directory | File Count | Purpose | Status / Recommendation |
|---|---|---|---|
| `backend/` | 46 | Core Python package `eyenav` | Active production code. Keep intact. |
| `tests/` | 15 | Pytest test suite (safety, config, camera, etc.) | Active test suite. Keep intact. |
| `scripts/` | 9 | CLI scripts (desktop runner, calibration, dataset audit) | Active operational scripts. Keep intact. |
| `docs/` | 39 | Comprehensive documentation (architecture, product, ADRs) | Active documentation. Add audit and ML folders. |
| `configs/` | 3 | Default YAML configuration and ML config examples | Active configuration. Keep intact. |
| `data/` | 53 | Runtime telemetry CSVs (42 files) and heatmap PNGs (11 files) | Local runtime telemetry. Exclude from Git; organize into `data/interim/`. |
| `frontend/` | 26,643 | Next.js dashboard app (includes `node_modules` and `.next`) | Separate web frontend with independent `.git`. Keep separated under `app/frontend/`. |
| `benchmarks/` | 3 | Pipeline benchmark scripts and report | Performance benchmarking. Keep in place or group under `tests/benchmarks/`. |
| `deployment/` | 2 | Dockerfile and docker-compose.yml | Container deployment config. Keep intact. |
| `papers/` | 1 | `TECHNICAL_WHITEPAPER.md` | Academic whitepaper documentation. Consolidate into `docs/research/`. |
| `optional/` | 1 | CI quality gate configuration | CI templates. Consolidate into `.github/`. |
| `datasets/` | 3 | Dataset registry, consent form, dataset spec | Reference documentation. Move to `docs/data/`. |
| `trash/` | 0 | Designated quarantine directory | Active quarantine target. |
| **Scaffolding / Stub Folders** | 1 each | `README.md` placeholder only: `annotation/`, `assets/`, `cli/`, `desktop/`, `evaluation/`, `experiments/`, `mobile/`, `models/`, `research/`, `sdk/`, `training/` | Historical scaffolding from early design. Propose consolidating into clean `app/`, `ml/`, `docs/`, `scripts/` architecture. |

---

## 4. Verification of Critical Assets

1. **`face_landmarker.task`**:
   - Location: Repository root.
   - Investigation: Checked references in `backend/eyenav/vision/landmarks.py` lines 73–81:
     ```python
     model_path = Path(__file__).resolve().parent.parent.parent.parent / "face_landmarker.task"
     if not model_path.exists():
         model_path = Path("face_landmarker.task")
     ```
   - Finding: **CRITICAL ACTIVE ASSET**. If deleted or moved without path adjustment, `FaceLandmarkExtractor` crashes on startup.
   - Action: Retain in place during baseline; plan orderly relocation to `assets/models/` or `models/` with updated fallback paths.

2. **Pre-trained Model Pickles**:
   - `backend/eyenav/models/spatial_mapper.pkl`: Trained Random Forest regressor for screen coordinate mapping.
   - `backend/eyenav/models/intent_classifier.pkl`: Model artifact for intent classification.
   - Finding: Active artifacts. Preserved.

---

## 5. Build and Test Health Baseline

- **Python Environment:** Python 3.14.3 virtual environment in `.venv/`.
- **Ruff Linter:** `ruff check backend/ tests/` → **PASSED** (0 errors).
- **MyPy Type Checker:** `mypy backend` → **PASSED** (0 issues in 20 source files).
- **Pytest Suite:** `pytest -v` → **68 PASSED, 8 SKIPPED** (WCAG tests skipped due to dashboard server offline). 0 failures.

