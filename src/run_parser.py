from pathlib import Path
import argparse

from parser import parse_file, export_records_to_csv, export_errors_to_csv
from database import (
    get_connection,
    create_cases_table,
    insert_records,
    add_missing_columns,
    create_class_schedule_table,
    create_case_assignments_table,
)

BASE_DIR = Path(__file__).resolve().parent.parent

DEFAULT_INPUT = BASE_DIR / "data" / "mock_daily_file_v2.txt"
RECORDS_OUT = BASE_DIR / "output" / "parsed_records.csv"
ERRORS_OUT = BASE_DIR / "output" / "parsing_errors.csv"


def main():
    parser = argparse.ArgumentParser(description="Run the legacy file parser")
    parser.add_argument(
        "--input",
        type=str,
        default=str(DEFAULT_INPUT),
        help="Path to input daily file"
    )

    args = parser.parse_args()
    input_file = Path(args.input)

    # Ensure output folder exists
    (BASE_DIR / "output").mkdir(exist_ok=True)

    # Parse file
    records, errors = parse_file(str(input_file))

    # Export CSV outputs
    export_records_to_csv(records, str(RECORDS_OUT))
    export_errors_to_csv(errors, str(ERRORS_OUT))

    # Write records to SQLite
    conn = get_connection()
    create_cases_table(conn)
    add_missing_columns(conn)
    create_class_schedule_table(conn)
    create_case_assignments_table(conn)
    inserted = insert_records(conn, records)
    conn.close()

    print(f"Input file: {input_file}")
    print(f"Parsed {len(records)} records")
    print(f"Found {len(errors)} errors")
    print(f"Wrote {inserted} records to SQLite database")


if __name__ == "__main__":
    main()

