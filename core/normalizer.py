from __future__ import annotations

from typing import Any

from core.models import NormalizedRecord

_FIELD_ALIASES = {
    "module_id": ["module_id", "module", "id", "moduleId", "mod_id"],
    "temperature": ["temperature", "temp", "temp_c", "temperature_c"],
    "voltage": ["voltage", "vcc", "v", "supply_voltage"],
    "tx_power": ["tx_power", "tx", "tx_dbm", "txPower"],
    "rx_power": ["rx_power", "rx", "rx_dbm", "rxPower"],
    "status": ["status", "state", "module_status"],
    "lane_count": ["lane_count", "lanes", "lane", "num_lanes"],
}


def _extract_value(record: dict[str, Any], key: str) -> Any:
    for alias in _FIELD_ALIASES[key]:
        if alias in record:
            return record[alias]
    return None


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip().lower().replace("v", "")
    if text.startswith("0x"):
        return float(int(text, 16))
    return float(text)


def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, int):
        return value

    text = str(value).strip().lower()
    if text.startswith("0x"):
        return int(text, 16)
    return int(float(text))


def _normalize_status(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    status_map = {
        "up": "active",
        "on": "active",
        "ok": "active",
        "idle": "standby",
        "err": "fault",
        "down": "disabled",
    }
    return status_map.get(text, text)


def normalize_records(raw_records: list[dict[str, Any]]) -> tuple[list[NormalizedRecord], list[str]]:
    normalized: list[NormalizedRecord] = []
    warnings: list[str] = []

    for idx, raw in enumerate(raw_records):
        record = NormalizedRecord(source_index=idx, source_data=raw)

        record.module_id = _extract_value(raw, "module_id")
        record.status = _normalize_status(_extract_value(raw, "status"))

        if record.status is None:
            record.status = "unknown"
            warnings.append(f"Record {idx}: status missing, defaulted to 'unknown'")

        try:
            record.temperature = _to_float(_extract_value(raw, "temperature"))
            record.voltage = _to_float(_extract_value(raw, "voltage"))
            record.tx_power = _to_float(_extract_value(raw, "tx_power"))
            record.rx_power = _to_float(_extract_value(raw, "rx_power"))
            record.lane_count = _to_int(_extract_value(raw, "lane_count"))
        except ValueError as exc:
            warnings.append(f"Record {idx}: conversion issue: {exc}")

        if record.module_id is not None:
            record.module_id = str(record.module_id)

        normalized.append(record)

    return normalized, warnings
