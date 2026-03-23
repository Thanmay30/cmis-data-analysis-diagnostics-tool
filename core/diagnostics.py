from __future__ import annotations

from collections import defaultdict

from core.models import NormalizedRecord, RecordValidationResult


def _record_level_diagnostics(record: NormalizedRecord, result: RecordValidationResult):
    if record.temperature is not None and record.temperature > 85:
        result.diagnostics.append("Temperature approaching upper threshold")

    if record.status == "active":
        if (record.tx_power is not None and record.tx_power <= 0.2) or (
            record.rx_power is not None and record.rx_power <= 0.2
        ):
            result.diagnostics.append("Status inconsistent with power levels")

    if record.status == "fault" and result.is_valid:
        result.diagnostics.append("Fault set with mostly valid telemetry")


def _trend_diagnostics(records: list[NormalizedRecord], results: list[RecordValidationResult]) -> list[str]:
    by_module: dict[str, list[tuple[NormalizedRecord, RecordValidationResult]]] = defaultdict(list)
    trend_messages: list[str] = []

    for record, result in zip(records, results):
        module_key = record.module_id or f"record-{record.source_index}"
        by_module[module_key].append((record, result))

    for module_id, series in by_module.items():
        if len(series) < 2:
            continue

        temps = [r.temperature for r, _ in series if r.temperature is not None]
        voltages = [r.voltage for r, _ in series if r.voltage is not None]

        if len(temps) >= 3 and temps == sorted(temps) and len(set(temps)) > 1:
            trend_messages.append(
                f"{module_id}: steadily increasing temperature across snapshots"
            )

        if len(voltages) >= 2:
            fluctuation = max(voltages) - min(voltages)
            if fluctuation > 0.25:
                trend_messages.append(
                    f"{module_id}: voltage fluctuating beyond expected range"
                )

        state_values = [r.status for r, _ in series if r.status]
        if len(set(state_values)) > 2:
            trend_messages.append(f"{module_id}: inconsistent states across records")

        unstable_points = sum(1 for _, result in series if result.errors or result.warnings)
        if unstable_points >= 2:
            trend_messages.append(f"{module_id}: possible hardware instability detected")

    return trend_messages


def generate_diagnostics(
    records: list[NormalizedRecord], results: list[RecordValidationResult]
) -> list[str]:
    for record, result in zip(records, results):
        _record_level_diagnostics(record, result)

    return _trend_diagnostics(records, results)
