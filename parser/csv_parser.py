from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def parse_csv_file(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    parse_errors: list[str] = []
    records: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("CSV file is missing a header row")

        for idx, row in enumerate(reader):
            clean_row: dict[str, Any] = {}
            malformed = False
            for key, value in row.items():
                if key is None:
                    malformed = True
                    continue
                clean_row[key.strip()] = value.strip() if isinstance(value, str) else value

            if malformed:
                parse_errors.append(f"Row {idx}: malformed CSV columns")
            records.append(clean_row)

    return records, parse_errors
