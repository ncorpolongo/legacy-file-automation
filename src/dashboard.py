from pathlib import Path
import sqlite3
import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "output" / "legacy_file_automation.db"


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)

def insert_class(
    course_section: str,
    class_date: str,
    class_time: str,
    campus: str,
    room: str,
    capacity: int,
    notes: str
):
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO class_schedule
            (course_section, class_date, class_time, campus, room, capacity, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (course_section, class_date, class_time, campus, room, capacity, notes)
        )
        conn.commit()
    finally:
        conn.close()


def load_classes() -> pd.DataFrame:
    conn = get_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM class_schedule ORDER BY class_date", conn)
        return df
    finally:
        conn.close()

def update_class(
    class_id: int,
    course_section: str,
    class_date: str,
    class_time: str,
    campus: str,
    room: str,
    capacity: int,
    notes: str
):
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE class_schedule
            SET course_section = ?,
                class_date = ?,
                class_time = ?,
                campus = ?,
                room = ?,
                capacity = ?,
                notes = ?
            WHERE class_id = ?
            """,
            (course_section, class_date, class_time, campus, room, capacity, notes, class_id)
        )
        conn.commit()
    finally:
        conn.close()


def delete_class(class_id: int):
    conn = get_connection()
    try:
        result = conn.execute(
            "SELECT COUNT(*) FROM case_assignments WHERE class_id = ?",
            (class_id,)
        ).fetchone()[0]

        if result > 0:
            return False

        conn.execute(
            "DELETE FROM class_schedule WHERE class_id = ?",
            (class_id,)
        )
        conn.commit()
        return True
    finally:
        conn.close()

def load_classes_with_enrollment() -> pd.DataFrame:
    conn = get_connection()
    try:
        query = """
            SELECT
                cs.class_id,
                cs.course_section,
                cs.class_date,
                cs.class_time,
                cs.campus,
                cs.room,
                cs.capacity,
                COUNT(ca.assignment_id) AS current_enrollment,
                cs.notes
            FROM class_schedule cs
            LEFT JOIN case_assignments ca
                ON cs.class_id = ca.class_id
            GROUP BY
                cs.class_id,
                cs.course_section,
                cs.class_date,
                cs.class_time,
                cs.campus,
                cs.room,
                cs.capacity,
                cs.notes
            ORDER BY cs.class_date
        """
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()


def load_case_assignments(case_number: str) -> pd.DataFrame:
    conn = get_connection()
    try:
        query = """
            SELECT
                ca.assignment_id,
                cs.class_id,
                cs.course_section,
                cs.class_date,
                cs.class_time,
                cs.campus,
                cs.room
            FROM case_assignments ca
            JOIN class_schedule cs
                ON ca.class_id = cs.class_id
            WHERE ca.case_number = ?
            ORDER BY cs.class_date
        """
        return pd.read_sql_query(query, conn, params=(case_number,))
    finally:
        conn.close()

def assign_case_to_class(case_number: str, class_id: int) -> tuple[bool, str]:
    conn = get_connection()
    try:
        # prevent duplicate assignment
        existing = conn.execute(
            """
            SELECT COUNT(*)
            FROM case_assignments
            WHERE case_number = ? AND class_id = ?
            """,
            (case_number, class_id)
        ).fetchone()[0]

        if existing > 0:
            return False, "This case is already assigned to that class."

        # check capacity
        capacity_row = conn.execute(
            "SELECT capacity FROM class_schedule WHERE class_id = ?",
            (class_id,)
        ).fetchone()

        if capacity_row is None:
            return False, "Class not found."

        capacity = capacity_row[0]

        current_enrollment = conn.execute(
            """
            SELECT COUNT(*)
            FROM case_assignments
            WHERE class_id = ?
            """,
            (class_id,)
        ).fetchone()[0]

        if capacity is not None and current_enrollment >= capacity:
            return False, "Class is at maximum capacity."

        conn.execute(
            """
            INSERT INTO case_assignments (case_number, class_id)
            VALUES (?, ?)
            """,
            (case_number, class_id)
        )
        conn.commit()
        return True, "Case assigned to class successfully."
    finally:
        conn.close()


def remove_case_assignment(assignment_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "DELETE FROM case_assignments WHERE assignment_id = ?",
            (assignment_id,)
        )
        conn.commit()
    finally:
        conn.close()


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
        st.divider()
        st.write("### Class Assignments")

        assigned_df = load_case_assignments(selected_case["case_number"])
        if not assigned_df.empty:
            st.write("Currently Assigned Classes")
            st.dataframe(assigned_df, use_container_width=True, hide_index=True)

            assignment_options = assigned_df.copy()
            assignment_options["label"] = (
                assignment_options["course_section"] + " | " +
                assignment_options["class_date"] + " | " +
                assignment_options["class_time"] + " | " +
                assignment_options["campus"] + " | Room " +
                assignment_options["room"]
            )

            selected_assignment_label = st.selectbox(
                "Select Assigned Class to Remove",
                assignment_options["label"],
                key=f"remove_assignment_{selected_case['case_number']}"
            )

            selected_assignment_id = int(
                assignment_options[
                    assignment_options["label"] == selected_assignment_label
                ]["assignment_id"].iloc[0]
            )

            if st.button("Remove Selected Class Assignment", key=f"remove_btn_{selected_case['case_number']}"):
                remove_case_assignment(selected_assignment_id)
                st.success("Class assignment removed.")
                st.rerun()
        else:
            st.info("No classes currently assigned to this case.")

        st.write("### Add Class Assignment")

        classes_df = load_classes_with_enrollment()

        if not classes_df.empty:
            available_classes = classes_df[
                classes_df["current_enrollment"] < classes_df["capacity"]
            ].copy()

            if not available_classes.empty:
                available_classes["label"] = (
                    available_classes["class_id"].astype(str) + " | " +
                    available_classes["course_section"] + " | " +
                    available_classes["class_date"] + " | " +
                    available_classes["class_time"] + " | " +
                    available_classes["campus"] + " | Room " +
                    available_classes["room"] + " | " +
                    available_classes["current_enrollment"].astype(str) + "/" +
                    available_classes["capacity"].astype(str)
                )

                selected_class_label = st.selectbox(
                    "Select Class to Add",
                    available_classes["label"],
                    key=f"add_class_{selected_case['case_number']}"
                )

                selected_class_id = int(
                    available_classes[
                        available_classes["label"] == selected_class_label
                    ]["class_id"].iloc[0]
                )

                if st.button("Add Selected Class", key=f"add_btn_{selected_case['case_number']}"):
                    success, message = assign_case_to_class(
                        selected_case["case_number"],
                        selected_class_id
                    )

                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            else:
                st.warning("No classes currently have available capacity.")
        else:
            st.info("No scheduled classes available.")
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

    st.divider()
    st.header("📅 Class Scheduling")

    with st.form("create_class_form"):

        course_options = [
            "DDC-4 Internet", "DDC-4", "DDC-4 Spanish",
            "DDC-8", "DDC-8 Spanish",
            "DDC-ADD", "LVIP", "Alive at 25",
            "SAM", "BCM-J", "BCM-A",
            "Family Parenting Internet",
            "Family Parenting", "Family Parenting Spanish"
        ]

        course_section = st.selectbox("Course Section", course_options)

        class_date = st.date_input("Class Date")
        class_time = st.text_input("Class Time (e.g., 6:00 PM - 10:00 PM)")

        campus = st.text_input("Campus")
        room = st.text_input("Room")

        capacity = st.number_input("Capacity", min_value=1, max_value=100, value=20)

        notes = st.text_area("Notes")

        submitted = st.form_submit_button("Create Class")

        if submitted:
            insert_class(
                course_section,
                str(class_date),
                class_time,
                campus,
                room,
                capacity,
                notes
            )
            st.success("Class created successfully!")

    st.subheader("✏️ Edit Class")

    classes_df = load_classes()

    if not classes_df.empty:
        class_options = classes_df["class_id"].tolist()

        selected_class_id = st.selectbox("Select Class ID to Edit", class_options)

        selected_class = classes_df[classes_df["class_id"] == selected_class_id].iloc[0]

        with st.form("edit_class_form"):
            course_section = st.text_input("Course Section", value=selected_class["course_section"])
            class_date = st.date_input("Class Date", value=pd.to_datetime(selected_class["class_date"]))
            class_time = st.text_input("Class Time", value=selected_class["class_time"])
            campus = st.text_input("Campus", value=selected_class["campus"])
            room = st.text_input("Room", value=selected_class["room"])
            capacity = st.number_input(
                "Capacity",
                value=int(selected_class["capacity"]) if pd.notna(selected_class["capacity"]) else 20
            )
            notes = st.text_area(
                "Notes",
                value="" if pd.isna(selected_class["notes"]) else selected_class["notes"]
            )

            submitted = st.form_submit_button("Update Class")

            if submitted:
                update_class(
                    selected_class_id,
                    course_section,
                    str(class_date),
                    class_time,
                    campus,
                    room,
                    capacity,
                    notes
                )
                st.success("Class updated successfully!")
                st.rerun()


    st.subheader("🗑️ Delete Class")

    classes_df = load_classes_with_enrollment()

    if not classes_df.empty:
        class_display = classes_df.copy()
        class_display["label"] = (
            class_display["class_id"].astype(str) + " | " +
            class_display["course_section"] + " | " +
            class_display["class_date"] + " | " +
            class_display["class_time"] + " | " +
            class_display["campus"]
        )

        selected_delete_label = st.selectbox(
            "Select Class to Delete",
            class_display["label"],
            key="delete_class_select"
        )

        selected_delete_id = int(
            class_display[
                class_display["label"] == selected_delete_label
            ]["class_id"].iloc[0]
        )

        confirm_delete = st.checkbox("Confirm deletion", key="confirm_delete_class")

        if st.button("Delete Class", key="delete_class_button"):
            if not confirm_delete:
                st.warning("Please confirm deletion first.")
            else:
                success = delete_class(selected_delete_id)

                if success:
                    st.success("Class deleted successfully!")
                    st.rerun()
                else:
                    st.error("Cannot delete class — people are assigned to it.")
    else:
        st.info("No classes available to delete.")

    st.subheader("Scheduled Classes")

    classes_df = load_classes()

    if not classes_df.empty:
        st.dataframe(classes_df, use_container_width=True, hide_index=True)
    else:
        st.info("No classes scheduled yet.")

if __name__ == "__main__":
    main()



