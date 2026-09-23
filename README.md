# IntuiGaze

**IntuiGaze** is an experimental eye-tracking system that maps human gaze to screen coordinates to control a computer mouse.

It uses **MediaPipe + OpenCV** to extract facial and iris landmarks, combines them with head-pose information, and translates gaze into OS-level cursor movement.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/OpenCV-Computer%20Vision-5C3EE8?style=flat-square&logo=opencv&logoColor=white" alt="OpenCV">
  <img src="https://img.shields.io/badge/MediaPipe-Facial%20Landmarks-0097A7?style=flat-square" alt="MediaPipe">
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="MIT License">
</p>

<p align="center">
  <img src="https://img.shields.io/github/stars/Deekshith-goud/IntuiGaze?style=flat-square" alt="GitHub Stars">
  <img src="https://img.shields.io/github/forks/Deekshith-goud/IntuiGaze?style=flat-square" alt="GitHub Forks">
  <img src="https://img.shields.io/github/issues/Deekshith-goud/IntuiGaze?style=flat-square" alt="GitHub Issues">
</p>

---

## Features

### Gaze-to-Cursor Mapping

Maps iris and head-pose vectors to screen coordinates using a **polynomial regression model**.

### Intent Recognition

Detects **blinks** and **dwell events** to simulate mouse interactions.

### Online Calibration

Provides a **9-point calibration routine** that adapts the gaze mapping model to the user's eyes and camera setup.

### Safety Filter

Reduces unintended cursor movement and clicks using:

* Confidence thresholds
* Movement smoothing
* Lag compensation
* Click filtering

---

## How It Works

```text
Camera
  │
  ▼
┌─────────────────────┐
│ Face / Iris Tracking│
│     MediaPipe       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Feature Extraction  │
│ Iris + Head Pose    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Gaze Mapping Model  │
│ Polynomial Regression│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Safety + Smoothing  │
└──────────┬──────────┘
           │
           ▼
      Mouse Cursor
```

---

## Quick Start

### 1. Installation

Python **3.11+** is recommended.

```bash
git clone https://github.com/Deekshith-goud/IntuiGaze.git
cd IntuiGaze

python -m venv .venv
```

Activate the virtual environment:

**Windows**

```powershell
.venv\Scripts\activate
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

### 2. Calibration

Before running the desktop controller, calibrate the gaze mapping model for your camera and eye position:

```bash
python scripts/calibrate_ml.py
```

Follow the on-screen prompts and look at each calibration target.

The resulting calibration profile is saved locally and used by the controller.

---

### 3. Run the Desktop Controller

Once calibration is complete:

```bash
python scripts/run_desktop.py
```

The application will begin translating your gaze into mouse movement.

> [!WARNING]
> **Failsafe:** Move your physical mouse to any corner of the screen to immediately stop the controller and regain control.

---

## Project Structure

```text
IntuiGaze/
│
├── backend/
│   └── eyenav/
│       ├── vision/          # Facial and iris landmark extraction
│       ├── mapping/         # Gaze-to-screen mapping
│       ├── intent/          # Blink and dwell detection
│       └── safety/          # Filtering and movement safety
│
├── scripts/
│   ├── calibrate_ml.py      # Calibration routine
│   └── run_desktop.py       # Desktop controller
│
├── tests/                   # Unit and integration tests
│
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

---

## Development & Testing

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Install Playwright's Chromium browser:

```bash
playwright install chromium
```

Run the test suite:

```bash
pytest tests/
```

Run linting:

```bash
ruff check backend/ tests/
```

---

## Tech Stack

| Technology                | Purpose                        |
| ------------------------- | ------------------------------ |
| **Python**                | Core implementation            |
| **OpenCV**                | Camera input & computer vision |
| **MediaPipe**             | Face & iris landmark detection |
| **Polynomial Regression** | Gaze-to-screen mapping         |
| **PyAutoGUI / OS APIs**   | Cursor control                 |
| **Pytest**                | Testing                        |
| **Ruff**                  | Linting                        |

---

## Current Scope

IntuiGaze is currently an **experimental research/project implementation** rather than a production-grade accessibility system.

Accuracy can vary depending on:

* Camera quality
* Lighting conditions
* Head movement
* Distance from the camera
* Screen resolution
* Individual eye characteristics
* Calibration quality

---

## Contributing

Contributions, experiments, bug reports, and improvements are welcome.

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature/your-feature
```

3. Make your changes
4. Run the tests and linter
5. Commit your changes

```bash
git commit -m "feat: add your feature"
```

6. Open a pull request

---

## License

This project is licensed under the **MIT License**.
