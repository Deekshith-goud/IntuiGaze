# Handoff Report: Quarantine File Path & Directory Creation Strategy (Milestone 1 — Step 7)

**Explorer**: Explorer M1-1 (Quarantine File Path & Directory Creation Strategy Explorer)  
**Date**: 2026-10-29  
**Working Directory**: `c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m1_1`  
**Parent Agent**: `49d5375b-5d7a-4c9a-8432-b9df2f718d02`  
**Mission**: Investigate filesystem move operations for Milestone 1 (Step 7: Quarantine and Structural Cleanup), formulating the quarantine directory structure creation strategy and step-by-step worker execution plan.  
**Operating Contract**: `c:\Users\Voriganti\Downloads\INAV\AGENTS.md`  
**Skills Applied**: `repository-archaeology`, `cursor-safety-review`, `test-quality`, `ponytail`

---

## 1. Observation

### 1.1 Manifest and 15 Quarantine Source Items Inventory
Direct inspection of `trash/cleanup_manifest.csv` (18 lines, 3,806 bytes) and corresponding filesystem targets revealed:

| # | Item Path (`original_path`) | Quarantine Target (`quarantine_path`) | Type | Size (Bytes) | Category | Git Status |
|---|-----------------------------|--------------------------------------|------|--------------|----------|------------|
| 1 | `20260801-0708-37.3171907.mp4` | `trash/pending_review/20260801-0708-37.3171907.mp4` | Video | 4,854,051 | Category B | Untracked (`??`) |
| 2 | `exp.py` | `trash/pending_review/exp.py` | Script | 1,299 | Category B | Untracked (`??`) |
| 3 | `eyemovement.txt` | `trash/pending_review/eyemovement.txt` | Text log | 60,248 | Category A | Untracked (`??`) |
| 4 | `__pycache__/` | `trash/confirmed_obsolete/__pycache__/` | Directory | Directory | Category A | Ignored (`.gitignore:2`) |
| 5 | `annotation/README.md` | `trash/pending_review/annotation/README.md` | Markdown | 2,528 | Category B | Untracked (`??`) |
| 6 | `assets/README.md` | `trash/pending_review/assets/README.md` | Markdown | 2,832 | Category B | Untracked (`??`) |
| 7 | `cli/README.md` | `trash/pending_review/cli/README.md` | Markdown | 3,264 | Category B | Untracked (`??`) |
| 8 | `desktop/README.md` | `trash/pending_review/desktop/README.md` | Markdown | 3,853 | Category B | Untracked (`??`) |
| 9 | `evaluation/README.md` | `trash/pending_review/evaluation/README.md` | Markdown | 2,786 | Category B | Untracked (`??`) |
| 10 | `experiments/README.md` | `trash/pending_review/experiments/README.md` | Markdown | 3,446 | Category B | Untracked (`??`) |
| 11 | `mobile/README.md` | `trash/pending_review/mobile/README.md` | Markdown | 3,553 | Category B | Untracked (`??`) |
| 12 | `models/README.md` | `trash/pending_review/models/README.md` | Markdown | 1,868 | Category B | Untracked (`??`) |
| 13 | `research/README.md` | `trash/pending_review/research/README.md` | Markdown | 1,694 | Category B | Untracked (`??`) |
| 14 | `sdk/README.md` | `trash/pending_review/sdk/README.md` | Markdown | 3,234 | Category B | Untracked (`??`) |
| 15 | `training/README.md` | `trash/pending_review/training/README.md` | Markdown | 3,307 | Category B | Untracked (`??`) |

### 1.2 Git Tracking Status
- Running `git ls-files 20260801-0708-37.3171907.mp4 exp.py eyemovement.txt annotation/ assets/ cli/ desktop/ evaluation/ experiments/ mobile/ models/ research/ sdk/ training/` returned **zero files**. None of the 15 items are under Git version control.
- `git status --porcelain` showed:
  ```
   M backend/eyenav/cursor/controller.py
   M docs/business/ETHICS.md
  ?? .agents/
  ?? .gitignore.ml-recommendations
  ?? 20260801-0708-37.3171907.mp4
  ?? AGENTS.md
  ...
  ?? annotation/
  ...
  ?? exp.py
  ?? eyemovement.txt
  ```
- `trash/cleanup_manifest.csv` is matched by `.gitignore` line 39 (`*.csv`).
- `__pycache__/` is matched by `.gitignore` line 2 (`__pycache__/`).

