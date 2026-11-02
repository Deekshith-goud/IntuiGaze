# IntuiGaze — Data Quality & Integrity Report

**Document Date:** October 29, 2026  
**Auditor:** Antigravity (AI Coding Assistant)  
**Target:** `archive.zip` (MIT GazeCapture)  

---

## 1. Archive & File Integrity

- **Archive Readability:** 100% of the 351,005 archive entries were enumerated and sampled successfully with zero zip format errors.
- **Corrupt Metadata:** 0 corrupt JSON files encountered across all 263 subjects.
- **Path Traversal / Security:** 0 relative paths (`../`) or absolute paths detected inside the zip.
- **Nested Archives:** 0 nested `.zip`, `.tar`, or `.gz` files.

---

## 2. Detection & Annotation Quality

Across the 263 participants:
- **Total Registered Frames:** 348,643 `.jpg` images
- **Mean Face Detection Rate:** `94.06%`
- **Mean Eye Detection Rate:** `68.37%`

### Quality Analysis:
1. **Face Visibility:** Face detection rate is high (>94%), indicating that participants generally maintained their face within the front-camera field of view.
2. **Eye Visibility:** The ~31.6% gap in eye detection reflects:
   - Natural eye blinks during recording.
   - Occlusion from eyelashes, bangs, or glasses frames.
   - Glances at extreme angles outside the screen boundary.
3. **Filtering Requirement:** During data pipeline ingestion, frames with `appleFace.IsValid == 0` or `appleLeftEye.IsValid == 0` or `appleRightEye.IsValid == 0` must be flagged and filtered out of standard gaze regression training.

---

## 3. Data Leakage and Grouping Analysis

### Critical Findings:
1. **Consecutive Temporal Frames:** Each participant session consists of video-recorded frames at ~30 FPS tracking moving dots. Adjacent frames have virtually identical lighting, head pose, eye appearance, and facial structure.
2. **Catastrophic Leakage Warning:** Random frame-level train/validation/test splitting (e.g. `train_test_split(shuffle=True)` on all frames) would cause severe data leakage:
   - The model would memorize specific user eye textures and backgrounds rather than general gaze mechanics.
   - Validation and test scores would appear unrealistically high (~98%+ accuracy), failing completely when deployed to a new user.
3. **Participant-Level Grouping Requirement:**
   - All dataset partitions must be grouped strictly by `subject_id` (participant).
   - The native GazeCapture splits provided in `info.json` (230 train, 7 val, 26 test) must be preserved as the official evaluation benchmark.

