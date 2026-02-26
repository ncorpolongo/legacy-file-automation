from pathlib import Path
from parser import parse_file, export_records_to_csv, export_errors_to_csv

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "mock_daily_file_v2.txt"
RECORDS_OUT = BASE_DIR / "output" / "parsed_records.csv"
ERRORS_OUT = BASE_DIR / "output" / "parsing_errors.csv"

def main():
    records, errors = parse_file(INPUT_FILE)

    export_records_to_csv(records, RECORDS_OUT)
    export_errors_to_csv(errors, ERRORS_OUT)

    print(f"Parsed {len(records)} records")
    print(f"Found {len(errors)} errors")

if __name__ == "__main__":
    main()

