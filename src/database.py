import sqlite3
from pathlib import Path
from typing import Dict, List


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "output" / "legacy_file_automation.db"


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """
    Create and return a SQLite connection.
    """
    return sqlite3.connect(db_path)


def create_cases_table(conn: sqlite3.Connection) -> None:
    """
    Create the main cases table if it does not already exist.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            case_number TEXT PRIMARY KEY,
            last_name TEXT,
            first_name TEXT,
            address1 TEXT,
            address2 TEXT,
            city TEXT,
            state TEXT,
            zip TEXT,
            dob_raw TEXT,
            gender TEXT,
            driver_license TEXT,
            branch TEXT,
            municipality TEXT,
            offense_date TEXT,
            supervision_end_date TEXT,
            charge_code TEXT,
            sentence_type TEXT,
            course_length TEXT,
            tail_id TEXT,
            line_number INTEGER
        )
    """)
    conn.commit()


def insert_records(conn: sqlite3.Connection, records: List[Dict[str, object]]) -> int:
    """
    Insert parsed records into the cases table.

    Uses INSERT OR REPLACE so reruns update the same case_number cleanly.

    Returns:
        Number of records written.
    """
    sql = """
        INSERT OR REPLACE INTO cases (
            case_number,
            last_name,
            first_name,
            address1,
            address2,
            city,
            state,
            zip,
            dob_raw,
            gender,
            driver_license,
            branch,
            municipality,
            offense_date,
            supervision_end_date,
            charge_code,
            sentence_type,
            course_length,
            tail_id,
            line_number
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    rows = []
    for rec in records:
        rows.append((
            rec.get("case_number"),
            rec.get("last_name"),
            rec.get("first_name"),
            rec.get("address1"),
            rec.get("address2"),
            rec.get("city"),
            rec.get("state"),
            rec.get("zip"),
            rec.get("dob_raw"),
            rec.get("gender"),
            rec.get("driver_license"),
            rec.get("branch"),
            rec.get("municipality"),
            rec.get("offense_date"),
            rec.get("supervision_end_date"),
            rec.get("charge_code"),
            rec.get("sentence_type"),
            rec.get("course_length"),
            rec.get("tail_id"),
            rec.get("line_number"),
        ))

    conn.executemany(sql, rows)
    conn.commit()
    return len(rows)