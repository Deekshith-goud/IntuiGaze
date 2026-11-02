# Explorer M2-2 Dispatch
Milestone: M2 Linters & Type Checking Strategy
## 2026-10-29T17:27:09Z
You are Explorer M2-2: Linters & Static Analysis Explorer.
Your working directory is: c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m2_2
Your task: Formulate the linter, formatter, and type check execution plan for Milestone 2 (Step 8: Regression and Quality Verification).

MANDATORY INPUTS:
- Read ORIGINAL_REQUEST.md at: c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\ORIGINAL_REQUEST.md
- Read PROJECT.md at: c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\orchestrator\PROJECT.md
- Operating contract: c:\Users\Voriganti\Downloads\INAV\AGENTS.md
- Read skill: c:\Users\Voriganti\Downloads\INAV\.agents\skills\test-quality\SKILL.md
- Read prior survey report at: c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_survey_2\handoff.md

INVESTIGATION OBJECTIVES:
1. Examine configuration and rules in `pyproject.toml` for `ruff` (linter/formatter), `mypy` (type checker), and `bandit`.
2. Determine exact standard commands matching CI workflows:
   - `ruff check backend/ tests/ scripts/`
   - `ruff format --check backend/ tests/`
   - `mypy backend/eyenav/ --ignore-missing-imports`
3. Formulate the verification plan for Worker M2 to execute and confirm zero new errors or regressions introduced.
4. Document full findings and actionable instructions in `c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m2_2\handoff.md`.

CONSTRAINTS:
- You are strictly read-only. Do NOT modify any files.
- Send a message to parent when complete.
