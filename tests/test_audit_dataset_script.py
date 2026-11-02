"""Smoke tests for the standalone metadata-only dataset auditor."""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_dataset.py"


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - controlled script path, argv list, and no shell
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_inventory_and_csv_manifest(tmp_path: Path) -> None:
    data_root = tmp_path / "dataset"
    data_root.mkdir()
    (data_root / "frame_a.jpg").write_bytes(b"fake-image-a")
    (data_root / "frame_b.jpg").write_bytes(b"fake-image-b")
    manifest = data_root / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sample_id", "label", "path"])
        writer.writeheader()
        writer.writerow({"sample_id": "a", "label": "look", "path": "frame_a.jpg"})
        writer.writerow({"sample_id": "a", "label": "look", "path": "missing.jpg"})
        writer.writerow({"sample_id": "c", "label": "", "path": "frame_b.jpg"})

    output = tmp_path / "report.json"
    result = run_script(
        "--root", str(data_root), "--manifest", str(manifest),
        "--id-column", "sample_id", "--label-column", "label",
        "--path-column", "path", "--output", str(output),
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["inventory"]["total_files"] == 3
    assert report["manifest"]["rows"] == 3
    assert report["manifest"]["duplicate_id_occurrences_after_first"] == 1
    assert report["manifest"]["missing_path_values"] == 1
    assert report["manifest"]["null_counts"]["label"] == 1


def test_jsonl_manifest(tmp_path: Path) -> None:
    data_root = tmp_path / "dataset"
    data_root.mkdir()
    manifest = data_root / "samples.jsonl"
    manifest.write_text(
        '{"id":"1","label":"left"}\n{"id":"2","label":"right"}\n',
        encoding="utf-8",
    )
    result = run_script(
        "--root", str(data_root), "--manifest", str(manifest),
        "--format", "jsonl", "--label-column", "label",
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["manifest"]["rows"] == 2
    assert report["manifest"]["label_categories_tracked"] == 2
    assert report["manifest"]["label_counts_complete"] is True


def test_missing_root_is_rejected(tmp_path: Path) -> None:
    result = run_script("--root", str(tmp_path / "absent"))
    assert result.returncode == 2
    assert "not a directory" in result.stderr
