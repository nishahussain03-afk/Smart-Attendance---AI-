import streamlit as st
import sqlite3
import re
import math
import os
import requests
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import quote
from apscheduler.schedulers.background import BackgroundScheduler


# ============================================================
# CONFIGURATION
# ============================================================

APP_TITLE = "SmartAttend AI"

DEPARTMENT = "B.Sc Computer Science with AI"
YEAR = "2nd Year"
SHIFT = "Shift 2"

MIN_ATTENDANCE = 75.0

ATTENDANCE_START = time(13, 0)
ATTENDANCE_END = time(13, 15)

ADMIN_PASSWORD = "admin123"

CLASS_MAAM_PHONE = "916381494411"
ADMIN_PHONE = "918428800487"

TIMEZONE = ZoneInfo("Asia/Kolkata")

DB_FILE = "attendance.db"

SUBJECT = "Attendance Session"


# ============================================================
# STUDENT DATA
# ============================================================

STUDENTS = [
    ("E25AI201", "AARTHY V"),
    ("E25AI202", "AFREEN NISHA M"),
    ("E25AI203", "AKSHAYA K"),
    ("E25AI204", "ASENIYA SHINY A"),
    ("E25AI205", "ASWINI S"),
    ("E25AI206", "AYESHA AFROZE M"),
    ("E25AI207", "HARI PRIYA B"),
    ("E25AI208", "BHAVATHARANI T"),
    ("E25AI209", "DEVISREE T"),
    ("E25AI210", "HARINI N"),
    ("E25AI212", "HEMADHARSHINI S"),
    ("E25AI213", "HEMALATHA K"),
    ("E25AI214", "HEMALATHA M"),
    ("E25AI215", "HEMAMALINI S"),
    ("E25AI216", "HUMAIRUL JASHIRA M"),
    ("E25AI217", "JASCINTH RHEMA R"),
    ("E25AI218", "JENITA ROSELIN S"),
    ("E25AI219", "RIYAVALLI K"),
    ("E25AI220", "KAVIYA SHREE V"),
    ("E25AI221", "KEERTHANA P"),
    ("E25AI222", "KEERTHIGA K U"),
    ("E25AI223", "KEERTHIKA M"),
    ("E25AI224", "MADHUMITHA U"),
    ("E25AI225", "MYTHILI K"),
    ("E25AI226", "NANDHINI SRI L V"),
    ("E25AI228", "POOJA SHREE S S"),
    ("E25AI229", "POOJA V"),
    ("E25AI230", "RENUKA DEVI S"),
    ("E25AI231", "SAGI SRUTHI"),
    ("E25AI232", "SANDHIYA R"),
    ("E25AI233", "SHALINI DEVI V"),
    ("E25AI234", "SIBIRAL R"),
    ("E25AI235", "SRUDHYA S"),
    ("E25AI236", "THANSILA BEGAM F"),
    ("E25AI237", "THIRIJA R"),
    ("E25AI238", "VAISHNAVI S"),
    ("E25AI239", "VARALAKSHMI K"),
    ("E25AI240", "YUVASHRI H"),
    ("E25AI241", "DODDI HASINI"),
    ("E25AI242", "RUPA S"),
    ("E25AI243", "MANISHA D"),
    ("E25AI244", "PRIYADARSHINI D"),
    ("E25AI245", "NIVETHITHA D"),
    ("E25AI246", "SNOWFER AMEENA A"),
    ("E25AI247", "LATTIKHASHRI N"),
    ("E25AI248", "PORKODI K"),
    ("E25AI249", "NIKITHA R"),
]


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    return sqlite3.connect(
        DB_FILE,
        check_same_thread=False
    )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            roll_no TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT NOT NULL,
            attendance_date TEXT NOT NULL,
            subject TEXT NOT NULL,
            status TEXT NOT NULL,
            marked_time TEXT NOT NULL,
            UNIQUE(roll_no, attendance_date, subject)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS session_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attendance_date TEXT NOT NULL,
            subject TEXT NOT NULL,
            generated_time TEXT NOT NULL,
            present_count INTEGER NOT NULL,
            absent_count INTEGER NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS holidays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            holiday_date TEXT UNIQUE NOT NULL,
            holiday_name TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS college_calendar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            calendar_date TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL,
            description TEXT DEFAULT '',
            academic_year TEXT NOT NULL
        )
        """
    )

    for roll_no, name in STUDENTS:

        cursor.execute(
            """
            INSERT OR IGNORE INTO students
            (roll_no, name)
            VALUES (?, ?)
            """,
            (roll_no, name)
        )

    conn.commit()

    conn.close()


# ============================================================
# TIME FUNCTIONS
# ============================================================

def current_time():

    return datetime.now(TIMEZONE)


def today_date():

    return current_time().date().isoformat()


def current_day():

    return current_time().strftime("%A")


# ============================================================
# DATE HELPERS
# ============================================================

def format_date(date_value):

    try:

        return datetime.fromisoformat(
            date_value
        ).strftime("%d-%m-%Y")

    except Exception:

        return date_value


def parse_date_from_question(question):

    q = question.lower()

    today = current_time().date()

    if "day after tomorrow" in q:

        return (
            today + timedelta(days=2)
        ).isoformat()

    if "tomorrow" in q:

        return (
            today + timedelta(days=1)
        ).isoformat()

    if "yesterday" in q:

        return (
            today - timedelta(days=1)
        ).isoformat()

    date_patterns = [
        r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b",
        r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b",
        r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+(\d{4}))?\b"
    ]

    for pattern in date_patterns:

        match = re.search(
            pattern,
            question
        )

        if match:

            try:

                groups = match.groups()

                if len(groups) == 3 and groups[1].isalpha():
                    day = int(groups[0])
                    month = datetime.strptime(groups[1], "%B").month
                    year = int(groups[2]) if groups[2] else today.year
                elif len(groups[0]) == 4:
                    year = int(groups[0])
                    month = int(groups[1])
                    day = int(groups[2])
                else:
                    day = int(groups[0])
                    month = int(groups[1])
                    year = int(groups[2])

                return datetime(
                    year,
                    month,
                    day
                ).date().isoformat()

            except ValueError:

                return None

    return None


# ============================================================
# HOLIDAY & COLLEGE CALENDAR MANAGEMENT
# ============================================================

def add_holiday(
    holiday_date,
    holiday_name
):

    conn = get_connection()

    try:

        conn.execute(
            """
            INSERT OR REPLACE INTO holidays
            (
                holiday_date,
                holiday_name
            )
            VALUES (?, ?)
            """,
            (
                holiday_date,
                holiday_name
            )
        )

        conn.commit()

    finally:

        conn.close()


def remove_holiday(holiday_date):

    conn = get_connection()

    try:

        conn.execute(
            """
            DELETE FROM holidays
            WHERE holiday_date = ?
            """,
            (holiday_date,)
        )

        conn.commit()

    finally:

        conn.close()


def get_all_holidays():

    conn = get_connection()

    try:

        holidays = conn.execute(
            """
            SELECT
                holiday_date,
                holiday_name
            FROM holidays
            ORDER BY holiday_date
            """
        ).fetchall()

    finally:

        conn.close()

    return holidays


# ============================================================
# COLLEGE CALENDAR STATUS
# ============================================================

def get_college_calendar_status(
    date_value=None
):

    if date_value is None:

        date_value = today_date()

    date_object = datetime.fromisoformat(
        date_value
    )

    if date_object.weekday() == 5:

        return False, "Saturday - Holiday"

    if date_object.weekday() == 6:

        return False, "Sunday - Holiday"

    conn = get_connection()

    try:

        calendar_day = conn.execute(
            """
            SELECT
                status,
                description
            FROM college_calendar
            WHERE calendar_date = ?
            """,
            (date_value,)
        ).fetchone()

    finally:

        conn.close()

    if calendar_day:

        status = calendar_day[0]

        description = calendar_day[1]

        if status.lower() == "working":

            if description:

                return True, description

            return True, "Working Day"

        else:

            if description:

                return False, description

            return False, "Holiday"

    return True, "Working Day"


# ============================================================
# HOLIDAY CHECK
# ============================================================

def is_holiday(date_value=None):

    if date_value is None:

        date_value = today_date()

    working, reason = (
        get_college_calendar_status(
            date_value
        )
    )

    if not working:

        return True

    conn = get_connection()

    try:

        holiday = conn.execute(
            """
            SELECT holiday_name
            FROM holidays
            WHERE holiday_date = ?
            """,
            (date_value,)
        ).fetchone()

    finally:

        conn.close()

    return holiday is not None


# ============================================================
# WEEKEND CHECK
# ============================================================

def is_weekend(date_value=None):

    if date_value is None:

        date_value = today_date()

    date_object = datetime.fromisoformat(
        date_value
    )

    return date_object.weekday() in (5, 6)


# ============================================================
# WORKING DAY CHECK
# ============================================================

def is_working_day(date_value=None):

    if date_value is None:

        date_value = today_date()

    if is_weekend(date_value):

        return False

    working, reason = (
        get_college_calendar_status(
            date_value
        )
    )

    if not working:

        return False

    conn = get_connection()

    try:

        holiday = conn.execute(
            """
            SELECT holiday_date
            FROM holidays
            WHERE holiday_date = ?
            """,
            (date_value,)
        ).fetchone()

    finally:

        conn.close()

    if holiday:

        return False

    return True


# ============================================================
# NON-WORKING DAY REASON
# ============================================================

def get_non_working_day_reason(
    date_value=None
):

    if date_value is None:

        date_value = today_date()

    date_object = datetime.fromisoformat(
        date_value
    )

    if date_object.weekday() == 5:

        return "Saturday - Holiday"

    if date_object.weekday() == 6:

        return "Sunday - Holiday"

    working, reason = (
        get_college_calendar_status(
            date_value
        )
    )

    if not working:

        return f"Holiday: {reason}"

    conn = get_connection()

    try:

        holiday = conn.execute(
            """
            SELECT holiday_name
            FROM holidays
            WHERE holiday_date = ?
            """,
            (date_value,)
        ).fetchone()

    finally:

        conn.close()

    if holiday:

        return f"Holiday: {holiday[0]}"

    return "Non-working day"


# ============================================================
# ATTENDANCE WINDOW
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


# ============================================================
# STUDENT FUNCTIONS
# ============================================================

def get_student(
    roll_no,
    name
):

    conn = get_connection()

    student = conn.execute(
        """
        SELECT
            roll_no,
            name
        FROM students
        WHERE UPPER(roll_no) = UPPER(?)
        AND UPPER(name) = UPPER(?)
        """,
        (
            roll_no.strip(),
            name.strip()
        )
    ).fetchone()

    conn.close()

    return student


def get_all_students():

    conn = get_connection()

    students = conn.execute(
        """
        SELECT
            roll_no,
            name
        FROM students
        ORDER BY roll_no
        """
    ).fetchall()

    conn.close()

    return students


def find_student_from_question(
    question
):

    q = question.lower()

    conn = get_connection()

    try:

        roll_match = re.search(
            r"\bE25AI\d{3}\b",
            question.upper()
        )

        if roll_match:

            roll_no = roll_match.group(0)

            student = conn.execute(
                """
                SELECT roll_no, name
                FROM students
                WHERE roll_no = ?
                """,
                (roll_no,)
            ).fetchone()

            return student

        for roll_no, name in STUDENTS:

            if name.lower() in q:

                return (
                    roll_no,
                    name
                )

            parts = name.lower().split()

            for part in parts:

                if len(part) >= 4 and part in q:

                    return (
                        roll_no,
                        name
                    )

    finally:

        conn.close()

    return None


# ============================================================
# ATTENDANCE FUNCTIONS
# ============================================================

def attendance_already_marked(
    roll_no,
    attendance_date,
    subject
):

    conn = get_connection()

    record = conn.execute(
        """
        SELECT
            id,
            status
        FROM attendance
        WHERE roll_no = ?
        AND attendance_date = ?
        AND subject = ?
        """,
        (
            roll_no,
            attendance_date,
            subject
        )
    ).fetchone()

    conn.close()

    return record


def mark_present(
    roll_no,
    attendance_date,
    subject
):

    now = current_time()

    conn = get_connection()

    try:

        conn.execute(
            """
            INSERT INTO attendance
            (
                roll_no,
                attendance_date,
                subject,
                status,
                marked_time
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                roll_no,
                attendance_date,
                subject,
                "Present",
                now.strftime("%H:%M:%S")
            )
        )

        conn.commit()

        success = True

        message = (
            "Attendance marked successfully."
        )

    except sqlite3.IntegrityError:

        success = False

        message = (
            "Attendance has already been "
            "marked for this session."
        )

    finally:

        conn.close()

    return success, message