### 1.3 State of Destination Directory `trash/`
- Direct inspection via `list_dir("c:\\Users\\Voriganti\\Downloads\\INAV\\trash")` showed exactly one item: `cleanup_manifest.csv`.
- Destination directories `trash/pending_review/` and `trash/confirmed_obsolete/` **do not exist**.
- Sub-path directories under `trash/pending_review/` (`annotation/`, `assets/`, `cli/`, etc.) **do not exist**.

### 1.4 State of the 11 Stub Parent Directories
- In all 11 directories (`annotation/`, `assets/`, `cli/`, `desktop/`, `evaluation/`, `experiments/`, `mobile/`, `models/`, `research/`, `sdk/`, `training/`), inspection via `list_dir` confirmed that `README.md` is the **sole item** present (0 subdirectories, 1 file).
- Grep across `backend/`, `tests/`, `scripts/`, and `configs/` confirmed that zero production code or test fixtures depend on any file within these 11 directories.

### 1.5 State and Behavior of Root `__pycache__/`
- `list_dir("__pycache__")` confirmed it contains `conftest.cpython-314-pytest-9.1.1.pyc` (3,315 bytes).
- When pytest executes in the repository root, Python's bytecode compiler compiles `conftest.py` into root `__pycache__/`.
- Manifest line 5 explicitly acknowledges this:
  `dependencies_checked: Yes - automatically regenerated by Python runtime`
  `restoration_instructions: Delete or let Python regenerate`

### 1.6 Verification of Safety Invariants
- `backend/eyenav/cursor/controller.py`: `_FIXATION_DEADZONE_PX = 45.0` present at line 54; gravity well present at lines 185–201.
- `docs/business/ETHICS.md`: Header date `**Last Updated:** 2026-Q4` present at line 6.
- `archive.zip`: Present in repo root with exact size `21,616,790,160` bytes.
- `face_landmarker.task`: Present in repo root with exact size `3,758,596` bytes; actively resolved by `landmarks.py:73-81`.
- Pytest baseline run: `68 passed, 8 skipped in 74.92s` (0 failures).

---

## 2. Logic Chain

1. **Tooling Constraint (`git mv` vs Filesystem Move)**:
   - *Observation*: `git ls-files` confirms none of the 15 target items are tracked in Git.
   - *Logic*: Executing `git mv <source> <target>` on an untracked file causes Git to error: `fatal: not under version control`.
   - *Deduction*: The Worker must use standard filesystem move operations (specifically Python `shutil.move` / `pathlib.Path` or PowerShell `Move-Item`), NOT `git mv`.

2. **Directory Structure Creation Requirement**:
   - *Observation*: `trash/` currently contains only `cleanup_manifest.csv`. No subdirectories exist.
   - *Logic*: Moving files into non-existent directories will fail with `FileNotFoundError` or `DirectoryNotFoundException`.
   - *Deduction*: The Worker must proactively create the following directory tree under `trash/` before executing file moves:
     - `trash/pending_review/`
     - `trash/confirmed_obsolete/`
     - `trash/pending_review/annotation/`
     - `trash/pending_review/assets/`
     - `trash/pending_review/cli/`
     - `trash/pending_review/desktop/`
     - `trash/pending_review/evaluation/`
     - `trash/pending_review/experiments/`
     - `trash/pending_review/mobile/`
     - `trash/pending_review/models/`
     - `trash/pending_review/research/`
     - `trash/pending_review/sdk/`
     - `trash/pending_review/training/`

3. **Parent Directory Cleanup Strategy for Placeholder Directories**:
   - *Observation*: The 11 placeholder directories currently contain only `README.md`.
   - *Logic*: When `README.md` is moved to `trash/pending_review/<dir>/README.md`, the root directories (`annotation/`, etc.) become completely empty.
   - *Logic*: Leaving 11 empty folders in the root clutters the project workspace, contradicting the mandate of "Structural Cleanup" in Milestone 1. Git does not track empty directories, and no source code or test references these directories.
   - *Deduction*: The Worker should safely remove each parent directory immediately after moving its `README.md`, provided the directory is completely empty (`os.rmdir(parent_dir)`). If unexpected files are present, the directory must not be removed. If restoration is ever needed, restoring `trash/pending_review/<dir>/README.md` trivially recreates the parent directory.

