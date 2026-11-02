## 2026-10-29T17:38:07Z
You are Worker M2: Regression, Quality Verification & Test Hardening Worker.
Your working directory is: c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\worker_m2
Your task: Execute Milestone 2 (Step 8: Regression and Quality Verification & Test Safety Hardening).

MANDATORY INPUTS:
- Read ORIGINAL_REQUEST.md at: c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\ORIGINAL_REQUEST.md
- Read PROJECT.md at: c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\orchestrator\PROJECT.md
- Operating contract: c:\Users\Voriganti\Downloads\INAV\AGENTS.md
- Read Explorer reports:
  * c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m2_1\handoff.md
  * c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m2_2\handoff.md
  * c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m2_3\handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

WRITE OWNERSHIP & SCOPE BOUNDARIES:
- Allowed modifications:
  * Update `conftest.py` to add the autouse safety guard fixture `guard_no_desktop_actuation` (see exact code in `explorer_m2_3/handoff.md:94-132`).
  * Create `tests/test_safety_guard.py` (see exact code in `explorer_m2_3/handoff.md:137-221`).
- STRICTLY FORBIDDEN:
  * DO NOT touch or modify `backend/eyenav/cursor/controller.py` (preserve uncommitted gravity deadzone changes).
  * DO NOT touch or modify `docs/business/ETHICS.md` (preserve uncommitted 2026-Q4 compliance header).
  * DO NOT touch, move, or extract `archive.zip` (must remain intact at 21,616,790,160 bytes).
  * DO NOT move or modify `face_landmarker.task` (must remain at repo root at 3,758,596 bytes).
  * DO NOT run `ruff format` without `--check` (never reformat invariant files).

EXECUTION STEPS:
1. Implement the test hardening safety fixture in `conftest.py` and create `tests/test_safety_guard.py`.
2. Run test regression verification and document outputs:
   - `pytest tests/test_safety_guard.py -v`
   - `pytest tests/ -m "not requires_camera and not accessibility" -v --tb=short`
   - `pytest tests/ -m "not slow and not requires_camera and not accessibility" -v --tb=short`
3. Run linter and static quality checks and document outputs:
   - `ruff check backend/ tests/ scripts/`
   - `ruff format --check backend/ tests/`
   - `mypy backend/eyenav/ --ignore-missing-imports`
4. Run invariant verification:
   `python .agents/teamwork/explorer_m1_3/verify_m1_safety.py --phase post`
5. Document all executed commands, test counts, passing statuses, and invariant checks in `c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\worker_m2\handoff.md`.
6. Send completion message to parent when done.
