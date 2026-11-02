# Explorer M1-3 Dispatch
Milestone: M1 Safety Invariants & Verification Strategy
## 2026-10-29T16:50:43Z
Sender: 49d5375b-5d7a-4c9a-8432-b9df2f718d02
Priority: MESSAGE_PRIORITY_HIGH

You are Explorer M1-3: Safety Invariants & Verification Strategy Explorer.
Your working directory is: c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m1_3
Your task: Formulate verification procedures and guard mechanisms for Safety Invariants during Milestone 1.

MANDATORY INPUTS:
- Read ORIGINAL_REQUEST.md at: c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\ORIGINAL_REQUEST.md
- Read PROJECT.md at: c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\orchestrator\PROJECT.md
- Operating contract: c:\Users\Voriganti\Downloads\INAV\AGENTS.md
- Read skill instructions: c:\Users\Voriganti\Downloads\INAV\.agents\skills\cursor-safety-review\SKILL.md and c:\Users\Voriganti\Downloads\INAV\.agents\skills\test-quality\SKILL.md

INVESTIGATION OBJECTIVES:
1. Define strict preservation checks for:
   - `backend/eyenav/cursor/controller.py` uncommitted changes (gravity well deadzone `_FIXATION_DEADZONE_PX = 45.0`).
   - `docs/business/ETHICS.md` uncommitted changes (`2026-Q4` compliance header).
   - `archive.zip` integrity and byte size (21,616,790,160 bytes).
   - `face_landmarker.task` location at repo root (3,758,596 bytes).
2. Detail pre-execution and post-execution verification steps that Worker and Reviewers must run to guarantee zero unintended file touches or modifications.
3. Formulate how tests should confirm that mouse control remains disabled during automated tests.
4. Document full strategy and recommendations in `c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m1_3\handoff.md`.

CONSTRAINTS:
- You are strictly read-only. Do NOT modify any files.
- Send a message to parent when complete.
