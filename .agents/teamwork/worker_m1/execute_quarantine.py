"""Milestone 1 Quarantine and Structural Cleanup Execution Script."""

from __future__ import annotations

import csv
import os
from pathlib import Path
import shutil
import sys

REPO_ROOT = Path("c:/Users/Voriganti/Downloads/INAV").resolve()
TRASH_DIR = REPO_ROOT / "trash"
MANIFEST_PATH = TRASH_DIR / "cleanup_manifest.csv"

# Safety Invariant Targets
ARCHIVE_PATH = REPO_ROOT / "archive.zip"
TASK_PATH = REPO_ROOT / "face_landmarker.task"
CONTROLLER_PATH = REPO_ROOT / "backend/eyenav/cursor/controller.py"
ETHICS_PATH = REPO_ROOT / "docs/business/ETHICS.md"

EXPECTED_ARCHIVE_SIZE = 21616790160
EXPECTED_TASK_SIZE = 3758596


def execute_quarantine() -> bool:
    print("=== Step 1: Invariant Pre-check ===")
    assert ARCHIVE_PATH.is_file(), f"{ARCHIVE_PATH} missing!"
    assert (
        ARCHIVE_PATH.stat().st_size == EXPECTED_ARCHIVE_SIZE
    ), f"archive.zip size mismatch: {ARCHIVE_PATH.stat().st_size}"
    print(f"[PASS] archive.zip intact: {EXPECTED_ARCHIVE_SIZE} bytes.")

    assert TASK_PATH.is_file(), f"{TASK_PATH} missing!"
    assert (
        TASK_PATH.stat().st_size == EXPECTED_TASK_SIZE
    ), f"face_landmarker.task size mismatch: {TASK_PATH.stat().st_size}"
    print(f"[PASS] face_landmarker.task intact: {EXPECTED_TASK_SIZE} bytes.")

    controller_text = CONTROLLER_PATH.read_text(encoding="utf-8")
    assert (
        "_FIXATION_DEADZONE_PX = 45.0" in controller_text
    ), "controller.py deadzone logic missing!"
    assert (
        "self._fixation_anchor" in controller_text
    ), "controller.py fixation anchor missing!"
    print("[PASS] controller.py uncommitted deadzone logic verified.")

    ethics_text = ETHICS_PATH.read_text(encoding="utf-8")
    assert (
        "**Last Updated:** 2026-Q4" in ethics_text
    ), "ETHICS.md compliance header missing!"
    print("[PASS] ETHICS.md uncommitted header verified.")

    print("\n=== Step 2: Read Manifest ===")
    assert MANIFEST_PATH.is_file(), f"{MANIFEST_PATH} missing!"
    rows: list[dict[str, str]] = []
    with open(MANIFEST_PATH, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    assert len(rows) == 15, f"Expected 15 records in manifest, found {len(rows)}"
    print(f"[PASS] Loaded {len(rows)} records from manifest.")

    print("\n=== Step 3: Execute Quarantine Moves ===")
    stub_dirs = {
        "annotation", "assets", "cli", "desktop", "evaluation",
        "experiments", "mobile", "models", "research", "sdk", "training"
    }

    for idx, row in enumerate(rows, start=1):
        orig_rel = row["original_path"].rstrip("/\\")
        quar_rel = row["quarantine_path"].rstrip("/\\")

        src_path = REPO_ROOT / orig_rel
        dst_path = REPO_ROOT / quar_rel

        if not src_path.exists():
            raise FileNotFoundError(f"Source path does not exist: {src_path}")

        # Ensure destination parent directory exists
        dst_path.parent.mkdir(parents=True, exist_ok=True)

        # Move file or directory
        print(f"[{idx}/15] Moving: {orig_rel} -> {quar_rel}")
        shutil.move(str(src_path), str(dst_path))

        # Check if source parent was a stub dir and is now empty
        if "/" in orig_rel:
            parent_dir = src_path.parent
            if parent_dir.name in stub_dirs and parent_dir.exists():
                remaining = list(parent_dir.iterdir())
                if not remaining:
                    parent_dir.rmdir()
                    print(f"       Removed empty stub directory: {parent_dir.name}/")
                else:
                    print(f"       [WARN] Stub directory {parent_dir.name}/ not empty: {remaining}")

        # Update row status in memory
        row["verification_status"] = "QUARANTINED_VERIFIED"

    print("\n=== Step 4: Verify Post-Move Filesystem State ===")
    for row in rows:
        orig_rel = row["original_path"].rstrip("/\\")
        quar_rel = row["quarantine_path"].rstrip("/\\")
        src_path = REPO_ROOT / orig_rel
        dst_path = REPO_ROOT / quar_rel

        assert not src_path.exists(), f"Source still exists: {src_path}"
        assert dst_path.exists(), f"Quarantine destination missing: {dst_path}"

        if row["file_type"] != "directory":
            expected_size = int(row["size_bytes"])
            actual_size = dst_path.stat().st_size
            assert actual_size == expected_size, (
                f"Size mismatch for {quar_rel}: actual {actual_size} vs expected {expected_size}"
            )

    print("[PASS] All 15 items verified at quarantine destinations and removed from sources.")

    # Verify stub directories are gone
    for d in stub_dirs:
        p = REPO_ROOT / d
        assert not p.exists(), f"Stub directory {d}/ still exists!"
    print("[PASS] All 11 stub directories confirmed removed.")

    print("\n=== Step 5: Write Updated Manifest ===")
    with open(MANIFEST_PATH, "w", encoding="utf-8", newline="\r\n") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"[PASS] Successfully updated {MANIFEST_PATH} with QUARANTINED_VERIFIED status.")

    print("\n=== Step 6: Post-Operation Invariant Check ===")
    assert (
        ARCHIVE_PATH.stat().st_size == EXPECTED_ARCHIVE_SIZE
    ), f"archive.zip size mismatch: {ARCHIVE_PATH.stat().st_size}"
    assert (
        TASK_PATH.stat().st_size == EXPECTED_TASK_SIZE
    ), f"face_landmarker.task size mismatch: {TASK_PATH.stat().st_size}"
    controller_text_after = CONTROLLER_PATH.read_text(encoding="utf-8")
    assert "_FIXATION_DEADZONE_PX = 45.0" in controller_text_after
    assert "self._fixation_anchor" in controller_text_after
    ethics_text_after = ETHICS_PATH.read_text(encoding="utf-8")
    assert "**Last Updated:** 2026-Q4" in ethics_text_after
    print("[PASS] All 4 safety invariants intact after quarantine execution.")

    return True


if __name__ == "__main__":
    try:
        success = execute_quarantine()
        if success:
            print("\n>>> QUARANTINE EXECUTION COMPLETED SUCCESSFULLY <<<")
            sys.exit(0)
    except Exception as exc:
        print(f"\n>>> QUARANTINE EXECUTION FAILED: {exc} <<<")
        sys.exit(1)
