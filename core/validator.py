from __future__ import annotations

from core.diagnostics import generate_diagnostics
from core.models import NormalizedRecord, RecordValidationResult

_ALLOWED_STATUS = {"active", "standby", "fault", "disabled", "unknown"}


def _validate_required_fields(record: NormalizedRecord, result: RecordValidationResult):
    if not record.module_id:
        result.errors.append("Missing required field: module_id")

    if record.tx_power is None:
        result.warnings.append("Missing field: tx_power")
    if record.rx_power is None:
        result.warnings.append("Missing field: rx_power")


def _validate_ranges(record: NormalizedRecord, result: RecordValidationResult):
    if record.temperature is not None:
        if record.temperature < -40 or record.temperature > 100:
            result.errors.append(f"Temperature out of range: {record.temperature}")
        elif record.temperature < -35 or record.temperature > 90:
            result.warnings.append(f"Temperature near threshold: {record.temperature}")

    if record.voltage is not None:
        if record.voltage < 2.8 or record.voltage > 3.6:
            result.errors.append(f"Voltage out of range: {record.voltage}")
        elif record.voltage < 2.9 or record.voltage > 3.5:
            result.warnings.append(f"Voltage near threshold: {record.voltage}")

    if record.lane_count is None:
        result.errors.append("Missing required field: lane_count")
    elif record.lane_count <= 0:
        result.errors.append(f"lane_count must be positive: {record.lane_count}")
    elif record.lane_count > 8:
        result.errors.append(f"lane_count suspiciously high: {record.lane_count}")


def _validate_consistency(record: NormalizedRecord, result: RecordValidationResult):
    status = (record.status or "").strip().lower()
    if status not in _ALLOWED_STATUS:
        result.warnings.append(f"Unknown status: {record.status}")

    if status == "active":
        if record.tx_power is not None and record.tx_power <= 0:
            result.warnings.append("Active module with non-positive tx_power")
        if record.rx_power is not None and record.rx_power <= 0:
            result.warnings.append("Active module with non-positive rx_power")

    if status == "disabled":
        if (record.tx_power or 0) > 0.5 or (record.rx_power or 0) > 0.5:
            result.warnings.append("Disabled module reports non-trivial optical power")

    if status == "fault":
        if (record.temperature is not None and record.temperature < 60) and (
            record.voltage is not None and 3.0 <= record.voltage <= 3.5
        ):
            result.warnings.append("Fault status but telemetry appears nominal")


def validate_records(
    records: list[NormalizedRecord],
    parse_errors: list[str],
    normalization_warnings: list[str],
):
    results: list[RecordValidationResult] = []

    for record in records:
        result = RecordValidationResult(source_index=record.source_index)
        _validate_required_fields(record, result)
        _validate_ranges(record, result)
        _validate_consistency(record, result)
        results.append(result)

    trend_diagnostics = generate_diagnostics(records, results)

    summary = {
        "total_records": len(records),
        "valid_records": sum(1 for r in results if r.is_valid),
        "records_with_errors": sum(1 for r in results if r.errors),
        "records_with_warnings": sum(1 for r in results if r.warnings),
        "records_with_diagnostics": sum(1 for r in results if r.diagnostics),
        "diagnostics_count": sum(len(r.diagnostics) for r in results) + len(trend_diagnostics),
        "parse_error_count": len(parse_errors),
        "normalization_warning_count": len(normalization_warnings),
        "parse_errors": parse_errors,
        "normalization_warnings": normalization_warnings,
        "trend_diagnostics": trend_diagnostics,
        "anomalies_detected": (
            sum(1 for r in results if r.errors or r.warnings or r.diagnostics)
            + len(trend_diagnostics)
        ),
    }

    return results, summary
