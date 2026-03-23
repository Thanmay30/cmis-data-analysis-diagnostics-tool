# CMIS Data Analysis & Diagnostics Tool

CLI tool for engineers to parse, validate, compare, and diagnose CMIS-like device telemetry across JSON, CSV, and raw text/hex-style inputs.

## What problem it solves

Engineers often receive low-level data in mixed formats while debugging module behavior. This tool normalizes records, flags issues, compares snapshots, and supports batch workflows for faster troubleshooting.

## Run

```bash
cd cmis_tool
python app.py --input sample_data/sample_valid.json --format json
python app.py --input sample_data/sample_valid.json --format json --compare sample_data/sample_compare.json
python app.py --batch sample_data
python app.py --interactive
python app.py --input sample_data/sample_invalid.json --format json --only-errors --export-csv errors.csv
```

## Tests

```bash
cd cmis_tool
python -m pytest tests -q
```
