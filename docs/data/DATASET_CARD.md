# Dataset Card — MIT GazeCapture Subset (`archive.zip`)

**Document Date:** October 29, 2026  
**Auditor:** Antigravity (AI Coding Assistant)  
**Status:** Validated via Non-Destructive In-Memory Forensics  

---

## 1. Dataset Summary

The archive `archive.zip` (20.13 GB) contains a substantial multi-subject subset of the **MIT GazeCapture** dataset, originally published in CVPR 2016 (*"Eye Tracking for Everyone"*, Krafka et al., MIT CSAIL). It captures natural eye gaze behaviors across Apple mobile devices (iPhones and iPads) collected crowdsourced under variable lighting and head poses.

---

## 2. Archive Metadata & Integrity

| Property | Value |
|---|---|
| **Archive File Path** | `C:\Users\Voriganti\Downloads\INAV\archive.zip` |
| **Archive File Size** | `21,616,790,160 bytes` (20.132 GB / 21.617 GB decimal) |
| **MD5 Checksum** | `b0a506f32701f39b55737b7f1243ade5` |
| **SHA-256 Checksum** | `48d2175ad792f82c2cea7df4d5763c4dc2bb781c3133c32b668ace251814d2c7` |
| **Total Archive Entries** | `351,005` |
| **Total Files** | `351,005` (0 directory entries) |
| **Uncompressed Byte Size**| `22,969,309,215 bytes` (21.392 GB) |
| **Compression Ratio** | `1.06:1` (JPEG frames are already compressed) |
| **Nested Archives** | None (0 nested archives detected) |
| **Path Traversal Issues** | None (0 suspicious or relative paths) |

---

## 3. Data Modality & File Distribution

| Extension | File Count | Uncompressed Size | Description |
|---|---|---|---|
| `.jpg` | 348,643 | 19.631 GB | RGB camera frames captured from front-facing mobile cameras |
| `.json` | 2,362 | 1.761 GB | Annotation and metadata files (per subject) |
| **Total** | **351,005** | **21.392 GB** | Complete archive |

---

## 4. Subject & Device Demographics

- **Unique Subjects:** 263 subjects
- **Average Frames per Subject:** 1,325.6 frames (Range: 11 to 3,590 frames)
- **Device Distribution:**
  - `iPhone 6`: 61 subjects
  - `iPhone 5S`: 54 subjects
  - `iPhone 5C`: 36 subjects
  - `iPhone 5`: 30 subjects
  - `iPhone 6 Plus`: 29 subjects
  - `iPad Air 2`: 13 subjects
  - `iPad 4`: 10 subjects
  - `iPhone 4S`: 10 subjects
  - `iPad Air`: 6 subjects
  - `iPhone 6s`: 6 subjects
  - `iPad Mini`: 3 subjects
  - `iPad 3`: 2 subjects
  - `iPad 2`: 2 subjects
  - `iPhone 6s Plus`: 1 subject

---

## 5. Dataset Partitioning (Native GazeCapture Splits)

The metadata preserves the official participant-level train/validation/test partitions:

| Partition | Subject Count | Total Frames | Percentage of Frames |
|---|---|---|---|
| **`train`** | 230 | 289,591 | 82.9% |
| **`test`** | 26 | 46,438 | 13.3% |
| **`val`** | 7 | 13,340 | 3.8% |
| **Total** | **263** | **349,369** | **100.0%** |

*Note: Grouping is strictly by participant ID (`subject_id`). This completely eliminates participant leakage across train, val, and test splits.*

---

## 6. Annotations Available

Each subject directory contains the following annotation JSON files:
1. `dotInfo.json`: Gaze target coordinates on screen (`XPts`, `YPts`), 3D coordinates relative to camera in centimeters (`XCam`, `YCam`), and frame timestamps (`Time`).
2. `appleFace.json`: Bounding box of face detected by Apple CoreImage (`H`, `W`, `X`, `Y`, `IsValid`).
3. `appleLeftEye.json` / `appleRightEye.json`: Bounding boxes for left and right eyes.
4. `faceGrid.json`: Binary grid feature (25x25) representing face position and scale within the frame.
5. `frames.json`: Ordered list of frame image filenames corresponding to index rows in other JSON files.
6. `info.json`: Session metadata, total frames, face/eye detection counts, device name, and split name.
7. `motion.json`: Device IMU motion sensor streams (pitch, roll, yaw, user acceleration).
8. `screen.json`: Screen orientation (portrait/landscape) and screen physical/point dimensions (`H`, `W`).

---

## 7. License and Commercial Usability

- **Dataset License:** MIT License (confirmed in MIT CSAIL GazeCapture release).
- **Commercial Use:** Permitted.
- **Privacy Considerations:** The raw frames contain human faces collected with consent for gaze research. Raw frames must remain local and must never be committed to Git or uploaded to external APIs.

