# IntuiGaze — Dataset Structure and Schema Contract

**Document Date:** October 29, 2026  
**Auditor:** Antigravity (AI Coding Assistant)  
**Dataset:** MIT GazeCapture (`archive.zip`)  

---

## 1. Archive Internal Path Structure

Inside `archive.zip`, entries follow a double-nested subject hierarchy created during upstream Kaggle compression:

```text
archive.zip
├── <subject_id>/<subject_id>/
│   ├── appleFace.json
│   ├── appleLeftEye.json
│   ├── appleRightEye.json
│   ├── dotInfo.json
│   ├── faceGrid.json
│   ├── frames.json
│   ├── info.json
│   ├── motion.json
│   ├── screen.json
│   ├── 00000.jpg
│   ├── 00001.jpg
│   └── ...
```

Example paths:
- `00002/00002/info.json`
- `00002/00002/00000.jpg`

---

## 2. JSON Schema Specifications

### 2.1 `frames.json` (Primary Alignment Index)
- **Type:** JSON Array of Strings
- **Format:** `["00000.jpg", "00001.jpg", "00002.jpg", ...]`
- **Contract:** Every other JSON file index `i` corresponds directly to frame `frames[i]`.

### 2.2 `dotInfo.json` (Ground Truth Gaze Coordinates)
- **Type:** JSON Object containing parallel lists:
  - `DotNum`: `list[int]` — Identifier of the calibration dot shown on screen.
  - `XPts`: `list[float]` — Gaze target X coordinate in screen points/pixels.
  - `YPts`: `list[float]` — Gaze target Y coordinate in screen points/pixels.
  - `XCam`: `list[float]` — Gaze target X displacement relative to camera lens center in **centimeters**.
  - `YCam`: `list[float]` — Gaze target Y displacement relative to camera lens center in **centimeters**.
  - `Time`: `list[float]` — Timestamp in seconds from session start.

### 2.3 `screen.json` (Display Geometry)
- **Type:** JSON Object containing parallel lists:
  - `H`: `list[int]` — Screen height in points (e.g. 568 for iPhone 5/5S/5C in portrait, 320 in landscape).
  - `W`: `list[int]` — Screen width in points (e.g. 320 for iPhone 5/5S/5C in portrait, 568 in landscape).
  - `Orientation`: `list[int]` — Device orientation code (1: Portrait, 2: PortraitUpsideDown, 3: LandscapeRight, 4: LandscapeLeft).

### 2.4 `appleFace.json` (Face Detection Bounding Box)
- **Type:** JSON Object containing parallel lists:
  - `X`, `Y`: `list[float]` — Bounding box top-left corner in frame pixels.
  - `W`, `H`: `list[float]` — Bounding box width and height in frame pixels.
  - `IsValid`: `list[int]` — 1 if face was successfully detected; 0 otherwise.

### 2.5 `appleLeftEye.json` and `appleRightEye.json` (Eye Bounding Boxes)
- **Type:** JSON Object containing parallel lists:
  - `X`, `Y`: `list[float]` — Eye bounding box top-left corner.
  - `W`, `H`: `list[float]` — Eye bounding box width and height.
  - `IsValid`: `list[int]` — 1 if eye detected; 0 otherwise.

### 2.6 `faceGrid.json` (Face Spatial Grid Feature)
- **Type:** JSON Object containing:
  - `X`, `Y`, `W`, `H`: `list[int]` — Normalized grid bounds inside 25x25 cell matrix.
  - `IsValid`: `list[int]` — Validity indicator.

### 2.7 `info.json` (Participant Session Metadata)
- **Type:** JSON Object:
  - `TotalFrames`: `int` — Total frame count in session.
  - `NumFaceDetections`: `int` — Count of frames where face was detected.
  - `NumEyeDetections`: `int` — Count of frames where eyes were detected.
  - `Dataset`: `str` — Partition assigned by GazeCapture authors (`"train"`, `"val"`, `"test"`).
  - `DeviceName`: `str` — Device model (e.g. `"iPhone 6"`, `"iPad Air 2"`).

---

## 3. Recommended Storage Layout

Following the contract, raw and extracted data must live outside Git:

```text
INAV/
├── IntuiGaze/                     # Source-controlled repository root
├── datasets/
│   └── inav_gaze/
│       ├── raw/
│       │   └── archive.zip        # Read-only original archive (preserved)
│       ├── manifests/
│       │   ├── archive_manifest.csv
│       │   ├── train_manifest.csv
│       │   ├── val_manifest.csv
│       │   └── test_manifest.csv
│       ├── interim/               # Metadata JSONs and extracted feature caches
│       └── processed/             # Normalized eye patches / MediaPipe landmark vectors
└── trash/
    ├── pending_review/
    ├── confirmed_obsolete/
    └── cleanup_manifest.csv
```

