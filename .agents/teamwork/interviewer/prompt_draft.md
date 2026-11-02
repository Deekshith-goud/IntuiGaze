Execute the next stages of IntuiGaze repository restructuring, dataset integration, and ML development, starting with applying approved quarantine changes (Step 7) and proceeding through subsequent execution steps (Steps 8–11) as determined by the team.

Working directory: c:\Users\Voriganti\Downloads\INAV
Integrity mode: development

## Requirements

### R1. Quarantine and Structural Cleanup
Execute approved quarantine moves of unreferenced and obsolete files into the categorized `trash/` directory structure as defined in `trash/cleanup_manifest.csv`, and update the manifest to record post-quarantine verification statuses.

### R2. Safety and Preservation Invariants
Preserve uncommitted changes in `backend/eyenav/cursor/controller.py` and `docs/business/ETHICS.md`. Keep the original `archive.zip` intact. Keep `face_landmarker.task` intact in its active location. Ensure desktop mouse control remains disabled during automated tests.

### R3. Regression and Quality Verification
Verify that all existing automated tests and linters in the repository pass with zero errors or regressions following quarantine changes.

### R4. Dataset Pipeline and ML Development
Advance subsequent execution stages as determined by the team: define the primary ML prediction task (`docs/ml/ML_PROBLEM_DEFINITION.md`), build and validate the data pipeline from `archive.zip` (metadata extraction, manifest generation, schema validation), establish baseline models and evaluation gates, and maintain updated project documentation.

## Acceptance Criteria

### Repository Cleanup and Preservation
- [ ] Quarantined files listed in `trash/cleanup_manifest.csv` are moved to their respective categorized subdirectories under `trash/`.
- [ ] `trash/cleanup_manifest.csv` records the updated verification status of all quarantined items.
- [ ] Uncommitted modifications in `backend/eyenav/cursor/controller.py` and `docs/business/ETHICS.md` remain untouched and intact.
- [ ] `archive.zip` is intact and unmodified.
- [ ] `face_landmarker.task` is present and intact at its active path.

### Regression and Quality Gates
- [ ] All repository test suites (`pytest`) pass with zero errors or failures.
- [ ] All repository linter and type checks pass cleanly with no new errors introduced.

### Pipeline and ML Development (For Executed Stages)
- [ ] If data pipeline is built, generated metadata and manifests pass schema validation and verify data integrity without modifying `archive.zip`.
- [ ] If ML prediction tasks or models are established, `docs/ml/ML_PROBLEM_DEFINITION.md` and baseline model evaluation metrics are documented.
