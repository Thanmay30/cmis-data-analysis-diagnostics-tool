from core.comparator import compare_snapshots
from core.normalizer import normalize_records
from core.reporter import build_json_report
from core.validator import validate_records


def test_normalization_aliases_and_defaults():
    raw = [
        {
            "module": "A1",
            "temp": "42.1",
            "supply_voltage": "3.31V",
            "txPower": "1.2",
            "rxPower": "1.1",
            "num_lanes": "4",
            "state": "up",
        }
    ]

    normalized, warnings = normalize_records(raw)
    assert normalized[0].module_id == "A1"
    assert normalized[0].temperature == 42.1
    assert normalized[0].status == "active"
    assert normalized[0].voltage == 3.31
    assert warnings == []


def test_validation_and_diagnostics_generation():
    raw = [
        {
            "module_id": "M-1",
            "temperature": "95",
            "voltage": "2.5",
            "tx_power": "0",
            "rx_power": "-0.2",
            "status": "active",
            "lane_count": "4",
        }
    ]

    normalized, norm_warnings = normalize_records(raw)
    results, summary = validate_records(normalized, parse_errors=[], normalization_warnings=norm_warnings)

    assert any("Voltage out of range" in err for err in results[0].errors)
    assert any("Status inconsistent with power levels" in msg for msg in results[0].diagnostics)
    assert summary["diagnostics_count"] >= 1
    assert summary["anomalies_detected"] >= 1


def test_multi_record_trend_analysis():
    raw = [
        {"module_id": "M-9", "temperature": "60", "voltage": "3.1", "status": "active", "lane_count": "4"},
        {"module_id": "M-9", "temperature": "70", "voltage": "3.3", "status": "standby", "lane_count": "4"},
        {"module_id": "M-9", "temperature": "80", "voltage": "3.5", "status": "fault", "lane_count": "4"},
    ]

    normalized, norm_warnings = normalize_records(raw)
    _, summary = validate_records(normalized, parse_errors=[], normalization_warnings=norm_warnings)

    trend = " ".join(summary["trend_diagnostics"])
    assert "increasing temperature" in trend
    assert "inconsistent states" in trend


def test_comparison_logic_changes_and_anomaly_flags():
    base_raw = [
        {"module_id": "A", "temperature": "35", "voltage": "3.3", "tx_power": "1.0", "rx_power": "0.9", "status": "active", "lane_count": "4"}
    ]
    cmp_raw = [
        {"module_id": "A", "temperature": "91", "voltage": "3.55", "tx_power": "0.1", "rx_power": "0.1", "status": "active", "lane_count": "4"},
        {"module_id": "B", "temperature": "40", "voltage": "3.2", "tx_power": "1.1", "rx_power": "1.0", "status": "standby", "lane_count": "4"},
    ]

    base_records, base_norm_warnings = normalize_records(base_raw)
    base_results, _ = validate_records(base_records, parse_errors=[], normalization_warnings=base_norm_warnings)

    cmp_records, cmp_norm_warnings = normalize_records(cmp_raw)
    cmp_results, cmp_summary = validate_records(cmp_records, parse_errors=[], normalization_warnings=cmp_norm_warnings)

    comparison = compare_snapshots(base_records, base_results, cmp_records, cmp_results, cmp_summary["trend_diagnostics"])

    assert comparison["summary"]["changed_count"] == 1
    assert comparison["summary"]["added_count"] == 1
    assert comparison["anomalies_introduced"]


def test_report_generation_shape():
    raw = [{"module_id": "M1", "temperature": "25", "voltage": "3.3", "lane_count": "4", "status": "standby"}]
    normalized, norm_warnings = normalize_records(raw)
    results, summary = validate_records(normalized, parse_errors=[], normalization_warnings=norm_warnings)
    report = build_json_report(normalized, results, summary)

    assert "parsed_records" in report
    assert "validation_results" in report
    assert "summary" in report