def create_absent_records(
    attendance_date,
    subject
):

    conn = get_connection()

    students = conn.execute(
        """
        SELECT roll_no
        FROM students
        """
    ).fetchall()

    for (roll_no,) in students:

        conn.execute(
            """
            INSERT OR IGNORE INTO attendance
            (
                roll_no,
                attendance_date,
                subject,
                status,
                marked_time
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                roll_no,
                attendance_date,
                subject,
                "Absent",
                "-"
            )
        )

    conn.commit()

    conn.close()


# ============================================================
# AUTOMATIC ATTENDANCE FINALIZATION
# ============================================================

def automatic_finalize_attendance():

    attendance_date = today_date()

    if not is_working_day(
        attendance_date
    ):

        return

    if current_time().time() <= ATTENDANCE_END:

        return

    conn = get_connection()

    try:

        existing_report = conn.execute(
            """
            SELECT id
            FROM session_reports
            WHERE attendance_date = ?
            AND subject = ?
            """,
            (
                attendance_date,
                SUBJECT
            )
        ).fetchone()

    finally:

        conn.close()

    if existing_report:

        return

    create_absent_records(
        attendance_date,
        SUBJECT
    )

    save_session_report(
        attendance_date,
        SUBJECT
    )


# ============================================================
# ATTENDANCE RECORDS
# ============================================================

def get_today_records(subject):

    conn = get_connection()

    records = conn.execute(
        """
        SELECT
            a.roll_no,
            s.name,
            a.status,
            a.marked_time
        FROM attendance a
        JOIN students s
        ON a.roll_no = s.roll_no
        WHERE a.attendance_date = ?
        AND a.subject = ?
        ORDER BY a.roll_no
        """,
        (
            today_date(),
            subject
        )
    ).fetchall()

    conn.close()

    return records


def get_all_attendance():

    conn = get_connection()

    records = conn.execute(
        """
        SELECT
            a.roll_no,
            s.name,
            a.attendance_date,
            a.subject,
            a.status,
            a.marked_time
        FROM attendance a
        JOIN students s
        ON a.roll_no = s.roll_no
        ORDER BY
            a.attendance_date DESC,
            a.roll_no
        """
    ).fetchall()

    conn.close()

    return records


def get_records_for_date(
    date_value,
    subject=SUBJECT
):

    conn = get_connection()

    records = conn.execute(
        """
        SELECT
            a.roll_no,
            s.name,
            a.status,
            a.marked_time
        FROM attendance a
        JOIN students s
        ON a.roll_no = s.roll_no
        WHERE a.attendance_date = ?
        AND a.subject = ?
        ORDER BY a.roll_no
        """,
        (
            date_value,
            subject
        )
    ).fetchall()

    conn.close()

    return records


# ============================================================
# ATTENDANCE ANALYTICS
# ============================================================

def get_student_attendance(roll_no):

    conn = get_connection()

    total = conn.execute(
        """
        SELECT COUNT(*)
        FROM attendance
        WHERE roll_no = ?
        """,
        (roll_no,)
    ).fetchone()[0]

    present = conn.execute(
        """
        SELECT COUNT(*)
        FROM attendance
        WHERE roll_no = ?
        AND status = 'Present'
        """,
        (roll_no,)
    ).fetchone()[0]

    absent = conn.execute(
        """
        SELECT COUNT(*)
        FROM attendance
        WHERE roll_no = ?
        AND status = 'Absent'
        """,
        (roll_no,)
    ).fetchone()[0]

    conn.close()

    if total > 0:

        percentage = (
            present / total * 100
        )

    else:

        percentage = None

    return (
        total,
        present,
        absent,
        percentage
    )


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

    conn = get_connection()

    existing = conn.execute(
        """
        SELECT id
        FROM session_reports
        WHERE attendance_date = ?
        AND subject = ?
        """,
        (
            attendance_date,
            subject
        )
    ).fetchone()

    generated_time = (
        current_time().strftime(
            "%H:%M:%S"
        )
    )

    if existing:

        conn.execute(
            """
            UPDATE session_reports
            SET
                generated_time = ?,
                present_count = ?,
                absent_count = ?
            WHERE id = ?
            """,
            (
                generated_time,
                present,
                absent,
                existing[0]
            )
        )

    else:

        conn.execute(
            """
            INSERT INTO session_reports
            (
                attendance_date,
                subject,
                generated_time,
                present_count,
                absent_count
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                attendance_date,
                subject,
                generated_time,
                present,
                absent
            )
        )

    conn.commit()

    conn.close()


