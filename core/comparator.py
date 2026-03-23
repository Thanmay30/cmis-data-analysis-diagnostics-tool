from __future__ import annotations

from core.models import NormalizedRecord, RecordValidationResult

_FIELDS = ["temperature", "voltage", "tx_power", "rx_power", "status", "lane_count"]


def _key(record: NormalizedRecord) -> str:
    return record.module_id or f"record-{record.source_index}"


def _metrics(results: list[RecordValidationResult]) -> tuple[int, int, int]:
    errors = sum(len(item.errors) for item in results)
    warnings = sum(len(item.warnings) for item in results)
    diagnostics = sum(len(item.diagnostics) for item in results)
    return errors, warnings, diagnostics


def compare_snapshots(
    base_records: list[NormalizedRecord],
    base_results: list[RecordValidationResult],
    compare_records: list[NormalizedRecord],
    compare_results: list[RecordValidationResult],
    compare_trend_diagnostics: list[str] | None = None,
) -> dict:
    compare_trend_diagnostics = compare_trend_diagnostics or []

    base_map = {_key(record): record for record in base_records}
    compare_map = {_key(record): record for record in compare_records}

    base_keys = set(base_map.keys())
    compare_keys = set(compare_map.keys())

    added = sorted(compare_keys - base_keys)
    removed = sorted(base_keys - compare_keys)
    common = sorted(base_keys & compare_keys)

    changes: list[dict] = []
    for key in common:
        before = base_map[key]
        after = compare_map[key]

        field_changes: dict[str, dict] = {}
        for field_name in _FIELDS:
            before_value = getattr(before, field_name)
            after_value = getattr(after, field_name)
            if before_value != after_value:
                field_changes[field_name] = {"before": before_value, "after": after_value}

        if field_changes:
            changes.append({"module_id": key, "field_changes": field_changes})

    base_err, base_warn, base_diag = _metrics(base_results)
    cmp_err, cmp_warn, cmp_diag = _metrics(compare_results)

    anomaly_messages: list[str] = []
    if cmp_err > base_err:
        anomaly_messages.append("New validation errors introduced in compared snapshot")
    if cmp_warn > base_warn:
        anomaly_messages.append("Additional warning conditions detected in compared snapshot")
    if cmp_diag > base_diag:
        anomaly_messages.append("New diagnostics findings detected in compared snapshot")
    anomaly_messages.extend(compare_trend_diagnostics)

    return {
        "added_records": added,
        "removed_records": removed,
        "changed_records": changes,
        "anomalies_introduced": anomaly_messages,
        "summary": {
            "base_records": len(base_records),
            "compare_records": len(compare_records),
            "added_count": len(added),
            "removed_count": len(removed),
            "changed_count": len(changes),
            "anomaly_count": len(anomaly_messages),
        },
    }
