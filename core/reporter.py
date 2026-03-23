from __future__ import annotations

from core.models import NormalizedRecord, RecordValidationResult


def build_text_report(
    records: list[NormalizedRecord],
    results: list[RecordValidationResult],
    summary: dict,
) -> str:
    lines: list[str] = []
    lines.append("CMIS Data Analysis & Diagnostics Report")
    lines.append("=" * 39)
    lines.append(
        f"SUMMARY: total={summary['total_records']} valid={summary['valid_records']} "
        f"warnings={summary['records_with_warnings']} errors={summary['records_with_errors']} "
        f"anomalies={summary['anomalies_detected']}"
    )
    lines.append(
        f"input_issues: parse_errors={summary['parse_error_count']} "
        f"normalization_warnings={summary['normalization_warning_count']}"
    )

    if summary.get("processing_time_seconds") is not None:
        lines.append(
            f"performance: total_time={summary['processing_time_seconds']:.4f}s "
            f"avg_per_record={summary['avg_time_per_record_seconds']:.6f}s"
        )

    if summary.get("parse_errors"):
        lines.append("\nInput Parse Errors:")
        for err in summary["parse_errors"]:
            lines.append(f"  - {err}")

    if summary.get("normalization_warnings"):
        lines.append("\nNormalization Warnings:")
        for warning in summary["normalization_warnings"]:
            lines.append(f"  - {warning}")

    lines.append("\nRecord Diagnostics:")
    for record, result in zip(records, results):
        lines.append(
            f"- record={record.source_index} module_id={record.module_id} status={record.status}"
        )
        if result.errors:
            for err in result.errors:
                lines.append(f"    [ERROR] {err}")
        if result.warnings:
            for warning in result.warnings:
                lines.append(f"    [WARN ] {warning}")
        if result.diagnostics:
            for diag in result.diagnostics:
                lines.append(f"    [DIAG ] {diag}")
        if not result.errors and not result.warnings and not result.diagnostics:
            lines.append("    [OK   ] No issues detected")

    if summary.get("trend_diagnostics"):
        lines.append("\nCross-Record Trends:")
        for message in summary["trend_diagnostics"]:
            lines.append(f"  - {message}")

    return "\n".join(lines)


def build_batch_text_report(batch_summary: dict) -> str:
    lines = ["Batch Processing Summary", "=" * 24]
    lines.append(
        f"files_processed={batch_summary['files_processed']} total_records={batch_summary['total_records']} "
        f"warnings={batch_summary['total_warnings']} errors={batch_summary['total_errors']} "
        f"anomalies={batch_summary['total_anomalies']}"
    )
    lines.append(
        f"performance: total_time={batch_summary['processing_time_seconds']:.4f}s "
        f"avg_per_record={batch_summary['avg_time_per_record_seconds']:.6f}s"
    )
    if batch_summary["skipped_files"]:
        lines.append("\nSkipped Files:")
        for item in batch_summary["skipped_files"]:
            lines.append(f"  - {item}")

    lines.append("\nPer-file Summary:")
    for item in batch_summary["file_summaries"]:
        lines.append(
            f"- {item['file_name']}: records={item['total_records']} warnings={item['records_with_warnings']} "
            f"errors={item['records_with_errors']} anomalies={item['anomalies_detected']}"
        )
    return "\n".join(lines)


def build_compare_text_report(compare_result: dict) -> str:
    lines: list[str] = []
    lines.append("Snapshot Comparison")
    lines.append("=" * 19)
    info = compare_result["summary"]
    lines.append(
        f"base={info['base_records']} compare={info['compare_records']} changed={info['changed_count']} "
        f"added={info['added_count']} removed={info['removed_count']} anomalies={info['anomaly_count']}"
    )

    if compare_result["added_records"]:
        lines.append("\nAdded Records:")
        for item in compare_result["added_records"]:
            lines.append(f"  - {item}")

    if compare_result["removed_records"]:
        lines.append("\nRemoved Records:")
        for item in compare_result["removed_records"]:
            lines.append(f"  - {item}")

    if compare_result["changed_records"]:
        lines.append("\nChanged Values:")
        for entry in compare_result["changed_records"]:
            lines.append(f"  - module_id={entry['module_id']}")
            for field_name, values in entry["field_changes"].items():
                lines.append(
                    f"      {field_name}: {values['before']} -> {values['after']}"
                )

    if compare_result["anomalies_introduced"]:
        lines.append("\nAnomalies Introduced:")
        for item in compare_result["anomalies_introduced"]:
            lines.append(f"  - {item}")

    return "\n".join(lines)


def build_json_report(
    records: list[NormalizedRecord],
    results: list[RecordValidationResult],
    summary: dict,
    comparison: dict | None = None,
) -> dict:
    payload = {
        "parsed_records": [record.to_dict() for record in records],
        "validation_results": [result.to_dict() for result in results],
        "summary": summary,
    }
    if comparison is not None:
        payload["comparison"] = comparison
    return payload
