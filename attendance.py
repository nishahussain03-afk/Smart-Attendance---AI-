from datetime import datetime

from config import *
from database import *

# ============================================================
# ATTENDANCE FUNCTIONS
# ============================================================

def attendance_window_open():

    now = current_time().time()

    return (
        ATTENDANCE_START
        <= now
        <= ATTENDANCE_END
    )


def attendance_window_status():

    now = current_time().time()

    if now < ATTENDANCE_START:

        return "before"

    if now > ATTENDANCE_END:

        return "after"

    return "open"


def get_student(
    roll_no,
    name
):
    """Verify a student against the permanent Supabase students table."""
    wanted_roll = roll_no.strip().upper()
    wanted_name = name.strip().casefold()

    try:
        result = (
            supabase
            .table("students")
            .select("roll_no, name")
            .eq("roll_no", wanted_roll)
            .execute()
        )

        for row in (result.data or []):
            if row["name"].casefold() == wanted_name:
                return row["roll_no"], row["name"]

    except Exception as e:
        st.error(f"Unable to verify student from Supabase: {e}")

    return None


def get_all_students():
    """Return all registered students from Supabase."""
    try:
        result = (
            supabase
            .table("students")
            .select("roll_no, name")
            .order("roll_no")
            .execute()
        )
        return [
            (row["roll_no"], row["name"])
            for row in (result.data or [])
        ]
    except Exception as e:
        st.error(f"Unable to load students from Supabase: {e}")
        return []


def find_student_from_question(
    question
):
    """Find a registered student from a chatbot question."""
    q = question.lower()
    students = get_all_students()

    roll_match = re.search(
        r"\bE25AI\d{3}\b",
        question.upper()
    )

    if roll_match:
        roll_no = roll_match.group(0)
        for student_roll, student_name in students:
            if student_roll.upper() == roll_no.upper():
                return student_roll, student_name
        return None

    for roll_no, name in students:
        if name.lower() in q:
            return roll_no, name

        for part in name.lower().split():
            if len(part) >= 4 and part in q:
                return roll_no, name

    return None


def _attendance_rows_for_date(
    attendance_date,
    subject=SUBJECT
):
    """Read attendance rows for a date from Supabase."""
    try:
        result = (
            supabase
            .table("attendance")
            .select("id, roll_no, attendance_date, subject, status, marked_time")
            .eq("attendance_date", attendance_date)
            .eq("subject", subject)
            .order("roll_no")
            .execute()
        )
        return result.data or []
    except Exception as e:
        st.error(f"Unable to read attendance from Supabase: {e}")
        return []


def _student_name_map():
    return {
        roll_no: name
        for roll_no, name in get_all_students()
    }


def attendance_already_marked(
    roll_no,
    attendance_date,
    subject
):
    rows = _attendance_rows_for_date(
        attendance_date,
        subject
    )

    for row in rows:
        if row["roll_no"] == roll_no:
            return (
                row.get("id"),
                row.get("status")
            )

    return None


def mark_present(
    roll_no,
    attendance_date,
    subject
):
    """Save Present permanently to Supabase."""
    if attendance_already_marked(
        roll_no,
        attendance_date,
        subject
    ):
        return (
            False,
            "Attendance has already been marked for this session."
        )

    try:
        supabase.table("attendance").insert(
            {
                "roll_no": roll_no,
                "attendance_date": attendance_date,
                "subject": subject,
                "status": "Present",
                "marked_time": current_time().isoformat()
            }
        ).execute()

        return True, "Attendance marked successfully."

    except Exception as e:
        error_text = str(e).lower()
        if "23505" in error_text or "duplicate" in error_text:
            return (
                False,
                "Attendance has already been marked for this session."
            )
        return (
            False,
            f"Attendance could not be saved to Supabase: {e}"
        )


def create_absent_records(
    attendance_date,
    subject
):
    """Save Absent records permanently for students who did not mark."""
    students = get_all_students()
    existing_rows = _attendance_rows_for_date(
        attendance_date,
        subject
    )

    existing_rolls = {
        row["roll_no"]
        for row in existing_rows
    }

    missing_rows = [
        {
            "roll_no": roll_no,
            "attendance_date": attendance_date,
            "subject": subject,
            "status": "Absent"
        }
        for roll_no, name in students
        if roll_no not in existing_rolls
    ]

    if not missing_rows:
        return

    try:
        supabase.table("attendance").insert(
            missing_rows
        ).execute()
    except Exception as e:
        st.error(
            f"Unable to save absent records to Supabase: {e}"
        )


