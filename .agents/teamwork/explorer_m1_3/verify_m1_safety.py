#!/usr/bin/env python3
"""Milestone 1 Safety Invariants and Verification Script.

Zero-dependency verification tool for Worker and Reviewer agents.
Verifies all 4 safety invariants, quarantine execution, manifest integrity,
and mouse actuation isolation.

Usage:
    python .agents/teamwork/explorer_m1_3/verify_m1_safety.py --phase pre
    python .agents/teamwork/explorer_m1_3/verify_m1_safety.py --phase post
    python .agents/teamwork/explorer_m1_3/verify_m1_safety.py --check-mouse-isolation
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

# Repository root (assuming run from repo root or script parent discovery)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Invariant Targets
CONTROLLER_PATH = REPO_ROOT / "backend" / "eyenav" / "cursor" / "controller.py"
ETHICS_PATH = REPO_ROOT / "docs" / "business" / "ETHICS.md"
ARCHIVE_PATH = REPO_ROOT / "archive.zip"
TASK_PATH = REPO_ROOT / "face_landmarker.task"
MANIFEST_PATH = REPO_ROOT / "trash" / "cleanup_manifest.csv"

# Expected Invariant Constants
EXPECTED_CONTROLLER_SIZE = 13766
EXPECTED_ETHICS_SIZE = 9740
EXPECTED_ARCHIVE_SIZE = 21616790160
EXPECTED_TASK_SIZE = 3758596

CONTROLLER_REQUIRED_PATTERNS = [
    "_FIXATION_DEADZONE_PX = 45.0",
    "self._fixation_anchor: tuple[float, float] | None = None",
    "if dist_from_anchor < _FIXATION_DEADZONE_PX:",
]

ETHICS_REQUIRED_PATTERNS = [
    "**Last Updated:** 2026-Q4",
]


def verify_invariants() -> list[str]:
    """Check the 4 strict preservation safety invariants."""
    errors: list[str] = []

    # 1. Controller Invariant
    if not CONTROLLER_PATH.is_file():
        errors.append(f"INVARIANT 1 FAILED: {CONTROLLER_PATH} does not exist.")
    else:
        actual_size = CONTROLLER_PATH.stat().st_size
        if actual_size != EXPECTED_CONTROLLER_SIZE:
            errors.append(
                f"INVARIANT 1 WARNING/CHECK: controller.py size is {actual_size} bytes "
                f"(expected {EXPECTED_CONTROLLER_SIZE})."
            )
        content = CONTROLLER_PATH.read_text(encoding="utf-8")
        for pattern in CONTROLLER_REQUIRED_PATTERNS:
            if pattern not in content:
                errors.append(
                    f"INVARIANT 1 FAILED: controller.py is missing required uncommitted pattern: '{pattern}'"
                )

    # 2. Ethics Invariant
    if not ETHICS_PATH.is_file():
        errors.append(f"INVARIANT 2 FAILED: {ETHICS_PATH} does not exist.")
    else:
        actual_size = ETHICS_PATH.stat().st_size
        if actual_size != EXPECTED_ETHICS_SIZE:
            errors.append(
                f"INVARIANT 2 WARNING/CHECK: ETHICS.md size is {actual_size} bytes "
                f"(expected {EXPECTED_ETHICS_SIZE})."
            )
        content = ETHICS_PATH.read_text(encoding="utf-8")
        for pattern in ETHICS_REQUIRED_PATTERNS:
            if pattern not in content:
                errors.append(
                    f"INVARIANT 2 FAILED: ETHICS.md is missing required uncommitted pattern: '{pattern}'"
                )

    # 3. Archive Invariant
    if not ARCHIVE_PATH.is_file():
        errors.append(f"INVARIANT 3 FAILED: {ARCHIVE_PATH} does not exist at repo root.")
    else:
        actual_size = ARCHIVE_PATH.stat().st_size
        if actual_size != EXPECTED_ARCHIVE_SIZE:
            errors.append(
                f"INVARIANT 3 FAILED: archive.zip size is {actual_size} bytes "
                f"(expected exactly {EXPECTED_ARCHIVE_SIZE} bytes)."
            )

    # 4. Face Landmarker Task Invariant
    if not TASK_PATH.is_file():
        errors.append(f"INVARIANT 4 FAILED: {TASK_PATH} does not exist at repo root.")
    else:
        actual_size = TASK_PATH.stat().st_size
        if actual_size != EXPECTED_TASK_SIZE:
            errors.append(
                f"INVARIANT 4 FAILED: face_landmarker.task size is {actual_size} bytes "
                f"(expected exactly {EXPECTED_TASK_SIZE} bytes)."
            )

    return errors


def read_manifest_records() -> list[dict[str, str]]:
    """Parse trash/cleanup_manifest.csv."""
    if not MANIFEST_PATH.is_file():
        raise FileNotFoundError(f"Manifest not found at {MANIFEST_PATH}")
    with MANIFEST_PATH.open(mode="r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def verify_pre_execution() -> bool:
    """Pre-execution verification routine for Worker/Reviewer."""
    print("=== Milestone 1 Pre-Execution Verification ===")
    all_ok = True

    # 1. Invariants
    inv_errors = verify_invariants()
    if inv_errors:
        print("[FAIL] Invariant checks failed:")
        for e in inv_errors:
            print(f"  - {e}")
        all_ok = False
    else:
        print("[PASS] All 4 Safety Invariants intact and verified.")

    # 2. Manifest and Source Items
    try:
        records = read_manifest_records()
        if len(records) != 15:
            print(f"[FAIL] Manifest contains {len(records)} records (expected 15).")
            all_ok = False
        else:
            print(f"[PASS] Manifest contains exactly 15 cataloged records.")

        pending_count = 0
        sources_found = 0
        for rec in records:
            orig = REPO_ROOT / rec["original_path"]
            quar = REPO_ROOT / rec["quarantine_path"]
            status = rec["verification_status"]

            if status == "PENDING_APPROVAL":
                pending_count += 1

            if orig.exists():
                sources_found += 1
            else:
                print(f"[FAIL] Source item does not exist: {orig}")
                all_ok = False

            if quar.exists():
                print(f"[WARN] Target quarantine path already exists before move: {quar}")

        if pending_count == 15:
            print(f"[PASS] All 15 manifest records are in PENDING_APPROVAL status.")
        else:
            print(f"[WARN] {pending_count}/15 records are in PENDING_APPROVAL status.")

        if sources_found == 15:
            print(f"[PASS] All 15 source items confirmed present at original paths.")

    except Exception as exc:
        print(f"[FAIL] Manifest read error: {exc}")
        all_ok = False

    if all_ok:
        print("\n>>> PRE-EXECUTION AUDIT PASSED: Safe to proceed with quarantine moves. <<<")
    else:
        print("\n>>> PRE-EXECUTION AUDIT FAILED: Do NOT proceed until resolved. <<<")
    return all_ok


def verify_post_execution() -> bool:
    """Post-execution verification routine for Worker/Reviewer."""
    print("=== Milestone 1 Post-Execution Verification ===")
    all_ok = True

    # 1. Invariants
    inv_errors = verify_invariants()
    if inv_errors:
        print("[FAIL] Invariant checks failed:")
        for e in inv_errors:
            print(f"  - {e}")
        all_ok = False
    else:
        print("[PASS] All 4 Safety Invariants intact and verified.")

    # 2. Manifest and Quarantined Items
    try:
        records = read_manifest_records()
        if len(records) != 15:
            print(f"[FAIL] Manifest contains {len(records)} records (expected 15).")
            all_ok = False
        else:
            print(f"[PASS] Manifest contains exactly 15 records.")

        verified_count = 0
        destinations_found = 0
        sources_absent = 0

        for rec in records:
            orig = REPO_ROOT / rec["original_path"]
            quar = REPO_ROOT / rec["quarantine_path"]
            status = rec["verification_status"]

            if status == "QUARANTINED_VERIFIED":
                verified_count += 1
            else:
                print(f"[FAIL] Status for {rec['original_path']} is '{status}' (expected 'QUARANTINED_VERIFIED').")
                all_ok = False

            if not orig.exists():
                sources_absent += 1
            else:
                print(f"[FAIL] Original item still exists at old location: {orig}")
                all_ok = False

            if quar.exists():
                destinations_found += 1
                if rec["file_type"] != "directory":
                    expected_size = int(rec["size_bytes"])
                    actual_size = quar.stat().st_size
                    if actual_size != expected_size:
                        print(
                            f"[WARN] Size mismatch for {quar.name}: actual {actual_size} vs cataloged {expected_size}"
                        )
            else:
                print(f"[FAIL] Quarantined item missing from destination: {quar}")
                all_ok = False

        if verified_count == 15:
            print(f"[PASS] All 15 manifest records updated to QUARANTINED_VERIFIED.")
        if destinations_found == 15:
            print(f"[PASS] All 15 items present in designated trash/ locations.")
        if sources_absent == 15:
            print(f"[PASS] All 15 items confirmed removed from original locations.")

    except Exception as exc:
        print(f"[FAIL] Manifest check error: {exc}")
        all_ok = False

    # 3. Cleanliness of Stub Directories
    stub_dirs = [
        "annotation", "assets", "cli", "desktop", "evaluation",
        "experiments", "mobile", "models", "research", "sdk", "training"
    ]
    for d in stub_dirs:
        p = REPO_ROOT / d
        if p.exists() and not any(p.iterdir()):
            print(f"[NOTE] Empty directory {d}/ remains (can be pruned or kept as empty stub).")
        elif p.exists():
            print(f"[NOTE] Directory {d}/ contains non-quarantined files: {list(p.iterdir())}")

    if all_ok:
        print("\n>>> POST-EXECUTION AUDIT PASSED: Milestone 1 completed successfully with 0 invariant violations. <<<")
    else:
        print("\n>>> POST-EXECUTION AUDIT FAILED: Remediation required. <<<")
    return all_ok


def check_mouse_actuation_isolation() -> bool:
    """Audit test suite files to confirm zero desktop actuation."""
    print("=== Automated Test Mouse Actuation Isolation Audit ===")
    tests_dir = REPO_ROOT / "tests"
    violations: list[str] = []

    prohibited_calls = [
        "pyautogui.moveTo",
        "pyautogui.moveRel",
        "pyautogui.move",
        "pyautogui.click",
        "pyautogui.doubleClick",
        "pyautogui.tripleClick",
        "pyautogui.mouseDown",
        "pyautogui.mouseUp",
        "pyautogui.rightClick",
        "pyautogui.middleClick",
        "pyautogui.scroll",
        "pyautogui.dragTo",
        "pyautogui.dragRel",
    ]

    for py_file in tests_dir.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            for prohibited in prohibited_calls:
                if prohibited in content:
                    violations.append(f"{py_file.relative_to(REPO_ROOT)}: contains prohibited call '{prohibited}'")
        except Exception as exc:
            violations.append(f"Could not read {py_file}: {exc}")

    if violations:
        print("[FAIL] Desktop actuation calls found in automated tests:")
        for v in violations:
            print(f"  - {v}")
        return False
    else:
        print(f"[PASS] Audited all test files under {tests_dir.relative_to(REPO_ROOT)}.")
        print("[PASS] Zero unshielded desktop actuation calls detected in automated tests.")
        return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Milestone 1 Safety Invariants and Verification")
    parser.add_argument("--phase", choices=["pre", "post"], help="Run pre-execution or post-execution audit")
    parser.add_argument("--check-mouse-isolation", action="store_true", help="Audit test files for mouse actuation")

    args = parser.parse_args()

    success = True
    if args.phase == "pre":
        success = verify_pre_execution()
    elif args.phase == "post":
        success = verify_post_execution()

    if getattr(args, "check_mouse_isolation", False):
        mouse_ok = check_mouse_actuation_isolation()
        if not mouse_ok:
            success = False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
