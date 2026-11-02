# Handoff Report: Safety Invariants & Verification Strategy Explorer (Milestone 1)

**Explorer**: Explorer M1-3 (Safety Invariants & Verification Strategy Explorer)  
**Working Directory**: `c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m1_3`  
**Date**: 2026-10-29  
**Parent Agent**: `49d5375b-5d7a-4c9a-8432-b9df2f718d02`  
**Target Milestone**: Milestone 1 (Step 7: Quarantine Moves & Manifest Update)  
**Operating Contract**: `c:\Users\Voriganti\Downloads\INAV\AGENTS.md`  
**Skills Applied**: `cursor-safety-review`, `test-quality`, `repository-archaeology`, `ponytail`

---

## 1. Observation

Direct inspection of the repository files, operating contracts, and test infrastructure yielded the following observations:

### 1.1 Invariant Target 1: `backend/eyenav/cursor/controller.py` Uncommitted Modifications
- **Physical properties**: Path `backend/eyenav/cursor/controller.py`, 291 lines, 13,766 bytes.
- **Git status**: Tracked modified file in working tree (` M backend/eyenav/cursor/controller.py`).
- **Verbatim uncommitted modifications identified**:
  1. *Constant definition* (`controller.py:54`):
     ```python
     54: _FIXATION_DEADZONE_PX = 45.0  # Deadzone for fixation stability
     ```
  2. *Anchor state initialization* (`controller.py:119-121`):
     ```python
     119:         # Fixation gravity well — cursor anchors to the centroid and only
     120:         # moves when the eye deliberately departs by > _FIXATION_DEADZONE_PX.
     121:         self._fixation_anchor: tuple[float, float] | None = None
     ```
  3. *Fixation gravity well algorithm* (`controller.py:184-201`):
     ```python
     184:         else:
     185:             # During fixation: apply gravity well
     186:             if self._fixation_anchor is None:
     187:                 # First fixation frame — lock the anchor to the stable centroid
     188:                 self._fixation_anchor = (stable_x, stable_y)
     189: 
     190:             ax, ay = self._fixation_anchor
     191:             dist_from_anchor = math.hypot(raw_sx - ax, raw_sy - ay)
     192: 
     193:             if dist_from_anchor < _FIXATION_DEADZONE_PX:
     194:                 # Inside dead zone → hold perfectly still at anchor
     195:                 target_x, target_y = ax, ay
     196:             else:
     197:                 # Outside dead zone → the user made a deliberate small movement
     198:                 # Update the anchor to the new stable centroid and follow
     199:                 self._fixation_anchor = (stable_x, stable_y)
     200:                 target_x, target_y = stable_x, stable_y
     ```
- **Rationale**: The 45.0 px gravity well stabilizes the cursor during visual fixations, dampening micro-saccades and pupil jitter without latency in intentional saccades. Preserving these changes without accidental discard or premature commit is a mandatory contract invariant (`ORIGINAL_REQUEST.md:16,29` and `AGENTS.md:Before changing code`).

### 1.2 Invariant Target 2: `docs/business/ETHICS.md` Uncommitted Compliance Header
- **Physical properties**: Path `docs/business/ETHICS.md`, 269 lines, 9,740 bytes.
- **Git status**: Tracked modified file in working tree (` M docs/business/ETHICS.md`).
- **Verbatim uncommitted modification identified** (`ETHICS.md:1-8`):
  ```markdown
  1: # EyeNav — Ethics Assessment
  2: 
  3: **Document Version:** 1.0  
  4: **Status:** Draft — Pending External Review  
  5: **Owner:** Ethics Committee  
  6: **Last Updated:** 2026-Q4  
  7: **Classification:** Public  
  8: 
  ```
- **Rationale**: The `2026-Q4` compliance timestamp records the governance timeline for high-risk biometric AI ethical alignment.

### 1.3 Invariant Target 3: `archive.zip` Integrity and Byte Size
- **Physical properties**: Path `c:\Users\Voriganti\Downloads\INAV\archive.zip`, repository root.
- **Exact size**: `21,616,790,160` bytes (20.132 GB).
- **Archive contents**: Compressed MIT GazeCapture dataset containing 351,005 items (348,643 `.jpg` frames, 2,362 `.json` metadata files) across 263 subject sessions.
- **Contract requirement**: Must remain intact, unopened on disk, and never extracted in-place (`PROJECT.md:12`, `ORIGINAL_REQUEST.md:16,30`, `AGENTS.md:ML/data requirements`). In-memory extraction/streaming is planned for Milestone 4; in Milestone 1 it must be strictly untouched.

