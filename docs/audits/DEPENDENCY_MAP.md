# IntuiGaze — Dependency and Environment Map

**Document Date:** October 29, 2026  
**Auditor:** Antigravity (AI Coding Assistant)  
**Status:** Verified against Active Virtual Environment (`.venv`)  

---

## 1. Runtime Environment

- **Operating System:** Windows 11 (win32)
- **Active Python Executable:** `C:\Users\Voriganti\Downloads\INAV\.venv\Scripts\python.exe`
- **Active Python Version:** `Python 3.14.3`
- **Specification in `pyproject.toml`:** `requires-python = ">=3.11"`
- **MyPy Configuration:** Configured for Python 3.14 target in `pyproject.toml`.

---

## 2. Core Dependency Map

| Subsystem | Package | Installed Version | Role / Purpose |
|---|---|---|---|
| **Computer Vision** | `mediapipe` | `1.0.1` | Face and iris landmark detection (478 points, Tasks API) |
| | `opencv-python` | `5.0.0.93` | Video capture, frame preprocessing, color space conversion |
| | `pillow` | `12.3.0` | Image processing and format manipulation |
| **Machine Learning** | `scikit-learn` | `1.9.0` | Polynomial regression, Ridge mapper, Random Forest |
| | `torch` | `2.13.0` | Deep learning models (temporal transformers, gaze CNNs) |
| | `torchvision` | `0.28.0` | Image transforms and backbone models |
| | `onnxruntime` | `1.29.0` | Optimized model inference runtime |
| | `numpy` | `2.5.2` | Numerical computing and array representations |
| | `scipy` | `1.18.0` | Signal processing and scientific computing |
| **Desktop Automation** | `pyautogui` | `0.9.54` | Mouse movement, click emulation, corner failsafe |
| **Server & API** | `fastapi` | `0.141.1` | Asynchronous REST and WebSocket control API |
| | `uvicorn` | `0.52.3` | ASGI server |
| | `websockets` | `17.0.1` | Real-time telemetry streaming |
| **Data Handling** | `pandas` | `2.3.3` | Tabular data analysis and manifest manipulation |
| | `h5py` | `3.16.0` | Hierarchical data format for large datasets |
| | `pyarrow` | `25.0.1` | High-performance columnar data storage |
| **Code Quality** | `pytest` | `9.1.1` | Test runner |
| | `ruff` | `0.16.3` | Fast linter and formatter |
| | `mypy` | `2.3.1` | Static type checker |

---

## 3. Frontend Architecture

- **Path:** `frontend/`
- **Framework:** Next.js 15 (App Router), React 19, TypeScript
- **Styling:** TailwindCSS
- **State Management:** Zustand, SWR
- **Package Manager:** npm (`package.json`, `package-lock.json`)
- **Status:** Independent repository (`frontend/.git`) containing its own dependencies in `frontend/node_modules/`.

---

## 4. Environment & Secrets Check

- **`.env` files:** No active `.env` or API credentials found in working directory.
- **`.gitignore` Rules:** Correctly excludes `*.pt`, `*.pth`, `*.onnx`, `*.csv`, `*.parquet`, `data/raw/`, `logs/`, `.venv/`, `.env*`.
- **Recommendation:** Merge recommended entries from `.gitignore.ml-recommendations` into root `.gitignore` to explicitly protect `/data/`, `/datasets/`, `/model_artifacts/`, and `/trash/`.