def automatic_finalize_attendance():

    attendance_date = today_date()

    if not is_working_day(
        attendance_date
    ):

        return

    if current_time().time() <= ATTENDANCE_END:

        return

    try:
        result = (
            supabase
            .table("session_reports")
            .select("id")
            .eq("attendance_date", attendance_date)
            .eq("subject", SUBJECT)
            .limit(1)
            .execute()
        )
        if result.data:
            return
    except Exception as e:
        st.error(f"Unable to check session report in Supabase: {e}")
        return

    create_absent_records(
        attendance_date,
        SUBJECT
    )

    save_session_report(
        attendance_date,
        SUBJECT
    )


def get_today_records(subject):
    return get_records_for_date(
        today_date(),
        subject
    )


def get_all_attendance():
    """Return all attendance records from Supabase."""
    try:
        result = (
            supabase
            .table("attendance")
            .select("id, roll_no, attendance_date, subject, status, marked_time")
            .order("attendance_date", desc=True)
            .order("roll_no")
            .execute()
        )

        rows = result.data or []
        names = _student_name_map()

        return [
            (
                row["roll_no"],
                names.get(row["roll_no"], "Unknown Student"),
                str(row["attendance_date"]),
                row["subject"],
                row["status"],
                row.get("marked_time", "")
            )
            for row in rows
        ]

    except Exception as e:
        st.error(f"Unable to load attendance from Supabase: {e}")
        return []


def get_records_for_date(
    date_value,
    subject=SUBJECT
):
    rows = _attendance_rows_for_date(
        date_value,
        subject
    )
    names = _student_name_map()

    return [
        (
            row["roll_no"],
            names.get(row["roll_no"], "Unknown Student"),
            row["status"],
            row.get("marked_time", "")
        )
        for row in rows
    ]


def get_student_attendance(roll_no):
    try:
        result = (
            supabase
            .table("attendance")
            .select("status")
            .eq("roll_no", roll_no)
            .execute()
        )

        rows = result.data or []
        total = len(rows)
        present = sum(
            1 for row in rows
            if row.get("status") == "Present"
        )
        absent = sum(
            1 for row in rows
            if row.get("status") == "Absent"
        )

    except Exception as e:
        st.error(
            f"Unable to calculate attendance from Supabase: {e}"
        )
        total = 0
        present = 0
        absent = 0

    percentage = (
        present / total * 100
        if total > 0
        else None
    )

    return total, present, absent, percentage


def get_attendance_summary():

    students = get_all_students()

    summary = []

    for roll_no, name in students:

        total, present, absent, percentage = (
            get_student_attendance(
                roll_no
            )
        )

        if percentage is None:

            attendance_display = "N/A"

            risk = "No Data"

        else:

            attendance_display = round(
                percentage,
                2
            )

            risk = (
                "At Risk"
                if percentage < MIN_ATTENDANCE
                else "Safe"
            )

        summary.append(
            {
                "Roll No": roll_no,
                "Name": name,
                "Total Sessions": total,
                "Present": present,
                "Absent": absent,
                "Attendance %": attendance_display,
                "Risk": risk
            }
        )

    return summary


def get_today_counts(subject):

    records = get_today_records(
        subject
    )

    present = sum(
        1
        for r in records
        if r[2] == "Present"
    )

    absent = sum(
        1
        for r in records
        if r[2] == "Absent"
    )

    return present, absent


def save_session_report(
    attendance_date,
    subject
):

    records = get_records_for_date(
        attendance_date,
        subject
    )

    present = sum(
        1
        for r in records
        if r[2] == "Present"
    )

    absent = sum(
        1
        for r in records
        if r[2] == "Absent"
    )

    if present + absent == 0:
        return

    try:
        result = (
            supabase
            .table("session_reports")
            .select("id")
            .eq("attendance_date", attendance_date)
            .eq("subject", subject)
            .limit(1)
            .execute()
        )

        generated_time = current_time().isoformat()

        payload = {
            "attendance_date": attendance_date,
            "subject": subject,
            "generated_time": generated_time,
            "present_count": present,
            "absent_count": absent,
        }

        if result.data:
            report_id = result.data[0]["id"]
            (
                supabase
                .table("session_reports")
                .update(payload)
                .eq("id", report_id)
                .execute()
            )
        else:
            supabase.table("session_reports").insert(payload).execute()

    except Exception as e:
        st.error(f"Unable to save session report to Supabase: {e}")


def required_future_classes_for_75(
    present,
    total
):

    if total == 0:

        return None

    if present / total * 100 >= MIN_ATTENDANCE:

        return 0

    needed = math.ceil(
        (
            MIN_ATTENDANCE * total / 100
            - present
        )
        /
        (
            1 - MIN_ATTENDANCE / 100
        )
    )

    return max(
        0,
        needed
    )


def maximum_future_absences_at_75(
    present,
    total
):

    if total == 0:

        return None

    maximum = math.floor(
        present / (MIN_ATTENDANCE / 100)
        - total
    )

    return max(
        0,
        maximum
    )
