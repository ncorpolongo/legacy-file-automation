import sqlite3
from pathlib import Path


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


def main() -> None:
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        return

    conn = get_connection()

    try:
        print_total_records(conn)
        print_sample_rows(conn)
        print_charge_code_summary(conn)
        print_course_length_summary(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()