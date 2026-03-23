from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Callable

from core.comparator import compare_snapshots
from core.exporter import export_results_csv
from core.normalizer import normalize_records
from core.reporter import (
    build_batch_text_report,
    build_compare_text_report,
    build_json_report,
    build_text_report,
)
from core.validator import validate_records
from parser.csv_parser import parse_csv_file
from parser.hex_parser import parse_hex_file
from parser.json_parser import parse_json_file


def _parse_input(input_path: Path, input_format: str):
    if input_format == "json":
        return parse_json_file(input_path)
    if input_format == "csv":
        return parse_csv_file(input_path)
    if input_format == "hex":
        return parse_hex_file(input_path)
    raise ValueError(f"Unsupported format: {input_format}")


def _infer_format(path: Path, fallback: str | None = None) -> str:
    extension_map = {".json": "json", ".csv": "csv", ".hex": "hex", ".txt": "hex"}
    inferred = extension_map.get(path.suffix.lower())
    if inferred:
        return inferred
    if fallback:
        return fallback
    raise ValueError(f"Cannot infer format from file extension: {path}")


def _run_single(input_path: Path, input_format: str) -> tuple[list, list, dict]:
    start = time.perf_counter()
    raw_records, parse_errors = _parse_input(input_path, input_format)
    normalized_records, normalization_warnings = normalize_records(raw_records)
    validation_results, summary = validate_records(normalized_records, parse_errors, normalization_warnings)
    elapsed = time.perf_counter() - start
    total_records = max(1, summary["total_records"])
    summary["processing_time_seconds"] = elapsed
    summary["avg_time_per_record_seconds"] = elapsed / total_records
    return normalized_records, validation_results, summary


def _apply_filters(records: list, results: list, only_errors: bool, only_warnings: bool, only_anomalies: bool):
    filtered = []
    for record, result in zip(records, results):
        has_error = bool(result.errors)
        has_warning = bool(result.warnings)
        has_anomaly = has_error or has_warning or bool(result.diagnostics)

        keep = True
        if only_errors and not has_error:
            keep = False
        if only_warnings and not has_warning:
            keep = False
        if only_anomalies and not has_anomaly:
            keep = False

        if keep:
            filtered.append((record, result))

    if not filtered:
        return [], []
    out_records, out_results = zip(*filtered)
    return list(out_records), list(out_results)


def run_batch(folder_path: Path) -> int:
    if not folder_path.exists() or not folder_path.is_dir():
        print(f"Batch folder not found: {folder_path}", file=sys.stderr)
        return 1

    start = time.perf_counter()
    file_summaries = []
    skipped = []
    total_records = 0
    total_warnings = 0
    total_errors = 0
    total_anomalies = 0

    for file_path in sorted(folder_path.iterdir()):
        if not file_path.is_file():
            continue
        try:
            data_format = _infer_format(file_path)
            _, _, summary = _run_single(file_path, data_format)
            file_summaries.append({"file_name": file_path.name, **summary})
            total_records += summary["total_records"]
            total_warnings += summary["records_with_warnings"]
            total_errors += summary["records_with_errors"]
            total_anomalies += summary["anomalies_detected"]
        except Exception as exc:
            skipped.append(f"{file_path.name}: {exc}")

    elapsed = time.perf_counter() - start
    avg = elapsed / max(1, total_records)

    batch_summary = {
        "files_processed": len(file_summaries),
        "total_records": total_records,
        "total_warnings": total_warnings,
        "total_errors": total_errors,
        "total_anomalies": total_anomalies,
        "processing_time_seconds": elapsed,
        "avg_time_per_record_seconds": avg,
        "file_summaries": file_summaries,
        "skipped_files": skipped,
    }

    print(build_batch_text_report(batch_summary))
    return 0 if file_summaries else 1


def run(
    input_path: Path,
    input_format: str,
    output_json: Path | None = None,
    compare_path: Path | None = None,
    compare_format: str | None = None,
    export_csv: Path | None = None,
    only_errors: bool = False,
    only_warnings: bool = False,
    only_anomalies: bool = False,
) -> int:
    try:
        records, results, summary = _run_single(input_path, input_format)
    except Exception as exc:
        print(f"Input parsing failed: {exc}", file=sys.stderr)
        return 1

    records, results = _apply_filters(records, results, only_errors, only_warnings, only_anomalies)
    print(build_text_report(records, results, summary))

    comparison_payload = None
    if compare_path:
        if not compare_path.exists():
            print(f"Compare file not found: {compare_path}", file=sys.stderr)
            return 1

        try:
            cmp_format = compare_format or _infer_format(compare_path, input_format)
            cmp_records, cmp_results, cmp_summary = _run_single(compare_path, cmp_format)
            comparison_payload = compare_snapshots(
                records,
                results,
                cmp_records,
                cmp_results,
                cmp_summary.get("trend_diagnostics", []),
            )
            print("\n" + build_compare_text_report(comparison_payload))
        except Exception as exc:
            print(f"Comparison failed: {exc}", file=sys.stderr)
            return 1

    if output_json:
        report_data = build_json_report(records, results, summary, comparison_payload)
        output_json.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
        print(f"\nSaved JSON report: {output_json}")

    if export_csv:
        export_results_csv(export_csv, records, results)
        print(f"Saved CSV report: {export_csv}")

    return 0


