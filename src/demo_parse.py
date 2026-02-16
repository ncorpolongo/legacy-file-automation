from parser import parse_file

if __name__ == "__main__":
    records, errors = parse_file("data/0212026 (mock dailfy file).txt")

    print(f"Records: {len(records)}")
    print(f"Errors: {len(errors)}")

    for r in records:
        print("\n--- RECORD ---")
        print(r)

    if errors:
        print("\n--- ERRORS ---")
        for e in errors:
            print(e)