# ============================================================
# ATTENDANCE CALCULATIONS
# ============================================================

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


# ============================================================
# WHATSAPP
# ============================================================

def generate_whatsapp_link(
    phone,
    message
):

    return (
        "https://wa.me/"
        + phone
        + "?text="
        + quote(message)
    )


def generate_daily_report():

    date = today_date()

    records = get_today_records(
        SUBJECT
    )

    present = [
        r
        for r in records
        if r[2] == "Present"
    ]

    absent = [
        r
        for r in records
        if r[2] == "Absent"
    ]

    lines = [
        "SMARTATTEND AI - DAILY ATTENDANCE REPORT",
        "",
        f"Department: {DEPARTMENT}",
        f"Year: {YEAR}",
        f"Shift: {SHIFT}",
        f"Date: {date}",
        "",
        f"Total Students: {len(STUDENTS)}",
        f"Present: {len(present)}",
        f"Absent: {len(absent)}",
        "",
        "ABSENT STUDENTS:"
    ]

    for record in absent:

        lines.append(
            f"{record[0]} - {record[1]}"
        )

    return "\n".join(lines)


# ============================================================
# CALENDAR INFORMATION
# ============================================================

def calendar_answer_for_date(
    date_value
):

    working, reason = (
        get_college_calendar_status(
            date_value
        )
    )

    date_object = datetime.fromisoformat(
        date_value
    )

    day_name = date_object.strftime(
        "%A"
    )

    if working:

        return (
            f"📅 {format_date(date_value)} "
            f"({day_name}) is a working day.\n\n"
            f"Calendar information: {reason}"
        )

    return (
        f"🏖️ {format_date(date_value)} "
        f"({day_name}) is a holiday/non-working day.\n\n"
        f"Reason: {reason}"
    )


# ============================================================
# AI ATTENDANCE ASSISTANT
# ============================================================

def _normalise_text(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9%/\-\s]", " ", text)
    return re.sub(r"\s+", " ", text)


def _date_label(date_value):
    try:
        return datetime.fromisoformat(date_value).strftime("%d-%m-%Y")
    except Exception:
        return date_value


def _records_for_date_with_students(date_value):
    return get_records_for_date(date_value, SUBJECT)


def _present_absent_lists(date_value):
    records = _records_for_date_with_students(date_value)
    present = [r for r in records if r[2] == "Present"]
    absent = [r for r in records if r[2] == "Absent"]
    return records, present, absent


def _format_student_list(title, students):
    if not students:
        return f"{title}\n\nNo students found."
    lines = [title, ""]
    for i, (roll_no, name, *_) in enumerate(students, 1):
        lines.append(f"{i}. {roll_no} — {name}")
    return "\n".join(lines)


def _attendance_date_from_question(question):
    requested = parse_date_from_question(question)
    if requested:
        return requested
    q = _normalise_text(question)
    if "today" in q or "todays" in q:
        return today_date()
    return None


def _student_context_from_question(question, context_student):
    student = find_student_from_question(question)
    if student:
        return student
    q = _normalise_text(question)
    pronouns = {
        "she", "her", "hers", "he", "him", "his", "they", "them",
        "their", "that student", "this student", "that person", "the student"
    }
    if context_student and any(x in q for x in pronouns):
        return context_student
    return None


def _get_class_stats(date_value=None):
    if date_value:
        records = get_records_for_date(date_value, SUBJECT)
        present = sum(1 for r in records if r[2] == "Present")
        absent = sum(1 for r in records if r[2] == "Absent")
        return len(STUDENTS), present, absent, records

    records = get_today_records(SUBJECT)
    present = sum(1 for r in records if r[2] == "Present")
    absent = sum(1 for r in records if r[2] == "Absent")
    return len(STUDENTS), present, absent, records


