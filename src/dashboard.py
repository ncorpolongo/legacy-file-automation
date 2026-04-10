from pathlib import Path
import sqlite3
import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "output" / "legacy_file_automation.db"


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def load_data() -> pd.DataFrame:
    conn = get_connection()
    try:
        query = """
            SELECT
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
            FROM cases
            ORDER BY case_number
        """
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()


def main():
    st.set_page_config(page_title="Legacy File Automation Dashboard", layout="wide")

    st.title("Legacy File Automation Dashboard")
    st.write("Version 1: SQLite-backed record browser and summary view")

    if not DB_PATH.exists():
        st.error(f"Database not found: {DB_PATH}")
        st.stop()

    df = load_data()

    if df.empty:
        st.warning("No records found in the database.")
        st.stop()

    # --- Top summary metrics ---
    total_records = len(df)
    unique_charge_codes = df["charge_code"].nunique()
    unique_course_lengths = df["course_length"].nunique()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Records", total_records)
    col2.metric("Unique Charge Codes", unique_charge_codes)
    col3.metric("Unique Course Lengths", unique_course_lengths)

    st.divider()

    # --- Sidebar filters ---
    st.sidebar.header("Filters")

    last_name_filter = st.sidebar.text_input("Last Name Contains")
    city_filter = st.sidebar.text_input("City Contains")

    charge_options = ["All"] + sorted(df["charge_code"].dropna().unique().tolist())
    charge_filter = st.sidebar.selectbox("Charge Code", charge_options)

    course_options = ["All"] + sorted(df["course_length"].dropna().unique().tolist())
    course_filter = st.sidebar.selectbox("Course Length", course_options)

    state_options = ["All"] + sorted(df["state"].dropna().unique().tolist())
    state_filter = st.sidebar.selectbox("State", state_options)

    # --- Apply filters ---
    filtered_df = df.copy()

    if last_name_filter:
        filtered_df = filtered_df[
            filtered_df["last_name"].str.contains(last_name_filter, case=False, na=False)
        ]

    if city_filter:
        filtered_df = filtered_df[
            filtered_df["city"].str.contains(city_filter, case=False, na=False)
        ]

    if charge_filter != "All":
        filtered_df = filtered_df[filtered_df["charge_code"] == charge_filter]

    if course_filter != "All":
        filtered_df = filtered_df[filtered_df["course_length"] == course_filter]

    if state_filter != "All":
        filtered_df = filtered_df[filtered_df["state"] == state_filter]

    # --- Filtered summary ---
    st.subheader("Filtered Results")
    st.write(f"Showing {len(filtered_df)} record(s)")

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # --- Summary tables ---
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Count by Charge Code")
        charge_summary = (
            filtered_df.groupby("charge_code")
            .size()
            .reset_index(name="count")
            .sort_values(by=["count", "charge_code"], ascending=[False, True])
        )
        st.dataframe(charge_summary, use_container_width=True, hide_index=True)

    with right_col:
        st.subheader("Count by Course Length")
        course_summary = (
            filtered_df.groupby("course_length")
            .size()
            .reset_index(name="count")
            .sort_values(by="course_length")
        )
        st.dataframe(course_summary, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
