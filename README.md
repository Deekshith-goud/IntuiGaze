# IntuiGaze

IntuiGaze is an experimental eye-tracking system that maps human gaze to screen coordinates to control a computer mouse. It uses computer vision (MediaPipe/OpenCV) to extract facial landmarks and translates them into OS-level cursor movements.

## Features
- **Gaze-to-Cursor Mapping**: Translates iris and head pose vectors into screen coordinates using a polynomial regression model.
- **Intent Recognition**: Detects blinks and dwells to simulate mouse clicks.
- **Online Calibration**: A 9-point calibration routine that personalizes the gaze mapping model.
- **Safety Filter**: Prevents unintended clicks or sudden movements using confidence thresholds and lag compensation.

## Quick Start

### 1. Installation
Clone the repository and install the dependencies. Python 3.11+ is recommended.
```bash
git clone https://github.com/Deekshith-goud/IntuiGaze.git
cd IntuiGaze
python -m venv .venv
# Activate virtual environment
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Calibration
Before using the desktop controller, you must run the calibration routine to adapt the model to your eyes and camera setup.
```bash
python scripts/calibrate_ml.py
```
Follow the on-screen prompts and look at the targets. The calibration profile will be saved locally.

### 3. Run Desktop Controller
Once calibrated, you can start the desktop controller which will take control of your mouse.
```bash
python scripts/run_desktop.py
```
> **Failsafe**: Move your physical mouse to any corner of the screen to immediately stop the script and regain control.

## Project Structure
- `backend/eyenav/` - Core library containing vision extraction, cursor mapping, and safety filters.
- `scripts/` - Executable scripts for calibration, demos, and running the desktop controller.
- `tests/` - Unit and integration tests.

## Development & Testing
To run the test suite and linting checks:
```bash
pip install -r requirements-dev.txt
playwright install chromium
pytest tests/
ruff check backend/ tests/
```

## License
MIT License