def _date_attendance_answer(date_value, requested_status=None):
    if not is_working_day(date_value):
        return (
            f"🏖️ **{_date_label(date_value)}** was a non-working day.\n\n"
            f"Reason: **{get_non_working_day_reason(date_value)}**\n\n"
            "No attendance session was scheduled."
        )

    records, present, absent = _present_absent_lists(date_value)

    if requested_status == "absent":
        if not records:
            return (
                f"📅 There are no finalized attendance records for **{_date_label(date_value)}** yet."
            )
        return (
            f"❌ **Absent Students — {_date_label(date_value)}**\n\n"
            f"Total Students: {len(STUDENTS)}\n"
            f"Present: {len(present)}\n"
            f"Absent: {len(absent)}\n\n" +
            ("\n".join(f"{i}. {r[0]} — {r[1]}" for i, r in enumerate(absent, 1))
             if absent else "No students were absent.")
        )

    if requested_status == "present":
        if not records:
            return f"📅 There are no finalized attendance records for **{_date_label(date_value)}** yet."
        return (
            f"✅ **Present Students — {_date_label(date_value)}**\n\n"
            f"Total Students: {len(STUDENTS)}\n"
            f"Present: {len(present)}\n"
            f"Absent: {len(absent)}\n\n" +
            ("\n".join(f"{i}. {r[0]} — {r[1]}" for i, r in enumerate(present, 1))
             if present else "No students were present.")
        )

    if not records:
        return (
            f"📅 **Attendance — {_date_label(date_value)}**\n\n"
            "The date is a working day, but no finalized attendance records are available yet."
        )

    rate = len(present) / len(STUDENTS) * 100 if STUDENTS else 0
    return (
        f"📊 **Attendance — {_date_label(date_value)}**\n\n"
        f"Total Students: {len(STUDENTS)}\n"
        f"Present: {len(present)}\n"
        f"Absent: {len(absent)}\n"
        f"Attendance Rate: **{rate:.2f}%**\n\n"
        "Ask **who was present** or **who was absent** if you want the complete list."
    )


def _history_matrix_data(start_date=None, end_date=None):
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT DISTINCT attendance_date
            FROM attendance
            WHERE subject = ?
            ORDER BY attendance_date
            """,
            (SUBJECT,)
        ).fetchall()
    finally:
        conn.close()

    dates = [r[0] for r in rows]
    if start_date:
        dates = [d for d in dates if d >= start_date]
    if end_date:
        dates = [d for d in dates if d <= end_date]
    return dates


def build_attendance_matrix(start_date=None, end_date=None):
    dates = _history_matrix_data(start_date, end_date)
    if not dates:
        return []

    lookup = {}
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT roll_no, attendance_date, status
            FROM attendance
            WHERE subject = ?
            """,
            (SUBJECT,)
        ).fetchall()
    finally:
        conn.close()

    for roll_no, attendance_date, status in rows:
        if attendance_date in dates:
            lookup[(roll_no, attendance_date)] = "P" if status == "Present" else "A"

    matrix = []
    for roll_no, name in get_all_students():
        row = {"Roll No": roll_no, "Name": name}
        for d in dates:
            row[_date_label(d)] = lookup.get((roll_no, d), "-")
        completed = [lookup.get((roll_no, d)) for d in dates if lookup.get((roll_no, d))]
        if completed:
            p_count = completed.count("P")
            row["Attendance %"] = round(p_count / len(completed) * 100, 2)
        else:
            row["Attendance %"] = None
        matrix.append(row)
    return matrix


def _llm_fallback(question, context_student=None):
    """Optional natural-language fallback. It never invents database facts."""
    token = os.getenv("HF_TOKEN", "")
    if not token:
        try:
            token = st.secrets.get("HF_TOKEN", "")
        except Exception:
            token = ""
    if not token:
        return None

    model = os.getenv("HF_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    today = today_date()
    total, present, absent, records = _get_class_stats()
    context = {
        "application": "SmartAttend AI",
        "department": DEPARTMENT,
        "year": YEAR,
        "shift": SHIFT,
        "minimum_attendance": MIN_ATTENDANCE,
        "attendance_window": "1:00 PM to 1:15 PM",
        "registered_students": len(STUDENTS),
        "today": today,
        "today_is_working_day": is_working_day(today),
        "today_reason": get_non_working_day_reason(today) if not is_working_day(today) else "Working Day",
        "today_present": present,
        "today_absent": absent,
        "today_records_available": bool(records),
        "context_student": context_student,
    }

    prompt = (
        "You are SmartAttend AI, a college attendance assistant. "
        "Answer only from the supplied application context. Never invent student names, "
        "attendance records, dates, percentages, or rules. If the context does not contain "
        "the requested fact, say that it is not available and explain what can be checked. "
        "Be concise but complete.\n\n"
        f"APPLICATION CONTEXT:\n{context}\n\nUSER QUESTION:\n{question}"
    )

    try:
        response = requests.post(
            f"https://router.huggingface.co/v1/chat/completions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a factual SmartAttend application assistant."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.1,
                "max_tokens": 700,
            },
            timeout=30,
        )
        if response.ok:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        pass
    return None


