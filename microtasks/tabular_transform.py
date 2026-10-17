#!/usr/bin/env python3
"""Convert CSV to JSON or JSON to CSV using only the standard library."""

from __future__ import annotations

import argparse
import csv
import json
from io import StringIO
from pathlib import Path
from typing import Any, Iterable


def csv_to_records(text: str, numeric_fields: Iterable[str] = ()) -> list[dict[str, Any]]:
    """Parse CSV rows, mapping empty fields to None and selected fields to float."""

    reader = csv.DictReader(StringIO(text))
    if not reader.fieldnames:
        raise ValueError("CSV header is required")

    numeric = set(numeric_fields)
    missing = numeric.difference(reader.fieldnames)
    if missing:
        raise ValueError(f"numeric fields are not present in the header: {sorted(missing)}")

    records: list[dict[str, Any]] = []
    for row_number, row in enumerate(reader, start=2):
        record: dict[str, Any] = {}
        for field in reader.fieldnames:
            value = row.get(field)
            if value is None or value == "":
                record[field] = None
            elif field in numeric:
                try:
                    record[field] = float(value)
                except ValueError as exc:
                    raise ValueError(
                        f"row {row_number}: field {field!r} is not numeric: {value!r}"
                    ) from exc
            else:
                record[field] = value
        records.append(record)
    return records


def _validate_records(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError("JSON input must be an array of objects")
    if not all(isinstance(item, dict) for item in value):
        raise ValueError("every JSON array item must be an object")

    records = value
    for row_number, record in enumerate(records, start=1):
        for field, field_value in record.items():
            if isinstance(field_value, (dict, list)):
                raise ValueError(
                    f"row {row_number}: field {field!r} contains a nested value"
                )
    return records


def json_to_csv(text: str) -> tuple[str, dict[str, Any]]:
    """Convert a JSON array of flat objects to CSV and validate the emitted CSV."""

    records = _validate_records(json.loads(text))
    fieldnames: list[str] = []
    seen: set[str] = set()
    for record in records:
        for field in record:
            if field not in seen:
                seen.add(field)
                fieldnames.append(field)

    if not fieldnames:
        raise ValueError("at least one object field is required")

    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for record in records:
        writer.writerow(
            {field: "" if record.get(field) is None else record.get(field, "") for field in fieldnames}
        )

    csv_text = output.getvalue()
    parsed = list(csv.DictReader(StringIO(csv_text)))
    report = {
        "valid_csv": len(parsed) == len(records),
        "rows": len(records),
        "fields": fieldnames,
        "round_trip_row_count": len(parsed),
    }
    if not report["valid_csv"]:
        raise RuntimeError("generated CSV failed row-count validation")
    return csv_text, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    csv_parser = subparsers.add_parser("csv-to-json")
    csv_parser.add_argument("input", type=Path)
    csv_parser.add_argument("--output", type=Path)
    csv_parser.add_argument("--numeric-field", action="append", default=[])
    csv_parser.add_argument("--sample", type=int, metavar="ROWS")

    json_parser = subparsers.add_parser("json-to-csv")
    json_parser.add_argument("input", type=Path)
    json_parser.add_argument("--output", type=Path)

    args = parser.parse_args()
    source = args.input.read_text(encoding="utf-8-sig")

    if args.command == "csv-to-json":
        records = csv_to_records(source, args.numeric_field)
        payload = records if args.sample is None else records[: args.sample]
        rendered = json.dumps(payload, ensure_ascii=False, indent=2)
        if args.output:
            args.output.write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
        print(f"rows={len(records)}")
        return 0

    rendered, report = json_to_csv(source)
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="")
    else:
        print(rendered, end="")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
