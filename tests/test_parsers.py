from pathlib import Path

from parser.csv_parser import parse_csv_file
from parser.hex_parser import parse_hex_file
from parser.json_parser import parse_json_file


SAMPLE_DIR = Path(__file__).resolve().parents[1] / "sample_data"


def test_json_parser_valid():
    records, errors = parse_json_file(SAMPLE_DIR / "sample_valid.json")
    assert len(records) == 3
    assert errors == []


def test_csv_parser_valid():
    records, errors = parse_csv_file(SAMPLE_DIR / "sample_valid.csv")
    assert len(records) == 3
    assert errors == []


def test_hex_parser_valid_and_malformed_tokens():
    records, errors = parse_hex_file(SAMPLE_DIR / "sample_valid.hex")
    assert len(records) == 3
    assert errors == []

    _, malformed_errors = parse_hex_file(SAMPLE_DIR / "sample_malformed.hex")
    assert malformed_errors