4. **Handling of Root `__pycache__/`**:
   - *Observation*: `__pycache__/` is a directory containing compiled bytecode from `conftest.py`.
   - *Logic*: Moving the directory `__pycache__` to `trash/confirmed_obsolete/__pycache__` archives the existing bytecode. If Python or pytest runs again in the root, Python will naturally regenerate a fresh `__pycache__/` at the root because `conftest.py` resides there.
   - *Deduction*: The move of `__pycache__/` into `trash/confirmed_obsolete/` is safe and idempotent. Subsequent regeneration of `__pycache__/` during test runs (Milestone 2) is expected and ignored by Git.

5. **Manifest Status Updates**:
   - *Observation*: `trash/cleanup_manifest.csv` currently lists `verification_status` as `PENDING_APPROVAL` for all 15 rows.
   - *Logic*: Per `PROJECT.md` Interface Contracts (§44–46) and `ORIGINAL_REQUEST.md` (§R1, §28), successful completion of quarantine requires updating `verification_status` to `QUARANTINED_VERIFIED`.
   - *Deduction*: The Worker must update column 8 of `trash/cleanup_manifest.csv` to `QUARANTINED_VERIFIED` for each verified item, keeping all other columns unchanged.

---

## 3. Caveats

1. **Bytecode Cache Dynamic Regeneration**:
   Moving root `__pycache__/` into `trash/confirmed_obsolete/__pycache__/` clears the current bytecode cache. However, executing `pytest` or any Python command in the root will regenerate a fresh `__pycache__/` directory. This is not a failure of quarantine, but standard Python runtime behavior.
2. **Git Ignore on Manifest**:
   Because `.gitignore` contains `*.csv` (line 39), `trash/cleanup_manifest.csv` is not tracked in Git unless explicitly forced with `git add -f trash/cleanup_manifest.csv`. The Worker should be aware of this when checking `git status`.
3. **Empty Directory Removal**:
   The recommendation to remove the 11 stub directories after moving their `README.md` files applies strictly if they are empty. If any developer or process has placed an uncommitted file into any of those directories, the script must skip `rmdir` and alert.

---

## 4. Conclusion & Actionable Worker Execution Plan

### Recommended Execution Strategy
The Worker should execute the quarantine cleanup using a deterministic Python script. Python ensures cross-platform path handling, atomic directory creation, robust move semantics, and safe CSV updating.

### Step-by-Step Execution Plan for Worker

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Pre-flight Safety & Invariant Verification          │
│ - Assert controller.py deadzone logic is present            │
│ - Assert ETHICS.md header date is 2026-Q4                   │
│ - Assert archive.zip length is 21,616,790,160 bytes         │
│ - Assert face_landmarker.task length is 3,758,596 bytes     │
│ - Assert all 15 source items exist at original paths        │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ Step 2: Directory Structure Creation                        │
│ - Create trash/pending_review/                              │
│ - Create trash/confirmed_obsolete/                          │
│ - Create 11 subdirectories under trash/pending_review/      │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ Step 3: Execute Filesystem Moves                            │
│ - Move 3 root files to trash/pending_review/                │
│ - Move __pycache__/ to trash/confirmed_obsolete/            │
│ - Move 11 READMEs to trash/pending_review/<subpath>/        │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ Step 4: Clean Up Empty Parent Scaffolding Directories       │
│ - For each of the 11 stub dirs, if empty, os.rmdir()        │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ Step 5: Post-Move Verification                              │
│ - Assert all 15 items exist at target quarantine paths      │
│ - Assert file sizes match expectations                      │
│ - Assert original source paths no longer exist              │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ Step 6: Update cleanup_manifest.csv                         │
│ - Update verification_status to QUARANTINED_VERIFIED        │
│ - Write back CSV preserving schema                          │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ Step 7: Post-Execution Regression Verification              │
│ - Re-verify safety invariants                               │
│ - Run pytest test suite                                     │
└─────────────────────────────────────────────────────────────┘
```

### Reference Implementation Script for Worker
The Worker can save and execute this script or run it directly:

```python
"""Quarantine and Structural Cleanup Execution Script (Milestone 1 — Step 7)."""

import csv
import os
from pathlib import Path
import shutil

REPO_ROOT = Path("c:/Users/Voriganti/Downloads/INAV").resolve()
TRASH_DIR = REPO_ROOT / "trash"
MANIFEST_PATH = TRASH_DIR / "cleanup_manifest.csv"

