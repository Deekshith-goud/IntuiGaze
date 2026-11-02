#!/usr/bin/env python3
"""Bounded-memory inventory and manifest audit for large IntuiGaze datasets.

Supports recursive file inventory and streaming CSV, TSV, and JSON Lines manifest
checks. Reports structural metadata only; it does not print input row values or
train models. Keep the output report outside the repository if paths are sensitive.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

NULL_STRINGS = {"", "null", "none", "nan", "na", "n/a", "<na>"}


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Return a file SHA-256 using bounded memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory(root: Path) -> dict[str, Any]:
    """Count files and bytes by extension without opening file contents."""
    ext_counts: Counter[str] = Counter()
    ext_bytes: Counter[str] = Counter()
    total_files = 0
    total_bytes = 0
    errors: list[str] = []

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        # Do not traverse symlinked directories.
        dirnames[:] = [d for d in dirnames if not (Path(dirpath) / d).is_symlink()]
        for filename in filenames:
            path = Path(dirpath) / filename
            try:
                if path.is_symlink() or not path.is_file():
                    continue
                size = path.stat().st_size
            except OSError as exc:
                errors.append(f"Could not stat a file under {path.parent}: {type(exc).__name__}")
                continue
            suffix = path.suffix.lower() or "[no extension]"
            total_files += 1
            total_bytes += size
            ext_counts[suffix] += 1
            ext_bytes[suffix] += size

    return {
        "root_exists": root.exists() and root.is_dir(),
        "total_files": total_files,
        "total_bytes": total_bytes,
        "total_gib": round(total_bytes / (1024**3), 4),
        "by_extension": [
            {"extension": ext, "files": count, "bytes": ext_bytes[ext]}
            for ext, count in sorted(ext_counts.items(), key=lambda item: item[1], reverse=True)
        ],
        "filesystem_warnings": errors[:100],
        "filesystem_warning_count": len(errors),
    }


def is_null(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in NULL_STRINGS
    return False


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc.msg}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"JSONL line {line_number} is not an object")
            yield record


def audit_manifest(
    manifest: Path,
    fmt: str,
    id_column: str | None,
    label_column: str | None,
    path_column: str | None,
    data_root: Path,
    max_label_values: int = 30,
) -> dict[str, Any]:
    """Stream a manifest and report schema, nulls, optional key/label/path checks."""
    if fmt == "auto":
        suffix = manifest.suffix.lower()
        fmt = "tsv" if suffix in {".tsv", ".tab"} else "jsonl" if suffix in {".jsonl", ".ndjson"} else "csv"

    if fmt not in {"csv", "tsv", "jsonl"}:
        raise ValueError(f"Unsupported manifest format: {fmt}")
    if not manifest.is_file():
        raise FileNotFoundError(f"Manifest does not exist or is not a file: {manifest}")

    null_counts: Counter[str] = Counter()
    # Bound label-cardinality memory: exact for up to max_label_values categories.
    # Higher-cardinality values are counted in an overflow bucket, not retained.
    label_counts: Counter[str] = Counter()
    untracked_label_occurrences = 0
    id_db = sqlite3.connect("") if id_column else None  # disk-backed temporary SQLite DB
    if id_db is not None:
        id_db.execute("CREATE TABLE seen_ids (value TEXT PRIMARY KEY)")
    duplicate_ids = 0
    missing_paths = 0
    checked_paths = 0
    empty_records = 0
    schema: list[str] | None = None
    rows = 0
    malformed_schema_rows = 0
    size_bytes = manifest.stat().st_size
    rows_since_commit = 0

    def handle_record(record: dict[str, Any]) -> None:
        nonlocal schema, rows, malformed_schema_rows, duplicate_ids
        nonlocal missing_paths, checked_paths, empty_records, untracked_label_occurrences
        nonlocal rows_since_commit
        rows += 1
        rows_since_commit += 1
        current_keys = list(record.keys())
        if schema is None:
            schema = current_keys
        elif set(current_keys) != set(schema):
            malformed_schema_rows += 1

        if not current_keys or all(is_null(value) for value in record.values()):
            empty_records += 1

        for column in schema or []:
            if column not in record or is_null(record.get(column)):
                null_counts[column] += 1

        if id_column:
            if id_column not in record:
                raise ValueError(f"Requested id column {id_column!r} is not in manifest schema")
            value = record.get(id_column)
            if not is_null(value):
                key = str(value)
                if id_db is None:
                    raise RuntimeError("Internal error: ID index was not initialised")
                cursor = id_db.execute("INSERT OR IGNORE INTO seen_ids(value) VALUES (?)", (key,))
                if cursor.rowcount == 0:
                    duplicate_ids += 1
                if rows_since_commit >= 10_000:
                    id_db.commit()
                    rows_since_commit = 0

        if label_column:
            if label_column not in record:
                raise ValueError(f"Requested label column {label_column!r} is not in manifest schema")
            value = record.get(label_column)
            if not is_null(value):
                # Store only aggregate label counts, never complete rows. Keep
                # memory bounded if a supposedly categorical target is continuous.
                label_value = str(value)
                if label_value in label_counts:
                    label_counts[label_value] += 1
                elif len(label_counts) < max_label_values:
                    label_counts[label_value] = 1
                else:
                    untracked_label_occurrences += 1

        if path_column:
            if path_column not in record:
                raise ValueError(f"Requested path column {path_column!r} is not in manifest schema")
            value = record.get(path_column)
            if not is_null(value):
                checked_paths += 1
                candidate = Path(str(value))
                if not candidate.is_absolute():
                    candidate = data_root / candidate
                if not candidate.exists():
                    missing_paths += 1

    try:
        if fmt in {"csv", "tsv"}:
            delimiter = "\t" if fmt == "tsv" else ","
            with manifest.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle, delimiter=delimiter)
                if not reader.fieldnames:
                    raise ValueError("Delimited manifest has no header row")
                schema = list(reader.fieldnames)
                for record in reader:
                    handle_record(record)
        else:
            for record in iter_jsonl(manifest):
                handle_record(record)
        if id_db is not None:
            id_db.commit()
    finally:
        if id_db is not None:
            id_db.close()

    label_total_tracked = sum(label_counts.values())
    report: dict[str, Any] = {
        "manifest": {
            "name": manifest.name,
            "format": fmt,
            "bytes": size_bytes,
            "sha256": sha256_file(manifest),
            "rows": rows,
            "columns": schema or [],
            "schema_column_count": len(schema or []),
            "rows_with_schema_drift": malformed_schema_rows,
            "empty_or_all_null_rows": empty_records,
            "null_counts": {column: null_counts.get(column, 0) for column in (schema or [])},
            "null_rates": {
                column: round(null_counts.get(column, 0) / rows, 6) if rows else None
                for column in (schema or [])
            },
        }
    }
    if id_column:
        report["manifest"]["id_column"] = id_column
        report["manifest"]["duplicate_id_occurrences_after_first"] = duplicate_ids
        report["manifest"]["id_duplicate_check_storage"] = "temporary disk-backed SQLite database"
    if label_column:
        report["manifest"]["label_column"] = label_column
        report["manifest"]["label_categories_tracked"] = len(label_counts)
        report["manifest"]["label_value_counts_tracked"] = [
            {"label": value, "count": count, "fraction_of_all_non_null_labels": round(count / (label_total_tracked + untracked_label_occurrences), 6) if (label_total_tracked + untracked_label_occurrences) else None}
            for value, count in label_counts.most_common(max_label_values)
        ]
        report["manifest"]["label_counts_complete"] = untracked_label_occurrences == 0
        report["manifest"]["untracked_label_occurrences_due_to_cardinality_cap"] = untracked_label_occurrences
        report["manifest"]["label_cardinality_cap"] = max_label_values
    if path_column:
        report["manifest"]["path_column"] = path_column
        report["manifest"]["path_values_checked"] = checked_paths
        report["manifest"]["missing_path_values"] = missing_paths
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="Dataset directory to inventory; must exist")
    parser.add_argument("--manifest", type=Path, help="Optional CSV/TSV/JSONL manifest to audit")
    parser.add_argument("--format", choices=("auto", "csv", "tsv", "jsonl"), default="auto")
    parser.add_argument("--id-column", help="Optional stable sample/event ID column; reports duplicate ID occurrences")
    parser.add_argument("--label-column", help="Optional label column; tracks up to N distinct values with a memory cap")
    parser.add_argument("--path-column", help="Optional media/path column; checks referenced paths")
    parser.add_argument("--output", type=Path, help="JSON report path (prefer outside the repository for private data)")
    parser.add_argument("--max-label-values", type=int, default=30, help="Maximum label values printed in the report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print(f"ERROR: dataset root is not a directory: {root}", file=sys.stderr)
        return 2
    if args.max_label_values < 1:
        print("ERROR: --max-label-values must be >= 1", file=sys.stderr)
        return 2

    report: dict[str, Any] = {
        "tool": "IntuiGaze dataset inventory/audit",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_root_name": root.name,
        "inventory": inventory(root),
        "notes": [
            "Inventory is recursive and does not open media contents.",
            "Manifest rows are streamed. Duplicate IDs use a temporary disk-backed SQLite index; label categories are capped to keep RAM use bounded.",
            "This is a first-pass structural audit; it does not validate gaze geometry, visual quality, consent, labels, or leakage by itself.",
        ],
    }
    if args.manifest:
        manifest = args.manifest.expanduser().resolve()
        try:
            manifest_report = audit_manifest(
                manifest=manifest,
                fmt=args.format,
                id_column=args.id_column,
                label_column=args.label_column,
                path_column=args.path_column,
                data_root=root,
                max_label_values=args.max_label_values,
            )
        except (OSError, ValueError, csv.Error) as exc:
            print(f"ERROR: manifest audit failed: {exc}", file=sys.stderr)
            return 2
        report.update(manifest_report)

    serialised = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        output_path = args.output.expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(serialised + "\n", encoding="utf-8")
        print(f"Audit written to: {output_path}")
    else:
        print(serialised)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
