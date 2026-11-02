## 2026-10-29T16:38:27Z
You are Explorer 3: Dataset & ML Task Explorer.
Your working directory is: c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_survey_3
Your task: Survey dataset integration requirements, archive.zip contents, ML problem definition, and baseline model criteria.

MANDATORY INPUTS:
- Read ORIGINAL_REQUEST.md at: c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\ORIGINAL_REQUEST.md
- Read skill instructions at: c:\Users\Voriganti\Downloads\INAV\.agents\skills\dataset-auditing\SKILL.md and c:\Users\Voriganti\Downloads\INAV\.agents\skills\gaze-model-evaluation\SKILL.md
- Operating contract: c:\Users\Voriganti\Downloads\INAV\AGENTS.md

INVESTIGATION OBJECTIVES:
1. Safely inspect `archive.zip` structure without extracting the entire zip onto disk or modifying `archive.zip` (e.g. read zip table of contents/manifest). What data files, formats, subjects, and annotations are inside?
2. Check existing docs/code for ML problem definition: check `docs/ml/` (is `docs/ml/ML_PROBLEM_DEFINITION.md` present or planned?), existing ML modules in backend/eyenav or models.
3. Formulate the requirements for the dataset pipeline: metadata extraction, manifest generation, schema validation, train/val/test splitting rules (preserving participant/session boundaries).
4. Formulate the requirements for baseline models and evaluation gates: regression vs classification, metrics, error distributions.
5. Document all findings with clear evidence chains in `c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_survey_3\handoff.md`.

CONSTRAINTS:
- You are strictly read-only. Do NOT modify `archive.zip`, source code, or documentation files.
- Write your report to your assigned folder: `c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_survey_3\handoff.md`.
- Send a message to parent when complete.
