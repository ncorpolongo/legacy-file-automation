import sqlite3
from pathlib import Path
import argparse


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "output" / "legacy_file_automation.db"


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def print_total_records(conn: sqlite3.Connection) -> None:
    cursor = conn.execute("SELECT COUNT(*) FROM cases")
    total = cursor.fetchone()[0]
    print(f"Total records in database: {total}")


def print_sample_rows(conn: sqlite3.Connection, limit: int = 5) -> None:
    print(f"\nSample rows (limit {limit}):")
    cursor = conn.execute("""
        SELECT
            case_number,
            last_name,
            first_name,
            charge_code,
            sentence_type,
            course_length,
            offense_date,
            supervision_end_date
        FROM cases
        ORDER BY case_number
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    for row in rows:
        print(row)


def print_charge_code_summary(conn: sqlite3.Connection) -> None:
    print("\nRecords by charge_code:")
    cursor = conn.execute("""
        SELECT charge_code, COUNT(*)
        FROM cases
        GROUP BY charge_code
        ORDER BY COUNT(*) DESC, charge_code
    """)

    rows = cursor.fetchall()
    for charge_code, count in rows:
        print(f"{charge_code}: {count}")


def print_course_length_summary(conn: sqlite3.Connection) -> None:
    print("\nRecords by course_length:")
    cursor = conn.execute("""
        SELECT course_length, COUNT(*)
        FROM cases
        GROUP BY course_length
        ORDER BY course_length
    """)

    rows = cursor.fetchall()
    for course_length, count in rows:
        print(f"{course_length}: {count}")


def query_by_case(conn: sqlite3.Connection, case_number: str) -> None:
    print(f"\nQuery by case_number: {case_number}")
    cursor = conn.execute("""
        SELECT
            case_number,
            last_name,
            first_name,
            city,
            state,
            branch,
            municipality,
            offense_date,
            supervision_end_date,
            charge_code,
            sentence_type,
            course_length
        FROM cases
        WHERE case_number = ?
    """, (case_number,))

    rows = cursor.fetchall()
    if not rows:
        print("No matching case found.")
        return

    for row in rows:
        print(row)


def query_by_charge(conn: sqlite3.Connection, charge_code: str) -> None:
    print(f"\nQuery by charge_code: {charge_code}")
    cursor = conn.execute("""
        SELECT
            case_number,
            last_name,
            first_name,
            charge_code,
            sentence_type,
            course_length,
            offense_date,
            supervision_end_date
        FROM cases
        WHERE charge_code = ?
        ORDER BY case_number
    """, (charge_code,))

    rows = cursor.fetchall()
    if not rows:
        print("No matching charge_code found.")
        return

    for row in rows:
        print(row)


def query_by_course_length(conn: sqlite3.Connection, course_length: str) -> None:
    print(f"\nQuery by course_length: {course_length}")
    cursor = conn.execute("""
        SELECT
            case_number,
            last_name,
            first_name,
            charge_code,
            sentence_type,
            course_length,
            offense_date,
            supervision_end_date
        FROM cases
        WHERE course_length = ?
        ORDER BY case_number
    """, (course_length,))

    rows = cursor.fetchall()
    if not rows:
        print("No matching course_length found.")
        return

    for row in rows:
        print(row)


def query_by_last_name(conn: sqlite3.Connection, last_name: str) -> None:
    print(f"\nQuery by last_name: {last_name}")

    cursor = conn.execute("""
        SELECT
            case_number,
            last_name,
            first_name,
            city,
            state,
            charge_code,
            sentence_type,
            course_length,
            offense_date,
            supervision_end_date
        FROM cases
        WHERE UPPER(last_name) = UPPER(?)
        ORDER BY case_number
    """, (last_name,))

    rows = cursor.fetchall()
    if not rows:
        print("No matching last_name found.")
        return

    for row in rows:
        print(row)



def main() -> None:
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        return

    parser = argparse.ArgumentParser(description="Query the legacy file automation SQLite database")
    parser.add_argument("--case", type=str, help="Query a specific case_number")
    parser.add_argument("--charge", type=str, help="Query by charge_code")
    parser.add_argument("--course_length", type=str, help="Query by course_length")
    parser.add_argument("--last_name", type=str, help="Query by last_name")
    args = parser.parse_args()

    conn = get_connection()

    try:
        if args.case:
            query_by_case(conn, args.case)
        elif args.charge:
            query_by_charge(conn, args.charge)
        elif args.course_length:
            query_by_course_length(conn, args.course_length)
        elif args.last_name:
            query_by_last_name(conn, args.last_name)
        else:
            print_total_records(conn)
            print_sample_rows(conn)
            print_charge_code_summary(conn)
            print_course_length_summary(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()