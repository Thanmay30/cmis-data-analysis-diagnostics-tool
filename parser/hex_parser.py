from __future__ import annotations

from pathlib import Path
from typing import Any


def parse_hex_file(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    parse_errors: list[str] = []

    lines = path.read_text(encoding="utf-8").splitlines()
    for idx, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        line = line.replace(",", " ")
        tokens = [token for token in line.split() if token]

        row: dict[str, Any] = {}
        malformed_tokens: list[str] = []
        for token in tokens:
            if "=" not in token:
                malformed_tokens.append(token)
                continue
            key, value = token.split("=", 1)
            row[key.strip()] = value.strip()

        if malformed_tokens:
            parse_errors.append(
                f"Line {idx + 1}: malformed token(s): {', '.join(malformed_tokens)}"
            )

        if row:
            records.append(row)

    return records, parse_errors