def database_answer(question, context_student=None):
    q = _normalise_text(question)
    requested_date = _attendance_date_from_question(question)
    student = _student_context_from_question(question, context_student)

    # Greetings and capability questions
    if q in {"hi", "hello", "hey", "hai", "hii", "good morning", "good afternoon", "good evening"}:
        return (
            "Hello! 👋 I'm **SmartAttend AI**.\n\n"
            "Ask me naturally about students, attendance, dates, attendance history, "
            "75% risk, present/absent lists, class statistics, holidays, calendar rules, "
            "attendance timing, or how this application works."
        )

    if any(x in q for x in ["what can you do", "how can you help", "what do you know", "help me"]):
        return (
            "I can analyse the SmartAttend database and explain the application. 🤖\n\n"
            "**I can answer:**\n"
            "• Present/absent lists for today or any stored date\n"
            "• Individual attendance and history\n"
            "• Highest, lowest and average attendance\n"
            "• Students below 75% and risk status\n"
            "• Attendance percentages and class statistics\n"
            "• Working days, holidays and calendar information\n"
            "• Attendance timing and system rules\n"
            "• Student registration details\n"
            "• Questions about SmartAttend features and workflow\n\n"
            "You do not need to use an exact sentence. Ask naturally."
        )

    # Application information
    if any(x in q for x in ["what is smartattend", "what is this app", "what is this application", "about the attendance app", "tell me about smartattend", "tell me about the attendance app", "attendance system about"]):
        return (
            "🎓 **SmartAttend AI** is a college attendance management system for "
            f"**{DEPARTMENT} — {YEAR}, {SHIFT}**.\n\n"
            "Students verify their registered roll number and name, then mark attendance "
            "during the controlled **1:00 PM–1:15 PM** window on working days. Duplicate "
            "attendance is prevented. After the session, students who did not mark attendance "
            "are recorded as absent.\n\n"
            "The system also provides date-wise attendance history, attendance analytics, "
            "75% risk monitoring, college calendar/holiday handling, admin reporting, "
            "WhatsApp-ready reports and this database-grounded AI assistant."
        )

    if any(x in q for x in ["minimum attendance", "attendance requirement", "required attendance", "how much attendance", "attendance percentage required"]):
        return f"The minimum attendance requirement is **{MIN_ATTENDANCE:.0f}%**. Students below this level are classified as **At Risk**."

    if any(x in q for x in ["attendance time", "attendance timing", "when can i mark", "when can students mark", "what time can", "time to mark attendance"]):
        return "Students can mark attendance only from **1:00 PM to 1:15 PM** on a working day. Each student can mark only once for the session."

    if any(x in q for x in ["after 1:15", "after 1.15", "what happens after", "if i don't mark", "if i do not mark", "miss attendance"]):
        return "After **1:15 PM**, the attendance window closes. Students can no longer mark attendance for that session, and unmarked students are automatically recorded as **Absent** when the session is finalized."

    if "department" in q and not student:
        return f"The department is **{DEPARTMENT}**."
    if any(x in q for x in ["which year", "what year", "year are we", "class year"]):
        return f"The class is **{YEAR}**."
    if "shift" in q:
        return f"The class is **{SHIFT}**."
    if any(x in q for x in ["class details", "class information", "about our class", "our class"]):
        return (
            f"🎓 Department: {DEPARTMENT}\n"
            f"📚 Year: {YEAR}\n"
            f"🕑 Shift: {SHIFT}\n"
            f"👩‍🎓 Registered Students: {len(STUDENTS)}\n"
            f"📊 Minimum Attendance: {MIN_ATTENDANCE:.0f}%\n"
            "⏰ Attendance Window: 1:00 PM–1:15 PM"
        )

    if any(x in q for x in ["how many students", "total students", "number of students", "registered students"]):
        return f"There are **{len(STUDENTS)} registered students** in SmartAttend."

    # Date + calendar questions should be handled before generic date attendance.
    if requested_date and any(x in q for x in ["holiday", "working day", "working", "calendar", "non working", "non-working"]):
        return calendar_answer_for_date(requested_date)

    # Exact student identity
    if student and any(x in q for x in ["name", "who is", "roll number", "roll no", "registration", "registered"]):
        return f"**{student[1]}** is registered with roll number **{student[0]}**."

    # Individual student attendance and date-specific status
    if student:
        roll_no, student_name = student
        if requested_date:
            records = get_records_for_date(requested_date, SUBJECT)
            record = next((r for r in records if r[0] == roll_no), None)
            if record:
                if record[2] == "Present":
                    return f"Yes — **{student_name}** was **Present** on **{_date_label(requested_date)}**. Attendance was marked at **{record[3]}**."
                return f"**{student_name}** was **Absent** on **{_date_label(requested_date)}**."
            if not is_working_day(requested_date):
                return f"**{_date_label(requested_date)}** was a non-working day, so there was no attendance session."
            return f"There is no finalized attendance record for **{student_name}** on **{_date_label(requested_date)}** yet."

        total, present, absent, percentage = get_student_attendance(roll_no)
        if any(x in q for x in ["history", "attendance history", "records", "when was"]):
            records = [r for r in get_all_attendance() if r[0] == roll_no]
            if not records:
                return f"There is no attendance history available for **{student_name}** yet."
            lines = [f"📚 **Attendance History — {student_name} ({roll_no})**", ""]
            for r in sorted(records, key=lambda x: x[2]):
                lines.append(f"• {_date_label(r[2])} — **{r[4]}**" + (f" at {r[5]}" if r[4] == "Present" else ""))
            return "\n".join(lines)

        if any(x in q for x in ["reach 75", "get to 75", "achieve 75", "improve to 75", "how many classes", "how many sessions", "how many more"]):
            if total == 0:
                return f"**{student_name}** has no completed attendance sessions yet, so a 75% recovery calculation cannot be made."
            if percentage >= MIN_ATTENDANCE:
                return f"**{student_name}** is already at **{percentage:.2f}%**, which meets the {MIN_ATTENDANCE:.0f}% requirement."
            needed = required_future_classes_for_75(present, total)
            return f"**{student_name}** currently has **{percentage:.2f}%** attendance and needs to attend the next **{needed} consecutive classes** to reach {MIN_ATTENDANCE:.0f}%, assuming no further absence."

        if any(x in q for x in ["can i miss", "can she miss", "can he miss", "how many can i miss", "how many classes can i miss", "how many more can"]):
            if total == 0:
                return f"There is not enough attendance data for **{student_name}** yet."
            if percentage < MIN_ATTENDANCE:
                return f"**{student_name}** is currently below {MIN_ATTENDANCE:.0f}%, so missing more classes would increase the risk."
            allowed = maximum_future_absences_at_75(present, total)
            return f"**{student_name}** currently has **{percentage:.2f}%** attendance and can miss up to **{allowed} more class(es)** while remaining at or above {MIN_ATTENDANCE:.0f}%, assuming no other changes."

        if any(x in q for x in ["attendance", "percentage", "present", "absent", "status", "risk", "classes", "sessions"]):
            if total == 0:
                return f"There are no completed attendance sessions for **{student_name}** yet.\n\nPresent: 0\nAbsent: 0\nAttendance: **N/A**\nStatus: **No Data**"
            risk = "At Risk" if percentage < MIN_ATTENDANCE else "Safe"
            return f"📊 **Attendance — {student_name} ({roll_no})**\n\nSessions: {total}\nPresent: {present}\nAbsent: {absent}\nAttendance: **{percentage:.2f}%**\nStatus: **{risk}**"

    # Present / absent list for a requested date, including natural wording such as "absentees".
    status = None
    absent_words = ["absent", "absentee", "absentees", "didn't attend", "did not attend", "not attend", "missed", "missing students", "who missed"]
    present_words = ["present", "attended", "who attended", "came today", "who came", "students who came"]
    if any(x in q for x in absent_words):
        status = "absent"
    elif any(x in q for x in present_words):
        status = "present"

    if status:
        if requested_date is None:
            requested_date = today_date()
        return _date_attendance_answer(requested_date, status)

    # Today's / selected-date summary
    if requested_date and any(x in q for x in ["summary", "attendance", "details", "report", "how many"]):
        return _date_attendance_answer(requested_date)

    # Analytics across completed attendance
    summary = [s for s in get_attendance_summary() if s["Total Sessions"] > 0 and s["Attendance %"] is not None]
    if any(x in q for x in ["below 75", "under 75", "less than 75", "at risk", "need to improve"]):
        risky = [s for s in summary if s["Attendance %"] < MIN_ATTENDANCE]
        if not risky:
            return "There are no students currently below 75% based on completed attendance sessions."
        lines = [f"⚠️ **{len(risky)} student(s) below {MIN_ATTENDANCE:.0f}%**", ""]
        lines.extend(f"{i}. {s['Roll No']} — {s['Name']} — **{s['Attendance %']:.2f}%**" for i, s in enumerate(sorted(risky, key=lambda x: x["Attendance %"]), 1))
        return "\n".join(lines)

    if any(x in q for x in ["highest attendance", "highest percentage", "best attendance", "top attendance", "most attendance", "who has the highest"]):
        if not summary:
            return "There are no completed attendance sessions yet, so a highest-attendance result cannot be calculated."
        top = max(summary, key=lambda x: x["Attendance %"])
        return f"🏆 **Highest Attendance**\n\n{top['Name']} ({top['Roll No']})\nAttendance: **{top['Attendance %']:.2f}%**\nPresent: {top['Present']}\nAbsent: {top['Absent']}\nSessions: {top['Total Sessions']}"

    if any(x in q for x in ["lowest attendance", "lowest percentage", "worst attendance", "least attendance", "who has the lowest"]):
        if not summary:
            return "There are no completed attendance sessions yet, so a lowest-attendance result cannot be calculated."
        low = min(summary, key=lambda x: x["Attendance %"])
        return f"📉 **Lowest Attendance**\n\n{low['Name']} ({low['Roll No']})\nAttendance: **{low['Attendance %']:.2f}%**\nPresent: {low['Present']}\nAbsent: {low['Absent']}\nSessions: {low['Total Sessions']}"

    if any(x in q for x in ["average attendance", "class average", "average percentage", "overall attendance"]):
        if not summary:
            return "There are no completed attendance sessions yet, so the class average cannot be calculated."
        avg = sum(s["Attendance %"] for s in summary) / len(summary)
        return f"📊 **Class Average Attendance: {avg:.2f}%** based on {len(summary)} students with completed attendance data."

    if any(x in q for x in ["perfect attendance", "100% attendance"]):
        perfect = [s for s in summary if abs(s["Attendance %"] - 100) < 1e-9]
        if not perfect:
            return "No student currently has 100% attendance based on completed sessions."
        return "🏅 **Perfect Attendance**\n\n" + "\n".join(f"{i}. {s['Roll No']} — {s['Name']}" for i, s in enumerate(perfect, 1))

    if any(x in q for x in ["rank", "top 5", "top five", "bottom 5", "bottom five"]):
        if not summary:
            return "There are no completed attendance sessions yet, so ranking cannot be calculated."
        reverse = not any(x in q for x in ["bottom", "lowest"])
        count = 5 if any(x in q for x in ["5", "five"]) else len(summary)
        ranked = sorted(summary, key=lambda x: x["Attendance %"], reverse=reverse)[:count]
        title = "Top Attendance Ranking" if reverse else "Lowest Attendance Ranking"
        return f"📊 **{title}**\n\n" + "\n".join(f"{i}. {s['Name']} — {s['Attendance %']:.2f}%" for i, s in enumerate(ranked, 1))

    # Today fallback only when the user is actually asking about attendance.
    if requested_date is None and any(x in q for x in ["today", "todays", "today's"]):
        if any(x in q for x in ["attendance", "present", "absent", "attend", "summary", "report"]):
            return _date_attendance_answer(today_date())

    # Student list
    if any(x in q for x in ["list students", "show students", "all students", "student list", "registered list", "who are the students"]):
        return "👩‍🎓 **Registered Students**\n\n" + "\n".join(f"{i}. {r} — {n}" for i, (r, n) in enumerate(get_all_students(), 1))

    # Database status
    if any(x in q for x in ["database", "data available", "how much data", "how many records"]):
        total_records = len(get_all_attendance())
        return f"🗄️ **SmartAttend Data Status**\n\nRegistered students: {len(STUDENTS)}\nAttendance records: {total_records}\nMinimum attendance: {MIN_ATTENDANCE:.0f}%"

    # Calendar questions without explicit date.
    if any(x in q for x in ["holiday", "working day", "is today working", "is today a holiday", "college today"]):
        return calendar_answer_for_date(today_date())

    return None


