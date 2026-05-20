# CMIS Data Analysis & Diagnostics Tool

A command-line tool for parsing, validating, comparing, and diagnosing CMIS
module telemetry data across multiple input formats.

## My Role

Solo project. I designed the CLI interface, wrote the core parser and
validation logic, built the comparison engine, and wrote the test suite.

## Problem

Engineers working with CMIS module data often receive records in inconsistent
formats — JSON, CSV, or raw hex-style text — from different sources. Manually
comparing snapshots or tracking down validation errors across batches of files
is slow and error-prone. This tool normalizes records into a common structure
and flags issues automatically.

## Features

- Parse device telemetry from JSON, CSV, and raw text/hex inputs
- Validate records against expected field ranges and types
- Compare two snapshots side-by-side and report deltas
- Batch mode: run against a full directory of input files
- Interactive mode for step-by-step inspection
- `--only-errors` flag to suppress clean records from output
- Export validation errors to CSV for downstream analysis

## Tech Stack

| Category | Technology |
|---|---|
| Language | Python 3.11+ |
| CLI | argparse |
| Testing | pytest |
| Input formats | JSON, CSV, raw text/hex |

## Architecture

```text
cmis-data-analysis-diagnostics-tool/
  app.py          CLI entry point and argument parsing
  core/           Validation logic and report generation
  parser/         Format-specific parsers (JSON, CSV, raw text)
  tests/          pytest test suite
  sample_data/    Example input files for testing and demos
  requirements.txt
```

## Getting Started

```bash
git clone https://github.com/Thanmay30/cmis-data-analysis-diagnostics-tool.git
cd cmis-data-analysis-diagnostics-tool
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Example Usage

```bash
# Validate a single JSON file
python app.py --input sample_data/sample_valid.json --format json

# Compare two snapshots
python app.py --input sample_data/sample_valid.json \
              --compare sample_data/sample_compare.json \
              --format json

# Batch validate a directory, export errors only
python app.py --batch sample_data --only-errors --export-csv errors.csv

# Interactive mode
python app.py --interactive
```

## Testing

```bash
python -m pytest tests -q
```

## Known Limitations

- Parser currently handles a defined subset of CMIS fields; extending to new
  field types requires adding a mapping in the relevant parser module
- Raw hex parsing assumes a fixed byte layout; edge cases in non-standard
  layouts may need manual adjustment

## What I Learned

Separating parsing from validation early was the key design decision — each
format needs its own parser, but validation logic operates on a shared record
schema so adding a new input format does not touch the core validation code.
Testing against real sample data files catches edge cases that pure unit tests
miss because the complexity lives in the data, not the logic.

## Future Improvements

- Add YAML input support
- Generate an HTML diff report for snapshot comparisons
- `--watch` mode that re-runs validation when input files change
- Package as a pip-installable CLI tool

## License

MIT
