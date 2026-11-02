# IntuiGaze — Agent Instructions and ML Readiness Pack

This pack is designed to be merged into `Deekshith-goud/IntuiGaze`. It contains repository-level agent instructions, Antigravity-style rules/workflows/skills, an ML development plan, evaluation policy, templates, and a dataset inventory/audit script.

## Important boundary

This is a setup pack prepared from the repository's public README and `pyproject.toml`; it has **not** been committed to GitHub or merged into your local working tree. Merge it locally, review the changes, run checks, then commit and push yourself. It intentionally avoids replacing existing source files.

## Install into the repository

1. Download and extract this ZIP.
2. Open your existing local `IntuiGaze` checkout.
3. Copy the contents of the extracted `IntuiGaze-Agent-ML-Setup-Packet/` directory into the repository root. Merge folders; do not delete existing files.
4. Review `.agent/`, `AGENTS.md`, `docs/ml/`, `configs/ml/`, and `scripts/audit_dataset.py`.
5. Run the local checks shown below.
6. Commit the pack as one separate commit before adding model-training code.

Windows PowerShell example (adjust paths):

```powershell
cd C:\path\to\IntuiGaze
# Extract the ZIP elsewhere, then copy the *contents* into this folder.
# Review first: git status --short
python -m py_compile scripts/audit_dataset.py
python scripts/audit_dataset.py --root "D:\path\to\your\dataset" --output "D:\path\to\private\audit-report.json"
```

For a code-only smoke check, run `python scripts/audit_dataset.py --help`. The dataset path and output report path are examples only.

## Which instruction file does what?

- `AGENTS.md`: concise root-level instructions for agents that read AGENTS.md (including Codex-style agents).
- `.agent/rules/`: persistent project rules, split by responsibility.
- `.agent/workflows/`: explicit task playbooks; launch the relevant one rather than asking an agent to “do everything”.
- `.agent/skills/`: reusable specialist playbooks with triggers and deliverables. Each skill has one distinct purpose.
- `docs/ml/`: human-reviewed ML policy, phases, dataset card, experiment card, scorecards.
- `configs/ml/`: intended experiment/evaluation configuration templates; placeholders are deliberately not guessed.
- `scripts/audit_dataset.py`: streaming, metadata-only dataset audit for CSV, TSV, or JSONL manifests plus recursive file inventory. It does not train a model.
- `optional/ci/intuigaze-quality-gates.yml`: optional CI template. Because the repo already has `.github/workflows/`, first inspect the existing workflows and merge only missing steps; do not add a duplicate workflow blindly.

If your IDE uses a different folder convention, keep `AGENTS.md` and the documentation. Move or link the `.agent` directory only according to that IDE's documented convention; do not create duplicate copies of every rule in multiple files.

## First workflow to run

Run `.agent/workflows/00-repository-audit.md` first. Do not begin training until it has inspected the actual source and written a repository audit report. The repo README describes a gaze-to-screen mapping system, polynomial regression, blink/dwell intent recognition, a 9-point calibration routine, and cursor safety filtering. The audit must verify what is actually implemented rather than assume README claims equal tested behavior.

The public `pyproject.toml` also identifies the Python package as `eyenav`, contains EyENav-related URLs, and sets MyPy's `python_version` to `3.14`, while the README recommends Python 3.11+ and the project metadata says Python `>=3.11`. Treat this as a reconciliation task, not permission to rename modules automatically.

## Suggested first commands

```powershell
python --version
python -m pip install -r requirements-dev.txt
pytest tests/ -q
ruff check backend/ tests/ scripts/
```

Run only commands supported by the current checkout and installed dependencies. If a check fails before your changes, record it as a baseline failure; don't silently suppress it.

## Data handling

Keep the large dataset outside Git. Do not put raw frames, videos, face crops, calibration images, participant IDs, or private manifests into the repository. Store reports outside the repository when they include identifying paths or metadata. Add appropriate ignore patterns only after inspecting the existing `.gitignore` and deciding which artifact directories your project uses.

## Non-negotiable ML gate

Do not report “accuracy” as the main result for gaze-coordinate prediction. It is a regression problem unless the target is a discrete class. Gaze mapping should report pixel-space errors and target-hit rate; gaze-direction models may additionally report angular error if the ground-truth units permit it. Blink/dwell/intent classifiers should report precision, recall, F1, class support, and false-trigger rates. See `docs/ml/METRICS_POLICY.md`.
