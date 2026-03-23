from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def parse_json_file(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    content = path.read_text(encoding="utf-8")
    payload = json.loads(content)

    if isinstance(payload, dict):
        records = payload.get("records")
        if not isinstance(records, list):
            raise ValueError("JSON must contain a 'records' list or be a list itself")
    elif isinstance(payload, list):
        records = payload
    else:
        raise ValueError("JSON root must be a list or object with 'records'")

    normalized_records: list[dict[str, Any]] = []
    parse_errors: list[str] = []

    for idx, item in enumerate(records):
        if not isinstance(item, dict):
            parse_errors.append(f"Record {idx}: expected object, got {type(item).__name__}")
            continue
        normalized_records.append(item)

    return normalized_records, parse_errors
