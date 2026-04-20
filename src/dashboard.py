from pathlib import Path
import sqlite3
import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "output" / "legacy_file_automation.db"


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def update_case_details(
    case_number: str,
    phone: str,
    email: str,
    notes: str,
    reporting_status: str
) -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE cases
            SET phone = ?,
                email = ?,
                notes = ?,
                reporting_status = ?
            WHERE case_number = ?
            """,
            (phone, email, notes, reporting_status, case_number)
        )
        conn.commit()
    finally:
        conn.close()


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
                line_number,
                phone,
                email,
                notes,
                reporting_status
            FROM cases
            ORDER BY case_number
        """
        df = pd.read_sql_query(query, conn)
        df["supervision_end_date"] = pd.to_datetime(df["supervision_end_date"])
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

    
    use_supervision_filter = st.sidebar.checkbox("Filter by Supervision End Date", value=False)

    max_date = df["supervision_end_date"].max().date()

    supervision_end_filter = st.sidebar.date_input(
        "Supervision End Date",
        value=max_date,
        disabled=not use_supervision_filter
    )

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
    
    if use_supervision_filter:
        filtered_df = filtered_df[
            filtered_df["supervision_end_date"] == pd.to_datetime(supervision_end_filter)
        ]
    # --- Filtered summary ---
    st.divider()
    st.subheader("Case Lookup")

    search_case = st.text_input("Search by Case Number")
    search_name = st.text_input("Search by Last Name")

    selected_case = None
    results = None

    if search_case:
        results = df[df["case_number"] == search_case]

    elif search_name:
        results = df[df["last_name"].str.contains(search_name, case=False, na=False)]

    if results is not None and not results.empty:
        if len(results) == 1:
            selected_case = results.iloc[0]
        else:
            st.write("Multiple matching records found:")
            display_cols = ["case_number", "last_name", "first_name", "city", "state"]
            st.dataframe(results[display_cols], use_container_width=True, hide_index=True)
            selected_case = results.iloc[0]

    if selected_case is not None:
        st.success(f"Selected case: {selected_case['case_number']}")

        st.write("### Case Details")

        detail_cols_1 = st.columns(2)
        with detail_cols_1[0]:
            st.write(f"**Last Name:** {selected_case['last_name']}")
            st.write(f"**First Name:** {selected_case['first_name']}")
            st.write(f"**City:** {selected_case['city']}")
            st.write(f"**State:** {selected_case['state']}")
            st.write(f"**ZIP:** {selected_case['zip']}")

        with detail_cols_1[1]:
            st.write(f"**Case Number:** {selected_case['case_number']}")
            st.write(f"**Charge Code:** {selected_case['charge_code']}")
            st.write(f"**Sentence Type:** {selected_case['sentence_type']}")
            st.write(f"**Course Length:** {selected_case['course_length']}")
            st.write(f"**Supervision End Date:** {selected_case['supervision_end_date']}")

        st.write("**Address 1:**", selected_case["address1"])
        st.write("**Address 2:**", selected_case["address2"])

        st.divider()
        st.write("### Editable Case Information")

        with st.form(key=f"case_form_{selected_case['case_number']}"):
            phone = st.text_input(
                "Phone Number",
                value="" if pd.isna(selected_case["phone"]) else str(selected_case["phone"])
            )

            email = st.text_input(
                "Email Address",
                value="" if pd.isna(selected_case["email"]) else str(selected_case["email"])
            )

            reporting_options = ["", "N", "I", "C", "W"]
            current_status = "" if pd.isna(selected_case["reporting_status"]) else str(selected_case["reporting_status"])
            if current_status not in reporting_options:
                current_status = ""

            reporting_status = st.selectbox(
                "Reporting Status",
                reporting_options,
                index=reporting_options.index(current_status)
            )

            notes = st.text_area(
                "Notes",
                value="" if pd.isna(selected_case["notes"]) else str(selected_case["notes"]),
                height=150
            )

            submitted = st.form_submit_button("Save Case Updates")

            if submitted:
                update_case_details(
                    case_number=selected_case["case_number"],
                    phone=phone,
                    email=email,
                    notes=notes,
                    reporting_status=reporting_status
                )
                st.success("Case updated successfully. Refresh or rerun the search to see saved values.")
    
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