def run_interactive(input_fn: Callable[[str], str] = input, print_fn: Callable[..., None] = print) -> int:
    last_summary: dict | None = None
    while True:
        print_fn("\nCMIS Diagnostics Interactive Menu")
        print_fn("1. Analyze file")
        print_fn("2. Compare two files")
        print_fn("3. View summary statistics")
        print_fn("4. Exit")
        choice = input_fn("Select option: ").strip()

        if choice == "1":
            path = Path(input_fn("Input file path: ").strip())
            fmt = input_fn("Format (json/csv/hex): ").strip()
            if not path.exists():
                print_fn(f"Input file not found: {path}")
                continue
            try:
                _, _, last_summary = _run_single(path, fmt)
                code = run(path, fmt)
                if code != 0:
                    print_fn("Analysis failed.")
            except Exception as exc:
                print_fn(f"Analysis failed: {exc}")

        elif choice == "2":
            base_path = Path(input_fn("Base file path: ").strip())
            base_fmt = input_fn("Base format (json/csv/hex): ").strip()
            cmp_path = Path(input_fn("Compare file path: ").strip())
            cmp_fmt = input_fn("Compare format (json/csv/hex): ").strip()
            if not base_path.exists() or not cmp_path.exists():
                print_fn("One or more files do not exist")
                continue
            code = run(base_path, base_fmt, compare_path=cmp_path, compare_format=cmp_fmt)
            if code != 0:
                print_fn("Comparison failed.")
            else:
                _, _, last_summary = _run_single(base_path, base_fmt)

        elif choice == "3":
            if not last_summary:
                print_fn("No summary available yet. Run analysis first.")
            else:
                print_fn(
                    f"Latest summary: records={last_summary['total_records']} "
                    f"warnings={last_summary['records_with_warnings']} "
                    f"errors={last_summary['records_with_errors']} "
                    f"anomalies={last_summary['anomalies_detected']}"
                )

        elif choice == "4":
            print_fn("Exiting interactive mode.")
            return 0
        else:
            print_fn("Unknown option. Choose 1-4.")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CMIS Data Analysis & Diagnostics Tool")
    parser.add_argument("--input", help="Path to primary input data file")
    parser.add_argument("--format", choices=["json", "csv", "hex"], help="Primary input format")
    parser.add_argument("--compare", help="Optional path to compare dataset")
    parser.add_argument(
        "--compare-format",
        choices=["json", "csv", "hex"],
        help="Optional format override for compare dataset",
    )
    parser.add_argument("--batch", help="Folder path for batch processing")
    parser.add_argument("--interactive", action="store_true", help="Run menu-driven interactive mode")
    parser.add_argument("--output-json", help="Optional path to save JSON report")
    parser.add_argument("--export-csv", help="Optional path to save CSV report")
    parser.add_argument("--only-errors", action="store_true", help="Show/export only records with errors")
    parser.add_argument("--only-warnings", action="store_true", help="Show/export only records with warnings")
    parser.add_argument("--only-anomalies", action="store_true", help="Show/export only records with anomalies")
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.interactive:
        return run_interactive()

    if args.batch:
        return run_batch(Path(args.batch))

    if not args.input or not args.format:
        print("--input and --format are required unless using --batch or --interactive", file=sys.stderr)
        return 1

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    compare_path = Path(args.compare) if args.compare else None
    output_json = Path(args.output_json) if args.output_json else None
    export_csv = Path(args.export_csv) if args.export_csv else None

    return run(
        input_path=input_path,
        input_format=args.format,
        output_json=output_json,
        compare_path=compare_path,
        compare_format=args.compare_format,
        export_csv=export_csv,
        only_errors=args.only_errors,
        only_warnings=args.only_warnings,
        only_anomalies=args.only_anomalies,
    )


if __name__ == "__main__":
    raise SystemExit(main())