### 1.4 Invariant Target 4: `face_landmarker.task` Active Path & Binary Integrity
- **Physical properties**: Path `c:\Users\Voriganti\Downloads\INAV\face_landmarker.task`, repository root.
- **Exact size**: `3,758,596` bytes (~3.58 MB).
- **Runtime dependency**: Direct inspection of `backend/eyenav/vision/landmarks.py:72-82` reveals a hardcoded dependency resolving directly from repository root:
  ```python
  72:         # Try to find the task model
  73:         model_path = Path(__file__).resolve().parent.parent.parent.parent / "face_landmarker.task"
  74:         if not model_path.exists():
  75:             # Fallback to current working directory
  76:             model_path = Path("face_landmarker.task")
  77:             if not model_path.exists():
  78:                 raise FileNotFoundError(
  79:                     "face_landmarker.task not found! Please download it: "
  80:                     "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
  81:                 )
  ```
- **Rationale**: Any relocation or deletion of `face_landmarker.task` causes `landmarks.py` to raise `FileNotFoundError`, disabling the entire MediaPipe 478-landmark and iris detection pipeline.

### 1.5 Desktop Mouse Control and Automated Test Infrastructure
- **Live Actuation in Repository**:
  1. `backend/eyenav/cursor/controller.py`: `GazeCursorController` interacts with OS cursor via `pyautogui.moveTo(final_x, final_y)` (line 211), `pyautogui.click()` (line 257), `pyautogui.scroll(amount)` (line 283). Failsafes present: `pyautogui.FAILSAFE = True` (line 45) and physical mouse movement override pause (`_PHYSICAL_OVERRIDE_PX = 15`, line 143-155).
  2. `exp.py`: Contains unshielded, un-gated `pyautogui.moveTo` (line 23) and `pyautogui.click` (line 30). *Moving `exp.py` into `trash/pending_review/exp.py` as part of M1 eliminates this rogue actuation hazard from the root.*
  3. `scripts/run_desktop.py` and `scripts/target_practice.py`: Explicit manual entrypoints gated by CLI parameters.
- **Current Test Suites (`tests/`)**:
  - 8 test files: `test_config.py`, `test_intent_engine.py`, `test_safety_filter.py`, `test_audit_dataset_script.py`, `integration/test_pipeline_integration.py`, `camera/test_camera_compatibility.py`, `stress/test_sustained_operation.py`, `accessibility/test_wcag_compliance.py`.
  - **Grep check**: `grep_search("pyautogui", SearchPath="tests")` returned **0 matches**.
  - **Inspection**: Zero automated tests import `GazeCursorController` or invoke `pyautogui`. All automated tests execute with synthetic arrays or mock objects.
  - **Contract mandate** (`AGENTS.md:Engineering requirements` & `cursor-safety-review`): "Do not run code that controls the actual mouse or clicks on the desktop during automated tests. Use mock/stub cursor adapters and dry-run mode."

---

## 2. Logic Chain

1. **Vulnerability of Uncommitted Modifications**:
   - *Observation*: `backend/eyenav/cursor/controller.py` and `docs/business/ETHICS.md` are uncommitted working tree changes.
   - *Risk*: A careless `git checkout .`, `git restore .`, `git reset --hard`, or indiscriminate code formatter run would permanently destroy these changes.
   - *Mitigation*: Pre-execution snapshot and post-execution automated verification must check byte lengths, file existence, and specific semantic tokens (`_FIXATION_DEADZONE_PX = 45.0` and `**Last Updated:** 2026-Q4`).

2. **Integrity Boundary of Large Binary Assets**:
   - *Observation*: `archive.zip` is 21.6 GB; `face_landmarker.task` is 3.76 MB.
   - *Risk*: An untargeted move (e.g. wildcard `mv *`) or extraction tool would fill the disk, crash IDE indexing, or sever MediaPipe model loading.
   - *Mitigation*: Strict path and exact byte size assertions before and after every execution phase (`Length == 21616790160` and `Length == 3758596`).

3. **Confining Milestone 1 Blast Radius**:
   - *Observation*: Milestone 1 requires creating 2 primary quarantine subdirectories (`trash/pending_review/`, `trash/confirmed_obsolete/`), moving exactly 15 items, and editing exactly 1 CSV (`trash/cleanup_manifest.csv`).
   - *Risk*: An agent could unintentionally touch unrelated files in `backend/`, `tests/`, `configs/`, or delete empty root directories inappropriately.
   - *Mitigation*: Explicit boundary definition: exactly 15 moves, exactly 1 file edit (`trash/cleanup_manifest.csv`), zero edits to any other file.