def assistant_response(question):
    context_student = st.session_state.get("last_student")
    answer = database_answer(question, context_student)

    student = find_student_from_question(question)
    if student:
        st.session_state["last_student"] = student

    if answer:
        return answer

    llm_answer = _llm_fallback(question, st.session_state.get("last_student"))
    if llm_answer:
        return llm_answer

    return (
        "I can answer questions about the **SmartAttend application and its stored data**, "
        "but I couldn't identify the exact information you requested. 🤖\n\n"
        "Try asking naturally, for example:\n"
        "• Who are today's absentees?\n"
        "• Who attended today?\n"
        "• Who was absent on 15-09-2026?\n"
        "• Show attendance for a student\n"
        "• Who has the lowest attendance?\n"
        "• Who is below 75%?\n"
        "• What is the class average?\n"
        "• Is tomorrow a holiday?\n"
        "• Explain how SmartAttend works."
    )

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🎓",
    layout="wide"
)


# ============================================================
# INITIALIZE DATABASE
# ============================================================

initialize_database()


# ============================================================
# AUTOMATIC ATTENDANCE SCHEDULER
# ============================================================

@st.cache_resource
def start_attendance_scheduler():

    scheduler = BackgroundScheduler(
        timezone="Asia/Kolkata"
    )

    scheduler.add_job(
        automatic_finalize_attendance,
        trigger="cron",
        hour=13,
        minute=15,
        id="daily_attendance_finalization",
        replace_existing=True
    )

    scheduler.start()

    return scheduler


start_attendance_scheduler()


# ============================================================
# CUSTOM STYLE
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        font-size: 18px;
        margin-bottom: 25px;
    }

    .card {
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(128,128,128,0.25);
        margin-bottom: 15px;
    }

    .risk {
        font-weight: bold;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# TODAY'S ATTENDANCE STATUS
# ============================================================

today = today_date()

if not is_working_day(today):

    reason = get_non_working_day_reason(
        today
    )

    st.warning(
        f"""
        🏖️ **TODAY IS A HOLIDAY / NON-WORKING DAY**

        📅 Date: **{today}**

        📌 Reason: **{reason}**

        🚫 No attendance session is available today.

        📨 No attendance report will be generated or sent.
        """
    )

else:

    st.success(
        """
        🟢 **TODAY IS A WORKING DAY**

        ⏰ Attendance session: **1:00 PM – 1:15 PM**

        📊 Attendance will be automatically finalized after the session.
        """
    )


st.divider()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "🎓 SmartAttend AI"
)

st.sidebar.write(
    f"**{DEPARTMENT}**"
)

st.sidebar.write(
    f"**{YEAR} • {SHIFT}**"
)

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Home",
        "🎓 Student Portal",
        "🔐 Admin Dashboard",
        "🤖 AI Attendance Assistant"
    ]
)

st.sidebar.divider()

st.sidebar.info(
    "Attendance Window\n\n"
    "1:00 PM – 1:15 PM\n\n"
    "Minimum Attendance: 75%"
)


# ============================================================
# HOME
# ============================================================

if page == "🏠 Home":

    st.markdown(
        '<div class="main-title">'
        '🎓 SmartAttend AI'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        "AI-Powered College Attendance "
        "Management & Risk Prediction System"
        "</div>",
        unsafe_allow_html=True
    )

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "👩‍🎓 Registered Students",
            len(get_all_students())
        )

    with col2:

        present, absent = get_today_counts(
            SUBJECT
        )

        st.metric(
            "✅ Present Today",
            present
        )

    with col3:

        st.metric(
            "❌ Absent Today",
            absent
        )

    st.divider()

    st.subheader(
        "✨ System Features"
    )

    features = [
        "🎓 Student self-attendance",
        "🔍 Roll number and name verification",
        "⏰ Controlled 1:00 PM – 1:15 PM attendance window",
        "🚫 Duplicate attendance prevention",
        "❌ Automatic absent record generation",
        "📊 Admin attendance dashboard",
        "📈 75% attendance risk analysis",
        "🤖 Conversational AI Attendance Assistant",
        "📱 WhatsApp-ready attendance reports",
        "🏖️ College holiday management",
        "🗄️ Persistent SQLite attendance database"
    ]

    for feature in features:

        st.write(feature)

    st.divider()

    st.subheader(
        "📌 How SmartAttend AI Works"
    )

    st.markdown(
        """
        **1. Student Verification**

        Student enters registered roll number and name.

        **2. Working Day Check**

        SmartAttend checks whether the current date
        is a working day, weekend, or registered college holiday.

        **3. Attendance Window**

        Attendance can be marked only between
        **1:00 PM and 1:15 PM**.

        **4. Attendance Recording**

        Once marked, the student's attendance is
        permanently stored for that date.

        **5. Duplicate Prevention**

        The same student cannot mark attendance twice
        for the same session.

        **6. Automatic Absent Processing**

        After the attendance window,
        students without attendance are automatically
        recorded as absent.

        **7. Analytics**

        Attendance percentage and 75% risk status
        are calculated from stored records.

        **8. AI Assistant**

        The assistant answers attendance-related
        questions using SmartAttend database information.
        """
    )


