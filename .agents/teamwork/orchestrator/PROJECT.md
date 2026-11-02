# Project: IntuiGaze Restructuring, Dataset Integration, and ML Development

## Architecture
- **Core Package (`backend/eyenav/`)**:
  - `vision/`: MediaPipe FaceLandmarker (`landmarks.py`) requiring `face_landmarker.task`, L2CS-Net gaze estimation (`gaze.py`).
  - `cursor/`: `GazeCursorController` (`controller.py`) with uncommitted fixation gravity deadzone (`_FIXATION_DEADZONE_PX = 45.0`), `GazeScreenMapper` polynomial regression (`mapping.py`), filters, detectors, and calibration.
  - `safety.py`: Multi-tier safety policies (confidence gating, cooldown rate limiter, dwell confirmation, emergency stop).
  - `intent.py`: Temporal transformer intent engine (13 classes).
  - `desktop.py` / `pipeline.py`: Real-time application integration.
- **Data & Archive (`archive.zip`, `datasets/`)**:
  - 20.13 GB compressed archive with 351,005 items (348,643 frames, 2,362 JSON files) across 263 subjects.
  - Invariant: `archive.zip` must remain intact and unopened in full on disk. Metadata is streamed/extracted in-memory to construct structured manifests.
- **Quarantine (`trash/`)**:
  - `trash/cleanup_manifest.csv` cataloging 15 obsolete or unreferenced items to move to `trash/pending_review/` and `trash/confirmed_obsolete/`.
- **Test Infrastructure (`tests/`)**:
  - Purely synthetic/mocked tests with zero real desktop actuation.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Quarantine Moves Execution | Move 15 items to `trash/pending_review/` and `trash/confirmed_obsolete/` | M1 | ORIGINAL_REQUEST §R1, survey |
| 2 | Manifest Verification Update | Update `trash/cleanup_manifest.csv` with post-quarantine verification statuses | M1 | ORIGINAL_REQUEST §R1, survey |
| 3 | Safety Invariants Preservation | Guard `controller.py`, `ETHICS.md`, `archive.zip`, `face_landmarker.task` | M1, M2, M3, M4, M5 | ORIGINAL_REQUEST §R2, survey |
| 4 | Test Suite Regression Gate | Run pytest on all 8 test suites, ensuring 0 errors / 0 regressions | M2 | ORIGINAL_REQUEST §R3, survey |
| 5 | Linter & Type Check Gate | Run ruff check, ruff format --check, and mypy with zero errors | M2 | ORIGINAL_REQUEST §R3, survey |
| 6 | ML Problem Definition Doc | Author `docs/ml/ML_PROBLEM_DEFINITION.md` with task formulation & metrics | M3 | ORIGINAL_REQUEST §R4, survey |
| 7 | Data Pipeline & Extraction | Stream/extract metadata JSONs from `archive.zip` without extracting 20GB images | M4 | ORIGINAL_REQUEST §R4, survey |
| 8 | Dataset Manifest Generation | Generate train/val/test manifests partitioned strictly by subject ID | M4 | ORIGINAL_REQUEST §R4, survey |
| 9 | Dataset Schema Validation | Validate dataset manifests using `scripts/audit_dataset.py` schema checks | M4 | ORIGINAL_REQUEST §R4, survey |
| 10 | Baseline Models & Evaluation | Implement and evaluate Center Dummy, Polynomial Ridge, and RF baselines | M5 | ORIGINAL_REQUEST §R4, survey |
| 11 | Evaluation Gates & Documentation | Document error distributions (MAE, P50, P90, Hit@) and update ML docs | M5 | ORIGINAL_REQUEST §R4, survey |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1: Quarantine & Structural Cleanup (Step 7) | Create `trash/` subdirectories, execute moves from manifest, update `cleanup_manifest.csv` | none | DONE |
| 2 | M2: Regression & Quality Verification (Step 8) | Verify pytest test suites, ruff lint/format, and mypy after quarantine | M1 | DONE |
| 3 | M3: ML Problem Definition Specification (Step 9) | Author `docs/ml/ML_PROBLEM_DEFINITION.md` | M2 | IN_PROGRESS |
| 4 | M4: Dataset Pipeline & Validation from archive.zip (Step 10) | Safe metadata extraction, manifest generation, subject splitting, schema audit | M3 | PLANNED |
| 5 | M5: Baseline Models & Evaluation Gates (Step 11) | Implement baseline models, evaluation harness, documentation updates | M4 | PLANNED |
| 6 | M6: Final Verification & Forensic Audit | End-to-end verification and forensic integrity audit | M5 | PLANNED |

## Interface Contracts
### `trash/cleanup_manifest.csv` Schema Contract
- Columns: `original_path,quarantine_path,category,reason,file_type,size_bytes,dependencies_checked,verification_status,restoration_instructions`
- Post-quarantine status: `QUARANTINED_VERIFIED` for moved items.

### Data Pipeline Manifest Schema Contract
- Manifest fields: `frame_id,subject_id,device,orientation,screen_w,screen_h,target_x_pts,target_y_pts,target_x_norm,target_y_norm,face_valid,eye_valid,archive_frame_path`
- Splits: `train` (230 subjects), `val` (7 subjects), `test` (26 subjects) with zero participant leakage.

### ML Baseline Evaluation Contract
- Metrics output: `mae_x_px,mae_y_px,mean_euclidean_px,median_euclidean_px,p90_euclidean_px,p95_euclidean_px,normalized_diagonal_error,hit_at_25px,hit_at_50px,hit_at_100px`.

## Code Layout
- `backend/eyenav/`: Protected core application code.
- `trash/pending_review/`: Quarantined prototypes and unreferenced docs.
- `trash/confirmed_obsolete/`: Quarantined build caches (`__pycache__`).
- `docs/ml/`: Machine learning specifications and reports.
- `datasets/inav_gaze/`: Interim dataset manifests and metadata.
- `tests/`: Automated unit and integration test suites.