4. **Active Test Isolation for Mouse Actuation**:
   - *Observation*: While existing tests do not currently invoke `pyautogui`, nothing currently stops a new test or refactored module from calling real `pyautogui` actuation during `pytest`.
   - *Risk*: Desktop mouse cursor moves or clicks on the developer's screen during test runs, violating `AGENTS.md` and causing OS disruptions.
   - *Mitigation*: Implement an active, autouse safety interceptor in `conftest.py` that raises a hard `RuntimeError` if any test attempts OS mouse actuation, paired with a static audit rule verifying zero unshielded actuation calls in `tests/`.

---

## 3. Caveats

1. **Untracked Nature of Quarantine Candidates**:
   - 14 of the 15 quarantine items are untracked by Git; `__pycache__` and `trash/cleanup_manifest.csv` are gitignored.
   - Consequently, `git diff` cannot be the sole verification mechanism for quarantine execution; filesystem-level inspection of existence, sizes, and paths must be performed.
2. **Hash Performance on 21.6 GB `archive.zip`**:
   - Computing a full SHA-256 over 21,616,790,160 bytes takes 30–60+ seconds and generates significant disk I/O.
   - Exact byte-length verification (`Length == 21616790160`) combined with `LastWriteTime` stability and zip header parsing is far faster (<100ms) and provides robust verification without performance degradation.
3. **Bytecode Cache Regeneration**:
   - Moving root `__pycache__/` to `trash/confirmed_obsolete/__pycache__/` is safe, but subsequent runs of `pytest` will naturally recreate a fresh `__pycache__/` in the repository root. This is standard Python runtime behavior and must not be flagged as a regression.

---

## 4. Conclusion & Recommended Verification Strategy

To guarantee absolute compliance with the operating contract and safety requirements, the Worker and Reviewer agents must adhere to the following 5-point strategy:

### 4.1 Strict Preservation Specification for the 4 Targets

| Target | Expected Path | Required Attributes / Tokens | Verification Rule |
|--------|---------------|------------------------------|-------------------|
| **1. Controller** | `backend/eyenav/cursor/controller.py` | 13,766 bytes, 291 lines, contains `_FIXATION_DEADZONE_PX = 45.0` (line 54) and `self._fixation_anchor` (lines 121, 186-200) | `git status` must show ` M backend/eyenav/cursor/controller.py`; text must contain token |
| **2. Ethics Doc** | `docs/business/ETHICS.md` | 9,740 bytes, 269 lines, contains `**Last Updated:** 2026-Q4` (line 6) | `git status` must show ` M docs/business/ETHICS.md`; text must contain token |
| **3. Archive** | `archive.zip` | Exactly `21,616,790,160` bytes at repo root | Size must equal `21616790160`; write timestamp unchanged |
| **4. Face Task** | `face_landmarker.task` | Exactly `3,758,596` bytes at repo root | File must exist at root; size must equal `3758596` |

### 4.2 Permitted Scope Boundary for Milestone 1
The Worker is strictly constrained to the following operations:
- **Allowed directory creations**:
  - `trash/pending_review/` (and subdirectories `annotation/`, `assets/`, `cli/`, `desktop/`, `evaluation/`, `experiments/`, `mobile/`, `models/`, `research/`, `sdk/`, `training/`)
  - `trash/confirmed_obsolete/`
- **Allowed file moves**: Exactly the 15 items cataloged in `trash/cleanup_manifest.csv`.
- **Allowed directory cleanups**: Removing empty stub parent directories (`annotation/`, etc.) once their single `README.md` has been moved to quarantine.
- **Allowed file modifications**: Exactly 1 file: `trash/cleanup_manifest.csv` (updating `verification_status` column from `PENDING_APPROVAL` to `QUARANTINED_VERIFIED`).
- **FORBIDDEN**: Any modification, deletion, or renaming of any other file in `backend/`, `tests/`, `configs/`, `docs/`, `scripts/`, or root directory.

### 4.3 Pre-Execution and Post-Execution Checklists

#### Pre-Execution Checklist (Worker before touching files)
- [ ] Run `python .agents/teamwork/explorer_m1_3/verify_m1_safety.py --phase pre` -> Output reports `PRE-EXECUTION AUDIT PASSED`.
- [ ] Verify `git status --porcelain` shows only expected dirty files (`controller.py`, `ETHICS.md`, untracked items).
- [ ] Verify baseline test suite passes: `pytest tests/` (68 passed, 8 skipped).