# ============================================================
# STUDENT PORTAL
# ============================================================

elif page == "🎓 Student Portal":

    st.title(
        "🎓 Student Attendance Portal"
    )

    today = today_date()

    if not is_working_day(today):

        status = "holiday"

        reason = get_non_working_day_reason(
            today
        )

        st.warning(
            f"""
            🏖️ **TODAY IS A NON-WORKING DAY**

            📅 Date: **{today}**

            📌 Reason: **{reason}**

            🚫 Attendance is not available today.
            """
        )

    else:

        st.info(
            "Attendance window: "
            "**1:00 PM – 1:15 PM**"
        )

        status = attendance_window_status()

        if status == "before":

            st.warning(
                "⏳ Attendance has not started yet. "
                "Please return at 1:00 PM."
            )

        elif status == "after":

            st.error(
                "🔒 The attendance window is closed."
            )

        else:

            st.success(
                "🟢 Attendance window is currently OPEN."
            )

    st.divider()

    roll_no = st.text_input(
        "Roll Number",
        placeholder="Example: E25AI206"
    )

    name = st.text_input(
        "Student Name",
        placeholder="Enter your registered full name"
    )

    if st.button(
        "🔍 Verify Student",
        use_container_width=True
    ):

        if not roll_no or not name:

            st.warning(
                "Please enter both roll number and name."
            )

        else:

            student = get_student(
                roll_no,
                name
            )

            if not student:

                st.error(
                    "❌ Student verification failed. "
                    "Check your roll number and registered name."
                )

            else:

                st.session_state[
                    "verified_student"
                ] = student

                st.success(
                    f"✅ Verified: "
                    f"{student[1]} "
                    f"({student[0]})"
                )

    if "verified_student" in st.session_state:

        student = st.session_state[
            "verified_student"
        ]

        st.divider()

        st.subheader(
            "Student Details"
        )

        col1, col2 = st.columns(2)

        with col1:

            st.write(
                f"**Roll Number:** {student[0]}"
            )

        with col2:

            st.write(
                f"**Name:** {student[1]}"
            )

        st.divider()

        existing = attendance_already_marked(
            student[0],
            today_date(),
            SUBJECT
        )

        if status == "holiday":

            st.warning(
                "🏖️ Attendance cannot be marked "
                "because today is a non-working day."
            )

        elif existing:

            if existing[1] == "Present":

                st.success(
                    "✅ Your attendance has already "
                    "been marked for today's session."
                )

            else:

                st.warning(
                    "Your attendance is recorded as absent."
                )

        elif (
            status == "open"
            and is_working_day(today_date())
        ):

            if st.button(
                "✅ MARK MY ATTENDANCE",
                use_container_width=True
            ):

                success, message = mark_present(
                    student[0],
                    today_date(),
                    SUBJECT
                )

                if success:

                    st.success(
                        "🎉 Attendance marked successfully!"
                    )

                    st.balloons()

                    st.rerun()

                else:

                    st.warning(message)

        elif status == "before":

            st.info(
                "⏳ Attendance will open at 1:00 PM."
            )

        else:

            st.error(
                "🔒 Attendance window is closed."
            )

        st.divider()

        total, present, absent, percentage = (
            get_student_attendance(
                student[0]
            )
        )

        st.subheader(
            "📊 My Attendance"
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Total Sessions",
                total
            )

        with c2:

            st.metric(
                "Present",
                present
            )

        with c3:

            if percentage is None:

                st.metric(
                    "Attendance",
                    "N/A"
                )

            else:

                st.metric(
                    "Attendance",
                    f"{percentage:.2f}%"
                )

        if total == 0:

            st.info(
                "ℹ️ No completed attendance sessions "
                "are available yet."
            )

        elif percentage < MIN_ATTENDANCE:

            st.error(
                f"⚠️ Your attendance is below "
                f"{MIN_ATTENDANCE:.0f}%."
            )

        else:

            st.success(
                f"✅ Your attendance is above "
                f"{MIN_ATTENDANCE:.0f}%."
            )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

