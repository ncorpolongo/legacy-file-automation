from parser import parse_file, export_records_to_csv, export_errors_to_csv

INPUT_FILE = "data/mock_daily_file_v2.txt"
RECORDS_OUT = "output/parsed_records.csv"
ERRORS_OUT = "output/parsing_errors.csv"

def main():
    records, errors = parse_file(INPUT_FILE)

    export_records_to_csv(records, RECORDS_OUT)
    export_errors_to_csv(errors, ERRORS_OUT)

    print(f"Parsed {len(records)} records")
    print(f"Found {len(errors)} errors")

if __name__ == "__main__":
    main()