#### Post-Execution Checklist (Worker and Reviewer)
- [ ] Run `python .agents/teamwork/explorer_m1_3/verify_m1_safety.py --phase post` -> Output reports `POST-EXECUTION AUDIT PASSED`.
- [ ] Verify 15 source items no longer exist at original paths.
- [ ] Verify 15 quarantined items exist at designated paths under `trash/`.
- [ ] Verify `trash/cleanup_manifest.csv` contains 15 rows with `QUARANTINED_VERIFIED` and zero `PENDING_APPROVAL`.
- [ ] Verify `backend/eyenav/cursor/controller.py` and `docs/business/ETHICS.md` are 100% preserved.
- [ ] Verify `archive.zip` and `face_landmarker.task` remain intact at repo root.
- [ ] Run regression gate: `pytest tests/` passes with 0 failures / 0 regressions.
- [ ] Run linter gate: `ruff check .` and `ruff format --check .` introduce zero new errors.

### 4.4 Automated Verification Script
A dedicated zero-dependency verification utility has been placed at:
`c:\Users\Voriganti\Downloads\INAV\.agents\teamwork\explorer_m1_3\verify_m1_safety.py`

Features:
- `--phase pre`: Checks invariant preservation, manifest syntax, and existence of all 15 source items.
- `--phase post`: Checks invariant preservation, verified relocation of all 15 items to `trash/`, absence from old paths, and status update to `QUARANTINED_VERIFIED`.
- `--check-mouse-isolation`: Scans all test files to verify zero unshielded desktop actuation calls.

### 4.5 Active Test Guard for Mouse Actuation Isolation
To ensure compliance with `AGENTS.md` ("Do not run code that controls the actual mouse or clicks on the desktop during automated tests"), we recommend adding the following autouse fixture to `conftest.py` in Milestone 2:

```python
@pytest.fixture(autouse=True)
def guard_no_desktop_actuation(monkeypatch):
    """Safety guard: Intercept and fail any physical OS desktop actuation during tests."""
    def forbidden_actuation(*args, **kwargs):
        raise RuntimeError(
            "CRITICAL SAFETY VIOLATION: Automated test attempted physical desktop mouse/keyboard actuation! "
            "Tests must use mock cursor adapters or dry-run mode per AGENTS.md."
        )

    try:
        import pyautogui
        for fn_name in [
            "moveTo", "moveRel", "move",
            "click", "doubleClick", "tripleClick",
            "mouseDown", "mouseUp", "rightClick", "middleClick",
            "dragTo", "dragRel", "drag",
            "scroll", "hscroll", "vscroll",
            "write", "press", "keyDown", "keyUp", "hotkey"
        ]:
            if hasattr(pyautogui, fn_name):
                monkeypatch.setattr(pyautogui, fn_name, forbidden_actuation)
    except ImportError:
        pass
```

---

## 5. Verification Method

To independently verify the safety invariants and test isolation, execute the following commands from the repository root:

### 1. Invariants Independent Verification (PowerShell)
```powershell
# 1. Verify controller.py deadzone logic
Select-String -Path "backend/eyenav/cursor/controller.py" -Pattern "_FIXATION_DEADZONE_PX = 45.0"
Select-String -Path "backend/eyenav/cursor/controller.py" -Pattern "self._fixation_anchor"

# 2. Verify ETHICS.md compliance header
Select-String -Path "docs/business/ETHICS.md" -Pattern "\*\*Last Updated:\*\* 2026-Q4"

# 3. Verify archive.zip byte size (must equal 21616790160)
(Get-Item "archive.zip").Length

# 4. Verify face_landmarker.task byte size (must equal 3758596)
(Get-Item "face_landmarker.task").Length
```

### 2. Full Automated Pre/Post Verification (Python)
```bash
# Pre-execution check (Worker prior to moving files)
python .agents/teamwork/explorer_m1_3/verify_m1_safety.py --phase pre

# Post-execution check (Worker and Reviewers after moves and manifest update)
python .agents/teamwork/explorer_m1_3/verify_m1_safety.py --phase post

# Test mouse isolation audit
python .agents/teamwork/explorer_m1_3/verify_m1_safety.py --check-mouse-isolation
```

### 3. Test Suite Regression Gate
```bash
pytest tests/ -v
```
Expected output: 68 passed, 8 skipped (camera/WCAG), 0 failures.

### 4. Invalidation Conditions
The verification FAILS if any of the following occur:
1. `_FIXATION_DEADZONE_PX` or gravity well deadzone logic in `backend/eyenav/cursor/controller.py` is removed, modified, or committed.
2. `**Last Updated:** 2026-Q4` in `docs/business/ETHICS.md` is removed, modified, or committed.
3. `archive.zip` is moved, renamed, extracted, or altered from 21,616,790,160 bytes.
4. `face_landmarker.task` is moved from the root or altered from 3,758,596 bytes.
5. Any file outside `trash/` (other than the 15 moved items) is modified, deleted, or touched.
6. Any automated test attempts to actuate the physical mouse or click on the user desktop.
