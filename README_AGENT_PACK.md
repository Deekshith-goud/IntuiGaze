# Pack contents

This archive adds files only; it does not replace `README.md`, `pyproject.toml`, existing workflows, or `.gitignore`.

- Root contract: `AGENTS.md`
- Local merge prompt: `APPLY_PACK_PROMPT.md`
- Persistent rules: `.agent/rules/`
- Agent workflows: `.agent/workflows/`
- Reusable skills: `.agent/skills/`
- ML roadmap/policies/templates: `docs/ml/`
- Example configs: `configs/ml/`
- Streaming data inventory/auditor: `scripts/audit_dataset.py`
- Auditor smoke tests: `tests/test_audit_dataset_script.py`
- Optional CI steps: `optional/ci/intuigaze-quality-gates.yml` (merge into the existing CI only if it does not already cover these checks)
- Reviewed ignore suggestions: `.gitignore.ml-recommendations`

The `.gitignore.ml-recommendations` file is intentionally named as a recommendation and should be merged manually into the existing `.gitignore` after confirming the intended artifact locations.
