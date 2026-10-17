#!/usr/bin/env python3
"""Audit and deduplicate UTF-8 CSV using only the Python standard library."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from io import StringIO
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DuplicateRow:
    row: int
    first_seen_row: int
    key: str


def audit_csv(text: str, key_field: str) -> tuple[dict[str, Any], str]:
    """Return an audit report and cleaned CSV.

    Row numbers are one-based file line numbers, so the first data row is 2.
    Empty keys are flagged and retained because silently dropping them would
    hide data loss. Duplicate non-empty keys keep their first occurrence.
    """

    reader = csv.DictReader(StringIO(text))
    fieldnames = reader.fieldnames
    if not fieldnames:
        raise ValueError("CSV header is required")
    if key_field not in fieldnames:
        raise ValueError(f"key field {key_field!r} is not present in the header")

    seen: dict[str, int] = {}
    cleaned: list[dict[str, str]] = []
    duplicates: list[DuplicateRow] = []
    missing_field_rows: list[dict[str, Any]] = []
    missing_key_rows: list[int] = []

    rows_read = 0
    for file_row, row in enumerate(reader, start=2):
        rows_read += 1
        normalized = {name: (row.get(name) or "") for name in fieldnames}
        missing = [name for name, value in normalized.items() if value.strip() == ""]
        if missing:
            missing_field_rows.append({"row": file_row, "fields": missing})

        key = normalized[key_field].strip()
        if not key:
            missing_key_rows.append(file_row)
            cleaned.append(normalized)
            continue
        if key in seen:
            duplicates.append(
                DuplicateRow(row=file_row, first_seen_row=seen[key], key=key)
            )
            continue

        seen[key] = file_row
        cleaned.append(normalized)

    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(cleaned)

    report: dict[str, Any] = {
        "valid_csv": True,
        "key_field": key_field,
        "counts": {
            "rows_read": rows_read,
            "rows_written": len(cleaned),
            "duplicates_removed": len(duplicates),
            "rows_with_missing_fields": len(missing_field_rows),
            "rows_with_missing_key": len(missing_key_rows),
        },
        "duplicates": [asdict(item) for item in duplicates],
        "missing_field_rows": missing_field_rows,
        "missing_key_rows": missing_key_rows,
    }
    return report, output.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--key-field", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report, cleaned = audit_csv(args.input.read_text(encoding="utf-8"), args.key_field)
    if args.output:
        args.output.write_text(cleaned, encoding="utf-8", newline="")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
