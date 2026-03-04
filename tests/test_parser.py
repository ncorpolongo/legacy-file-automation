from pathlib import Path
from src.parser import parse_file, DL_STRICT

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

FILE_A = DATA_DIR / "mock_daily_file_v2.txt"
FILE_B = DATA_DIR / "mock_daily_file_v2_test_copy.txt"


def test_file_a_parses_cleanly():
    records, errors = parse_file(str(FILE_A))
    assert len(errors) == 0, f"Expected 0 errors, got {len(errors)}: {errors[:1]}"
    assert len(records) == 12, f"Expected 12 records, got {len(records)}"


def test_file_b_parses_cleanly():
    records, errors = parse_file(str(FILE_B))
    assert len(errors) == 0, f"Expected 0 errors, got {len(errors)}: {errors[:1]}"
    assert len(records) == 12, f"Expected 12 records, got {len(records)}"


def test_required_fields_present_and_nonempty():
    records, errors = parse_file(str(FILE_A))
    assert len(errors) == 0

    required = [
        "last_name", "first_name", "address1", "city", "state", "zip",
        "dob_raw", "gender", "driver_license",
        "case_number", "branch", "municipality",
        "offense_date", "supervision_end_date",
        "charge_code", "sentence_type", "course_length",
        "tail_id"
    ]

    for rec in records:
        for key in required:
            assert key in rec, f"Missing key {key} in record line {rec.get('line_number')}"
            assert rec[key] not in ("", None), f"Empty {key} in record line {rec.get('line_number')}"


def test_driver_license_strict_format():
    records, errors = parse_file(str(FILE_A))
    assert len(errors) == 0

    for rec in records:
        dl = rec["driver_license"]
        assert DL_STRICT.match(dl), f"DL failed strict format: {dl} (line {rec.get('line_number')})"


def test_dates_are_iso_format():
    records, errors = parse_file(str(FILE_A))
    assert len(errors) == 0

    for rec in records:
        od = rec["offense_date"]
        sd = rec["supervision_end_date"]
        # very lightweight ISO check
        assert len(od) == 10 and od[4] == "-" and od[7] == "-", f"Bad offense_date: {od}"
        assert len(sd) == 10 and sd[4] == "-" and sd[7] == "-", f"Bad supervision_end_date: {sd}"


def test_charge_code_contains_wjsup_somewhere():
    records, errors = parse_file(str(FILE_A))
    assert len(errors) == 0

    # at least one record should have WJSUP if your mock data uses it
    assert any(rec["charge_code"] == "WJSUP" for rec in records), "Expected at least one WJSUP charge_code"