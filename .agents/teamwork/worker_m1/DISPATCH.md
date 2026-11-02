## 2026-10-29T17:01:39Z
You are Worker M1: Quarantine & Structural Cleanup Worker.
Your working directory is: c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\worker_m1
Your task: Execute Milestone 1 (Step 7: Quarantine Moves and Manifest Verification Update).

MANDATORY INPUTS:
- Read ORIGINAL_REQUEST.md at: c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\ORIGINAL_REQUEST.md
- Read PROJECT.md at: c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\orchestrator\PROJECT.md
- Operating contract: c:\Users\Voriganti\Downloads\INAV\AGENTS.md
- Read Explorer reports:
  * c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m1_1\handoff.md
  * c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m1_2\handoff.md
  * c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m1_3\handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

WRITE OWNERSHIP & SCOPE BOUNDARIES:
- Allowed modifications:
  * Create `trash/pending_review/` (and subdirectories) and `trash/confirmed_obsolete/`
  * Move the 15 items in `trash/cleanup_manifest.csv` to their respective quarantine paths
  * Clean up the 11 stub parent directories (`annotation/`, `assets/`, `cli/`, `desktop/`, `evaluation/`, `experiments/`, `mobile/`, `models/`, `research/`, `sdk/`, `training/`) if empty after moving their README.md
  * Update `trash/cleanup_manifest.csv` verification_status to `QUARANTINED_VERIFIED`
- STRICTLY FORBIDDEN:
  * DO NOT touch or modify `backend/eyenav/cursor/controller.py` (preserve uncommitted gravity deadzone changes)
  * DO NOT touch or modify `docs/business/ETHICS.md` (preserve uncommitted 2026-Q4 compliance header)
  * DO NOT touch, move, or extract `archive.zip` (must remain intact at 21,616,790,160 bytes)
  * DO NOT move or modify `face_landmarker.task` (must remain at repo root at 3,758,596 bytes)
  * DO NOT enable live desktop mouse control in tests.

EXECUTION STEPS:
1. Run pre-execution verification:
   `python .agents/teamwork/explorer_m1_3/verify_m1_safety.py --phase pre`
2. Create directories and execute the 15 quarantine moves using standard filesystem operations (see Python reference script in `explorer_m1_1/handoff.md:193-271`). Remember: all 15 items are untracked by Git, so use filesystem moves (shutil.move / Move-Item), NOT `git mv`.
3. Clean up the 11 empty stub directories.
4. Update `trash/cleanup_manifest.csv` setting `verification_status` to `QUARANTINED_VERIFIED` for all 15 records, preserving all other 8 columns and formatting (see `explorer_m1_2/handoff.md:264-281`).
5. Run post-execution verification:
   `python .agents/teamwork/explorer_m1_3/verify_m1_safety.py --phase post`
6. Run the repository test suite to confirm zero regressions:
   `pytest tests/`
7. Document all actions taken, verification command outputs, and final file states in `c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\worker_m1\handoff.md`.
8. Send completion message to parent when done.