elif page == "🔐 Admin Dashboard":

    st.title(
        "🔐 Admin Dashboard"
    )

    if "admin_authenticated" not in st.session_state:

        st.session_state[
            "admin_authenticated"
        ] = False

    if not st.session_state[
        "admin_authenticated"
    ]:

        password = st.text_input(
            "Admin Password",
            type="password"
        )

        if st.button(
            "🔓 Login",
            use_container_width=True
        ):

            if password == ADMIN_PASSWORD:

                st.session_state[
                    "admin_authenticated"
                ] = True

                st.success(
                    "Login successful."
                )

                st.rerun()

            else:

                st.error(
                    "Incorrect password."
                )

    else:

        st.success(
            "🔓 Admin authenticated"
        )

        if st.button(
            "Logout"
        ):

            st.session_state[
                "admin_authenticated"
            ] = False

            st.rerun()

        # ====================================================
        # HOLIDAY MANAGEMENT
        # ====================================================

        st.divider()

        st.subheader(
            "🏖️ Holiday Management"
        )

        st.write(
            "Add official college holidays here. "
            "Attendance and automatic reports will be "
            "skipped on these dates."
        )

        holiday_date = st.date_input(
            "📅 Select Holiday Date"
        )

        holiday_name = st.text_input(
            "🏷️ Holiday Name",
            placeholder="Example: College Holiday"
        )

        if st.button(
            "➕ Add Holiday",
            use_container_width=True
        ):

            if not holiday_name.strip():

                st.warning(
                    "Please enter the holiday name."
                )

            else:

                add_holiday(
                    holiday_date.isoformat(),
                    holiday_name.strip()
                )

                st.success(
                    f"🏖️ Holiday added: "
                    f"{holiday_date.strftime('%d-%m-%Y')} - "
                    f"{holiday_name.strip()}"
                )

                st.rerun()

        st.subheader(
            "📋 Saved Holidays"
        )

        holidays = get_all_holidays()

        if holidays:

            holiday_table = []

            for holiday in holidays:

                holiday_table.append(
                    {
                        "Date": holiday[0],
                        "Holiday": holiday[1]
                    }
                )

            st.dataframe(
                holiday_table,
                use_container_width=True,
                hide_index=True
            )

            st.subheader(
                "🗑️ Remove Holiday"
            )

            holiday_options = {
                f"{date} - {name}": date
                for date, name in holidays
            }

            selected_holiday = st.selectbox(
                "Select holiday to remove",
                list(
                    holiday_options.keys()
                )
            )

            if st.button(
                "🗑️ Remove Selected Holiday",
                use_container_width=True
            ):

                selected_date = holiday_options[
                    selected_holiday
                ]

                remove_holiday(
                    selected_date
                )

                st.success(
                    "Holiday removed successfully."
                )

                st.rerun()

        else:

            st.info(
                "No holidays have been added yet."
            )

        # ====================================================
        # TODAY'S ATTENDANCE
        # ====================================================

        st.divider()

        st.subheader(
            "📅 Today's Attendance"
        )

        if not is_working_day(
            today_date()
        ):

            reason = get_non_working_day_reason(
                today_date()
            )

            st.warning(
                f"""
                🏖️ **TODAY IS A NON-WORKING DAY**

                📅 Date: **{today_date()}**

                📌 Reason: **{reason}**

                🚫 Attendance session is disabled.

                📨 No attendance report will be generated.
                """
            )

            present = 0
            absent = 0

        else:

            present, absent = get_today_counts(
                SUBJECT
            )

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Total Students",
                len(STUDENTS)
            )

        with c2:

            st.metric(
                "Present",
                present
            )

        with c3:

            st.metric(
                "Absent",
                absent
            )

        # ====================================================
        # FINALIZATION STATUS
        # ====================================================

        st.divider()

        st.subheader(
            "⚙️ Attendance Processing"
        )

        if not is_working_day(
            today_date()
        ):

            st.info(
                "🏖️ Automatic attendance finalization "
                "is disabled because today is a "
                "non-working day."
            )

        elif attendance_window_status() == "after":

            st.success(
                "🤖 Today's attendance has been "
                "processed after the 1:15 PM "
                "attendance window."
            )

        elif attendance_window_status() == "open":

            st.info(
                "🟢 Attendance window is currently open."
            )

        else:

            st.info(
                "⏳ Attendance session has not started yet."
            )

        # ====================================================
        # TODAY'S RECORDS
        # ====================================================

        st.divider()

        st.subheader(
            "📋 Today's Records"
        )

        records = get_today_records(
            SUBJECT
        )

        if records:

            table_data = []

            for (
                roll_no,
                name,
                status_value,
                marked_time
            ) in records:

                table_data.append(
                    {
                        "Roll No": roll_no,
                        "Name": name,
                        "Status": status_value,
                        "Marked Time": marked_time
                    }
                )

            st.dataframe(
                table_data,
                use_container_width=True,
                hide_index=True
            )

        else:

            if is_working_day(
                today_date()
            ):

                st.info(
                    "No attendance records "
                    "for today yet."
                )

            else:

                st.info(
                    "No attendance records because "
                    "today is a non-working day."
                )

        # ====================================================
        # STUDENT ATTENDANCE ANALYTICS
        # ====================================================

        st.divider()

        st.subheader(
            "📈 Student Attendance Analytics"
        )

        summary = get_attendance_summary()

        st.dataframe(
            summary,
            use_container_width=True,
            hide_index=True
        )

        risky_students = [
            s
            for s in summary
            if (
                s["Attendance %"] != "N/A"
                and s["Attendance %"] < MIN_ATTENDANCE
                and s["Total Sessions"] > 0
            )
        ]

        # ====================================================
        # ATTENDANCE RISK
        # ====================================================

        st.divider()

        st.subheader(
            "⚠️ Attendance Risk"
        )

        if risky_students:

            st.error(
                f"{len(risky_students)} student(s) "
                f"are below the "
                f"{MIN_ATTENDANCE:.0f}% requirement."
            )

            for student in risky_students:

                st.write(
                    f"🔴 {student['Roll No']} - "
                    f"{student['Name']} - "
                    f"{student['Attendance %']}%"
                )

        elif all(
            s["Total Sessions"] == 0
            for s in summary
        ):

            st.info(
                "ℹ️ No completed attendance sessions yet. "
                "Risk analysis will begin after attendance "
                "sessions are recorded."
            )

        else:

            st.success(
                f"✅ No student is currently below "
                f"the {MIN_ATTENDANCE:.0f}% requirement."
            )

        # ====================================================
        # ATTENDANCE REGISTER - STUDENT x DATE MATRIX
        # ====================================================

        st.divider()
        st.subheader("📊 Attendance Register")
        st.caption("Rows = students • Columns = attendance dates • P = Present • A = Absent • - = No record")

        history_dates = _history_matrix_data()

        if history_dates:
            min_history = datetime.fromisoformat(history_dates[0]).date()
            max_history = datetime.fromisoformat(history_dates[-1]).date()

            r1, r2 = st.columns(2)
            with r1:
                register_from = st.date_input(
                    "From Date",
                    value=min_history,
                    min_value=min_history,
                    max_value=max_history,
                    key="register_from"
                )
            with r2:
                register_to = st.date_input(
                    "To Date",
                    value=max_history,
                    min_value=min_history,
                    max_value=max_history,
                    key="register_to"
                )

            if register_from > register_to:
                st.error("From Date cannot be later than To Date.")
            else:
                matrix = build_attendance_matrix(
                    register_from.isoformat(),
                    register_to.isoformat()
                )
                if matrix:
                    st.dataframe(
                        matrix,
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("No attendance records are available in the selected date range.")
        else:
            st.info("Attendance Register will appear here after the first attendance session is finalized.")

        # ====================================================
        # COMPLETE ATTENDANCE HISTORY
        # ====================================================

        st.divider()

        st.subheader(
            "📚 Complete Attendance History"
        )

        all_records = get_all_attendance()

        if all_records:

            history = []

            for record in all_records:

                history.append(
                    {
                        "Roll No": record[0],
                        "Name": record[1],
                        "Date": record[2],
                        "Subject": record[3],
                        "Status": record[4],
                        "Time": record[5]
                    }
                )

            st.dataframe(
                history,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No attendance history available yet."
            )

        # ====================================================
        # WHATSAPP DAILY REPORT
        # ====================================================

        st.divider()

        st.subheader(
            "📱 WhatsApp Daily Report"
        )

        if not is_working_day(
            today_date()
        ):

            st.info(
                "🏖️ No WhatsApp attendance report "
                "is generated on non-working days."
            )

        else:

            report = generate_daily_report()

            st.code(
                report,
                language="text"
            )

            wa_maam = generate_whatsapp_link(
                CLASS_MAAM_PHONE,
                report
            )

            wa_admin = generate_whatsapp_link(
                ADMIN_PHONE,
                report
            )

            c1, c2 = st.columns(2)

            with c1:

                st.markdown(
                    f"[📱 Send to Class Ma'am]({wa_maam})"
                )

            with c2:

                st.markdown(
                    f"[📱 Send to Admin]({wa_admin})"
                )

            st.caption(
                "WhatsApp links open a pre-filled message. "
                "The final Send action is performed by the user."
            )


# ============================================================
# AI ATTENDANCE ASSISTANT
# ============================================================

elif page == "🤖 AI Attendance Assistant":

    st.title(
        "🤖 AI Attendance Assistant"
    )

    st.write(
        "Your conversational assistant for SmartAttend AI."
    )

    st.info(
    "Examples: "
    "What is the name of E25AI205? • "
    "What is the attendance requirement? • "
    "Who is absent today? • "
    "Who has the lowest attendance? • "
    "Show attendance for E25AI205."
    )

    if "chat_history" not in st.session_state:

        st.session_state[
            "chat_history"
        ] = []

    question = st.chat_input(
        "Ask me anything about SmartAttend..."
    )

    if question:

        st.session_state[
            "chat_history"
        ].append(
            {
                "role": "user",
                "content": question
            }
        )

        answer = assistant_response(
            question
        )

        st.session_state[
            "chat_history"
        ].append(
            {
                "role": "assistant",
                "content": answer
            }
        )

    for message in st.session_state[
        "chat_history"
    ]:

        with st.chat_message(
            message["role"]
        ):

            st.markdown(
                message["content"]
            )

    if st.session_state[
        "chat_history"
    ]:

        st.divider()

        if st.button(
            "🗑️ Clear Chat"
        ):

            st.session_state[
                "chat_history"
            ] = []

            st.session_state.pop(
                "last_student",
                None
            )

            st.rerun()
