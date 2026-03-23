from pathlib import Path

from app import run, run_batch, run_interactive


SAMPLE_DIR = Path(__file__).resolve().parents[1] / "sample_data"


def test_run_success_json_with_exports(tmp_path):
    out_path = tmp_path / "report.json"
    csv_path = tmp_path / "report.csv"
    code = run(SAMPLE_DIR / "sample_valid.json", "json", out_path, export_csv=csv_path)
    assert code == 0
    assert out_path.exists()
    assert csv_path.exists()


def test_run_compare_mode(tmp_path):
    out_path = tmp_path / "report_compare.json"
    code = run(
        SAMPLE_DIR / "sample_valid.json",
        "json",
        out_path,
        compare_path=SAMPLE_DIR / "sample_compare.json",
    )
    assert code == 0
    assert out_path.exists()


def test_filter_only_errors(tmp_path):
    csv_path = tmp_path / "errors_only.csv"
    code = run(
        SAMPLE_DIR / "sample_invalid.json",
        "json",
        export_csv=csv_path,
        only_errors=True,
    )
    assert code == 0
    content = csv_path.read_text(encoding="utf-8")
    assert "record_id" in content


def test_batch_mode(tmp_path):
    batch_dir = tmp_path / "batch"
    batch_dir.mkdir()
    (batch_dir / "a.json").write_text((SAMPLE_DIR / "sample_valid.json").read_text(encoding="utf-8"), encoding="utf-8")
    (batch_dir / "b.csv").write_text((SAMPLE_DIR / "sample_valid.csv").read_text(encoding="utf-8"), encoding="utf-8")
    (batch_dir / "c.hex").write_text((SAMPLE_DIR / "sample_valid.hex").read_text(encoding="utf-8"), encoding="utf-8")

    code = run_batch(batch_dir)
    assert code == 0


def test_interactive_mode_basic_exit():
    answers = iter(["4"])
    printed = []

    def fake_input(_prompt: str) -> str:
        return next(answers)

    def fake_print(*args, **kwargs):
        printed.append(" ".join(str(a) for a in args))

    code = run_interactive(input_fn=fake_input, print_fn=fake_print)
    assert code == 0
    assert any("Interactive Menu" in line for line in printed)


def test_run_bad_input_file(tmp_path):
    code = run(tmp_path / "missing.json", "json", None)
    assert code == 1
