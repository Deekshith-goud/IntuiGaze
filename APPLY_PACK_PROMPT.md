# Prompt to apply this pack in your local IntuiGaze workspace

Open the `IntuiGaze` repository root in your coding agent and paste the prompt below. Replace `<EXTRACTED_PACK_PATH>` with the folder where you extracted this ZIP.

---

You are preparing the IntuiGaze repository for a carefully evaluated gaze-learning model. Apply the agent/ML setup pack found at `<EXTRACTED_PACK_PATH>`.

## Safety and merge rules
1. Start with `git status --short` and preserve every existing local change. Never reset, clean, or delete user files.
2. Inspect the existing root instructions, `.agent/` or equivalent agent config, `docs/`, `configs/`, `scripts/`, `tests/`, `.gitignore`, `pyproject.toml`, and every current `.github/workflows/` file.
3. Before copying, report any existing file/path conflicts and explain the merge plan. If `AGENTS.md`, `.agent/rules/`, `.agent/workflows/`, or `.agent/skills/` already contains relevant instructions, consolidate them into canonical files rather than blindly duplicating content.
4. Copy/merge the pack's root-level and `.agent/` instructions, skills, workflows, ML docs, example configs, dataset auditor, and its tests. Do not overwrite stronger existing repo guidance without reviewing it.
5. Do not install a second CI workflow automatically. Inspect the existing CI first, then merge only missing relevant steps from `optional/ci/intuigaze-quality-gates.yml`; preserve existing test matrices and platform requirements. CI must not train models or access camera/mouse hardware.
6. Review `.gitignore.ml-recommendations` and merge only suitable patterns into the existing `.gitignore`. Do not replace `.gitignore` wholesale. Keep dataset media, private manifests, model checkpoints, calibration profiles, and experiment artifacts out of Git.
7. Run the repository audit workflow before adding model training code. The dataset schema, modalities, labels, licence/consent, grouping IDs, coordinate units, compute budget, and target hardware are not yet confirmed. Do not invent them.
8. Do not change the current gaze mapping, calibration, blink/dwell thresholds, confidence filters, or cursor safety behavior as part of this setup change. Do not run code that controls the live desktop mouse.

## Verification
- Run `python -m py_compile scripts/audit_dataset.py`.
- Run `python -m pytest tests/ -q` and report baseline versus new-test failures accurately.
- Run `ruff check backend/ tests/ scripts/` if Ruff is available and configured; do not silently suppress findings.
- Inspect `git diff --check` and `git status --short`.
- Verify the dataset auditor with a small temporary synthetic CSV/JSONL fixture, not the full private dataset.
- Make no claims about model accuracy until an actual baseline is evaluated on valid splits.

## Required final report
Provide (a) files added/merged, (b) conflicts resolved, (c) commands and exact results, (d) failures or checks not run, (e) instructions for running the first repository audit and safe dataset inventory, and (f) the prioritized remaining data/model decisions. Do not train a model in this task.