# 1. Safety Invariants Assertion
assert (
    REPO_ROOT / "archive.zip"
).stat().st_size == 21616790160, "archive.zip size mismatch or missing!"
assert (
    REPO_ROOT / "face_landmarker.task"
).stat().st_size == 3758596, "face_landmarker.task size mismatch or missing!"
controller_code = (
    REPO_ROOT / "backend/eyenav/cursor/controller.py"
).read_text(encoding="utf-8")
assert (
    "_FIXATION_DEADZONE_PX = 45.0" in controller_code
), "controller.py deadzone logic missing!"
ethics_code = (REPO_ROOT / "docs/business/ETHICS.md").read_text(
    encoding="utf-8"
)
assert (
    "**Last Updated:** 2026-Q4" in ethics_code
), "ETHICS.md header missing!"

# 2. Read Manifest
rows = []
with open(MANIFEST_PATH, "r", encoding="utf-8", newline="") as f:
  reader = csv.DictReader(f)
  fieldnames = reader.fieldnames
  for row in reader:
    rows.append(row)

# 3. Execute Moves and Update Verification Status
for row in rows:
  orig_rel = row["original_path"].rstrip("/\\")
  quar_rel = row["quarantine_path"].rstrip("/\\")

  src_path = REPO_ROOT / orig_rel
  dst_path = REPO_ROOT / quar_rel

  if not src_path.exists():
    raise FileNotFoundError(f"Source path does not exist: {src_path}")

  # Ensure destination parent directory exists
  dst_path.parent.mkdir(parents=True, exist_ok=True)

  # Move file or directory
  shutil.move(str(src_path), str(dst_path))
  print(f"Moved: {orig_rel} -> {quar_rel}")

  # Clean up empty parent directory if moving a stub README
  if "/" in orig_rel:
    parent_dir = src_path.parent
    if parent_dir.exists() and not any(parent_dir.iterdir()):
      parent_dir.rmdir()
      print(f"Removed empty directory: {parent_dir.name}/")

  # Update status
  row["verification_status"] = "QUARANTINED_VERIFIED"

# 4. Write Updated Manifest
with open(MANIFEST_PATH, "w", encoding="utf-8", newline="") as f:
  writer = csv.DictWriter(f, fieldnames=fieldnames)
  writer.writeheader()
  writer.writerows(rows)

print(
    "Quarantine moves complete and trash/cleanup_manifest.csv successfully"
    " updated!"
)
```

---

## 5. Verification Method

To independently verify these findings and confirm post-quarantine status:

1. **Verify Filesystem Moves**:
   ```powershell
   # Confirm quarantine directories exist
   Test-Path trash/pending_review
   Test-Path trash/confirmed_obsolete

   # Confirm 4 root items moved
   Test-Path trash/pending_review/20260801-0708-37.3171907.mp4
   Test-Path trash/pending_review/exp.py
   Test-Path trash/pending_review/eyemovement.txt
   Test-Path trash/confirmed_obsolete/__pycache__

   # Confirm original root items no longer exist
   !(Test-Path 20260801-0708-37.3171907.mp4)
   !(Test-Path exp.py)
   !(Test-Path eyemovement.txt)

   # Confirm 11 placeholder READMEs moved and parent dirs removed
   @("annotation", "assets", "cli", "desktop", "evaluation", "experiments", "mobile", "models", "research", "sdk", "training") | ForEach-Object {
       Test-Path "trash/pending_review/$_/README.md"
       !(Test-Path "$_")
   }
   ```

2. **Verify Manifest Status**:
   ```powershell
   # Check that no rows remain PENDING_APPROVAL and all 15 rows are QUARANTINED_VERIFIED
   (Get-Content trash/cleanup_manifest.csv | Select-String "QUARANTINED_VERIFIED").Count # Must equal 15
   (Get-Content trash/cleanup_manifest.csv | Select-String "PENDING_APPROVAL").Count     # Must equal 0
   ```

3. **Verify Safety Invariants & Pytest**:
   ```powershell
   # Check file sizes
   (Get-Item archive.zip).Length           # Must be 21616790160
   (Get-Item face_landmarker.task).Length  # Must be 3758596

   # Check deadzone logic
   Select-String -Path backend/eyenav/cursor/controller.py -Pattern "_FIXATION_DEADZONE_PX = 45.0"

   # Run test suite regression gate
   pytest
   ```

4. **Invalidation Conditions**:
   - If any of the 15 items fails to move or is missing from `trash/`.
   - If `git mv` is attempted, which will fail with a Git fatal error.
   - If any non-empty directory is inadvertently deleted.
   - If any safety invariant (`controller.py`, `ETHICS.md`, `archive.zip`, `face_landmarker.task`) is modified or relocated.
