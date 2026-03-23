from __future__ import annotations

import csv
from pathlib import Path

from core.models import NormalizedRecord, RecordValidationResult


def export_results_csv(
    path: Path,
    records: list[NormalizedRecord],
    results: list[RecordValidationResult],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["record_id", "module_id", "status", "warnings", "errors", "diagnostics"])
        for record, result in zip(records, results):
            writer.writerow(
                [
                    record.source_index,
                    record.module_id,
                    record.status,
                    " | ".join(result.warnings),
                    " | ".join(result.errors),
                    " | ".join(result.diagnostics),
                ]
            )
