import streamlit as st
import sqlite3
import re
import math
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
        r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b"
    ]

    for pattern in date_patterns:

        match = re.search(
            pattern,
            question
        )

        if match:

            try:

                groups = match.groups()

                if len(groups[0]) == 4:

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

def database_answer(
    question,
    context_student=None
):

    q = question.lower().strip()

    summary = get_attendance_summary()

    # ========================================================
    # DATE CONTEXT
    # ========================================================

    requested_date = parse_date_from_question(
        question
    )

    # ========================================================
    # STUDENT DETECTION
    # ========================================================

    student = find_student_from_question(
        question
    )

    if student is None and context_student:

        if any(
            word in q
            for word in [
                "she",
                "her",
                "he",
                "him",
                "his",
                "that student",
                "this student",
                "that person",
                "their",
                "them"
            ]
        ):

            student = context_student

    # ========================================================
    # GREETINGS
    # ========================================================

    if q in [
        "hi",
        "hello",
        "hey",
        "hai",
        "hii",
        "good morning",
        "good afternoon",
        "good evening"
    ]:

        return (
            "Hello! 👋 I'm SmartAttend AI.\n\n"
            "I can help you with student details, "
            "attendance, attendance percentage, "
            "75% risk analysis, today's attendance, "
            "college holidays, calendar information, "
            "and SmartAttend rules.\n\n"
            "What would you like to know?"
        )

    # ========================================================
    # WHAT CAN YOU DO
    # ========================================================

    if (
        "what can you do" in q
        or "help me" in q
        or "how can you help" in q
        or "what do you know" in q
    ):

        return (
            "Of course! 😊 I can help you with almost "
            "anything related to SmartAttend.\n\n"
            "🎓 **Students**\n"
            "• Find a student's name or roll number\n"
            "• Check registered students\n"
            "• Check class details\n\n"
            "📊 **Attendance**\n"
            "• Individual attendance\n"
            "• Present and absent students\n"
            "• Attendance percentage\n"
            "• Highest and lowest attendance\n"
            "• Students below 75%\n"
            "• Attendance history\n"
            "• Attendance trends and calculations\n\n"
            "📅 **Calendar**\n"
            "• Today's working/holiday status\n"
            "• Tomorrow and yesterday\n"
            "• Specific dates\n"
            "• College events and calendar information\n\n"
            "⚙️ **Application Rules**\n"
            "• Attendance timing\n"
            "• Minimum attendance requirement\n"
            "• Department, year and shift\n"
            "• What happens after 1:15 PM\n\n"
            "Just ask naturally — you don't need to use "
            "a specific command. 🙂"
        )

    # ========================================================
    # APPLICATION INFORMATION
    # ========================================================

    if (
        "minimum attendance" in q
        or "attendance requirement" in q
        or "required attendance" in q
        or "how much attendance" in q
        or "attendance percentage required" in q
    ):

        return (
            f"The minimum attendance requirement "
            f"in SmartAttend is **{MIN_ATTENDANCE:.0f}%**. "
            "Students below this level are considered "
            "at risk."
        )

    if (
        (
            "what time" in q
            and (
                "attendance" in q
                or "mark" in q
            )
        )
        or "attendance timing" in q
        or "attendance time" in q
        or "when can i mark" in q
        or "when can students mark" in q
    ):

        return (
            "Students can mark attendance from "
            "**1:00 PM to 1:15 PM** on a working day. "
            "The same student cannot mark attendance "
            "twice for the same session."
        )

    if (
        "after 1:15" in q
        or "after 1.15" in q
        or "miss the attendance" in q
        or "if i don't mark" in q
        or "if a student doesn't mark" in q
    ):

        return (
            "After the 1:15 PM attendance window closes, "
            "students can no longer mark attendance for "
            "that session. SmartAttend automatically "
            "records students who did not mark attendance "
            "as **Absent** when the session is finalized."
        )

    if (
        "department" in q
        or "which department" in q
        or "what department" in q
    ):

        return (
            f"The class is **{DEPARTMENT}**."
        )

    if (
        "which year" in q
        or "what year" in q
        or "year are we" in q
        or "which class year" in q
    ):

        return (
            f"The class is in **{YEAR}**."
        )

    if (
        "which shift" in q
        or "what shift" in q
    ):

        return (
            f"The class is **{SHIFT}**."
        )

    if (
        "class details" in q
        or "class information" in q
        or "our class" in q
        or "about our class" in q
    ):

        return (
            "Here are the SmartAttend class details:\n\n"
            f"🎓 Department: {DEPARTMENT}\n"
            f"📚 Year: {YEAR}\n"
            f"🕑 Shift: {SHIFT}\n"
            f"👩‍🎓 Students: {len(STUDENTS)}\n"
            f"📊 Minimum attendance: "
            f"{MIN_ATTENDANCE:.0f}%\n"
            "⏰ Attendance: 1:00 PM – 1:15 PM"
        )

    if (
        "how many students" in q
        or "total students" in q
        or "number of students" in q
        or "registered students" in q
        or "how many are registered" in q
    ):

        return (
            f"There are **{len(STUDENTS)} registered students** "
            "in SmartAttend."
        )

    # ========================================================
    # STUDENT NAME / ROLL NUMBER
    # ========================================================

    if student:

        roll_no = student[0]
        student_name = student[1]

        asks_identity = (
            "name" in q
            or "who is" in q
            or "belongs" in q
            or "roll" in q
            or "registration" in q
            or "registered" in q
        )

        if asks_identity:

            if re.search(
                r"\bE25AI\d{3}\b",
                question.upper()
            ):

                return (
                    f"Yes. **{roll_no}** is registered "
                    f"to **{student_name}**."
                )

            return (
                f"**{student_name}** is registered with "
                f"roll number **{roll_no}**."
            )

    # ========================================================
    # STUDENT ATTENDANCE INFORMATION
    # ========================================================

    if student:

        roll_no = student[0]
        student_name = student[1]

        total, present, absent, percentage = (
            get_student_attendance(
                roll_no
            )
        )

        # ----------------------------------------------------
        # DATE-SPECIFIC STUDENT ATTENDANCE
        # ----------------------------------------------------

        if requested_date:

            records = get_records_for_date(
                requested_date,
                SUBJECT
            )

            student_record = None

            for record in records:

                if record[0] == roll_no:

                    student_record = record

                    break

            if student_record:

                status_value = student_record[2]

                if status_value == "Present":

                    return (
                        f"Yes — **{student_name}** was "
                        f"**Present** on "
                        f"{format_date(requested_date)}. "
                        f"Attendance was marked at "
                        f"{student_record[3]}."
                    )

                return (
                    f"**{student_name}** was recorded as "
                    f"**Absent** on "
                    f"{format_date(requested_date)}."
                )

            if not is_working_day(
                requested_date
            ):

                return (
                    f"{format_date(requested_date)} was a "
                    f"non-working day, so there was no "
                    "attendance session."
                )

            return (
                f"I don't have an attendance record for "
                f"**{student_name}** on "
                f"{format_date(requested_date)} yet."
            )

        # ----------------------------------------------------
        # CURRENT ATTENDANCE
        # ----------------------------------------------------

        if (
            "attendance" in q
            or "percentage" in q
            or "present" in q
            or "absent" in q
            or "status" in q
            or "risk" in q
            or "safe" in q
            or "classes" in q
            or "sessions" in q
        ):

            if total == 0:

                return (
                    f"I don't have any completed "
                    f"attendance sessions for "
                    f"**{student_name}** yet.\n\n"
                    f"Present: 0\n"
                    f"Absent: 0\n"
                    f"Attendance: **N/A**\n"
                    f"Status: **No Data**"
                )

            risk = (
                "At Risk"
                if percentage < MIN_ATTENDANCE
                else "Safe"
            )

            return (
                f"Here's the current attendance for "
                f"**{student_name}** ({roll_no}):\n\n"
                f"📚 Sessions: {total}\n"
                f"✅ Present: {present}\n"
                f"❌ Absent: {absent}\n"
                f"📊 Attendance: **{percentage:.2f}%**\n"
                f"⚠️ Status: **{risk}**"
            )

    # ========================================================
    # CAN STUDENT REACH 75%
    # ========================================================

    if student and (
        "reach 75" in q
        or "get to 75" in q
        or "achieve 75" in q
        or "come back to 75" in q
        or "improve to 75" in q
    ):

        roll_no = student[0]
        student_name = student[1]

        total, present, absent, percentage = (
            get_student_attendance(
                roll_no
            )
        )

        if total == 0:

            return (
                f"**{student_name}** has no completed "
                "attendance sessions yet, so there isn't "
                "enough data to calculate a recovery plan."
            )

        if percentage >= MIN_ATTENDANCE:

            return (
                f"Yes — **{student_name}** is already at "
                f"**{percentage:.2f}%**, which is above the "
                f"{MIN_ATTENDANCE:.0f}% requirement."
            )

        needed = required_future_classes_for_75(
            present,
            total
        )

        return (
            f"Yes. **{student_name}** can reach "
            f"{MIN_ATTENDANCE:.0f}% by attending the next "
            f"**{needed} consecutive classes** without "
            "missing one.\n\n"
            f"Current attendance: {percentage:.2f}%"
        )

    # ========================================================
    # HOW MANY CLASSES NEEDED
    # ========================================================

    if student and (
        "how many classes" in q
        or "how many sessions" in q
        or "how many more" in q
    ) and (
        "75" in q
        or "required" in q
        or "attendance" in q
    ):

        roll_no = student[0]
        student_name = student[1]

        total, present, absent, percentage = (
            get_student_attendance(
                roll_no
            )
        )

        if total == 0:

            return (
                f"**{student_name}** has no completed "
                "attendance sessions yet."
            )

        if percentage >= MIN_ATTENDANCE:

            return (
                f"**{student_name}** is already above the "
                f"{MIN_ATTENDANCE:.0f}% requirement at "
                f"{percentage:.2f}%."
            )

        needed = required_future_classes_for_75(
            present,
            total
        )

        return (
            f"**{student_name}** currently has "
            f"{percentage:.2f}% attendance.\n\n"
            f"They need to attend the next "
            f"**{needed} classes consecutively** "
            f"to reach {MIN_ATTENDANCE:.0f}%."
        )

    # ========================================================
    # HOW MANY CLASSES CAN BE MISSED
    # ========================================================

    if student and (
        "how many can i miss" in q
        or "how many classes can i miss" in q
        or "how many can she miss" in q
        or "how many can he miss" in q
        or "how many more can" in q
    ):

        roll_no = student[0]
        student_name = student[1]

        total, present, absent, percentage = (
            get_student_attendance(
                roll_no
            )
        )

        if total == 0:

            return (
                f"There isn't enough attendance data for "
                f"**{student_name}** yet."
            )

        allowed = maximum_future_absences_at_75(
            present,
            total
        )

        if percentage < MIN_ATTENDANCE:

            return (
                f"**{student_name}** is currently below "
                f"{MIN_ATTENDANCE:.0f}%, so the focus should "
                "be on attending upcoming classes rather "
                "than missing more."
            )

        if allowed == 0:

            return (
                f"**{student_name}** is currently at "
                f"{percentage:.2f}%. To stay at or above "
                f"{MIN_ATTENDANCE:.0f}%, they should not miss "
                "the next class."
            )

        return (
            f"**{student_name}** currently has "
            f"{percentage:.2f}% attendance and can miss "
            f"up to **{allowed} more class(es)** while "
            f"remaining at or above {MIN_ATTENDANCE:.0f}%, "
            "assuming no other attendance changes."
        )

    # ========================================================
    # BELOW 75% / AT RISK
    # ========================================================

    if (
        "below 75" in q
        or "below 75%" in q
        or "less than 75" in q
        or "under 75" in q
        or "at risk" in q
        or "low attendance students" in q
        or "who needs to improve" in q
        or "who need to improve" in q
        or "students at risk" in q
    ):

        risky = [
            s
            for s in summary
            if (
                s["Attendance %"] != "N/A"
                and s["Attendance %"] < MIN_ATTENDANCE
            )
        ]

        if not risky:

            if all(
                s["Total Sessions"] == 0
                for s in summary
            ):

                return (
                    "There are no completed attendance "
                    "sessions yet, so nobody can be classified "
                    "as below 75% at the moment. "
                    "Attendance will be calculated once "
                    "sessions are completed."
                )

            return (
                f"Good news! 😊 No student is currently "
                f"below the {MIN_ATTENDANCE:.0f}% requirement."
            )

        lines = [
            f"⚠️ I found {len(risky)} student(s) "
            f"below the {MIN_ATTENDANCE:.0f}% requirement:"
        ]

        for s in risky:

            lines.append(
                f"• {s['Roll No']} — "
                f"{s['Name']}: "
                f"{s['Attendance %']}%"
            )

        return "\n".join(lines)

    # ========================================================
    # HIGHEST ATTENDANCE
    # ========================================================

    if (
        "highest attendance" in q
        or "best attendance" in q
        or "maximum attendance" in q
        or "who has the highest" in q
        or "who has the best" in q
    ):

        valid = [
            s
            for s in summary
            if s["Total Sessions"] > 0
        ]

        if not valid:

            return (
                "No attendance sessions have been "
                "completed yet, so there is no highest "
                "attendance percentage to compare."
            )

        highest = max(
            valid,
            key=lambda x: x["Attendance %"]
        )

        return (
            f"🏆 **{highest['Name']}** currently has the "
            f"highest attendance at "
            f"**{highest['Attendance %']}%** "
            f"({highest['Roll No']})."
        )

    # ========================================================
    # LOWEST ATTENDANCE
    # ========================================================

    if (
        "lowest attendance" in q
        or "lowest" in q
        or "who has the lowest" in q
        or "worst attendance" in q
        or "minimum attendance among students" in q
    ):

        valid = [
            s
            for s in summary
            if s["Total Sessions"] > 0
        ]

        if not valid:

            return (
                "No attendance sessions have been "
                "completed yet, so there is no lowest "
                "attendance percentage to compare."
            )

        lowest = min(
            valid,
            key=lambda x: x["Attendance %"]
        )

        return (
            f"📉 **{lowest['Name']}** currently has the "
            f"lowest attendance at "
            f"**{lowest['Attendance %']}%** "
            f"({lowest['Roll No']})."
        )

    # ========================================================
    # TODAY'S ABSENT STUDENTS
    # ========================================================

    if (
        "absent today" in q
        or "who is absent today" in q
        or "who are absent today" in q
        or "today absent" in q
    ):

        if not is_working_day():

            return (
                f"Today is a non-working day.\n\n"
                f"Reason: {get_non_working_day_reason()}"
            )

        records = get_today_records(
            SUBJECT
        )

        absent = [
            r
            for r in records
            if r[2] == "Absent"
        ]

        if not absent:

            return (
                "There are no recorded absent students "
                "for today's session yet."
            )

        lines = [
            f"❌ Today's absent students "
            f"({len(absent)}):"
        ]

        for r in absent:

            lines.append(
                f"• {r[0]} — {r[1]}"
            )

        return "\n".join(lines)

    # ========================================================
    # TODAY'S PRESENT STUDENTS
    # ========================================================

    if (
        "present today" in q
        or "who is present today" in q
        or "who are present today" in q
        or "today present" in q
    ):

        if not is_working_day():

            return (
                f"Today is a non-working day.\n\n"
                f"Reason: {get_non_working_day_reason()}"
            )

        records = get_today_records(
            SUBJECT
        )

        present_records = [
            r
            for r in records
            if r[2] == "Present"
        ]

        if not present_records:

            return (
                "There are no recorded present students "
                "for today's session yet."
            )

        lines = [
            f"✅ Today's present students "
            f"({len(present_records)}):"
        ]

        for r in present_records:

            lines.append(
                f"• {r[0]} — {r[1]}"
            )

        return "\n".join(lines)

    # ========================================================
    # TODAY'S SUMMARY
    # ========================================================

    if (
        (
            "today" in q
            or "today's" in q
        )
        and (
            "summary" in q
            or "attendance" in q
            or "present" in q
            or "absent" in q
        )
    ):

        if not is_working_day():

            return (
                f"🏖️ Today is a non-working day.\n\n"
                f"Reason: {get_non_working_day_reason()}\n\n"
                "There is no attendance session today."
            )

        present, absent = (
            get_today_counts(
                SUBJECT
            )
        )

        if present + absent == 0:

            return (
                "Today's attendance session has not "
                "recorded any attendance yet.\n\n"
                f"Total Students: {len(STUDENTS)}\n"
                "Present: 0\n"
                "Absent: Not finalized yet"
            )

        return (
            "📊 Here's today's attendance summary:\n\n"
            f"Total Students: {len(STUDENTS)}\n"
            f"Present: {present}\n"
            f"Absent: {absent}"
        )

    # ========================================================
    # SPECIFIC DATE CALENDAR
    # ========================================================

    if requested_date and (
        "holiday" in q
        or "working" in q
        or "calendar" in q
        or "date" in q
        or "college" in q
    ):

        return calendar_answer_for_date(
            requested_date
        )

    # ========================================================
    # TOMORROW / YESTERDAY / DATE QUESTIONS
    # ========================================================

    if requested_date:

        records = get_records_for_date(
            requested_date,
            SUBJECT
        )

        if records:

            present_count = sum(
                1
                for r in records
                if r[2] == "Present"
            )

            absent_count = sum(
                1
                for r in records
                if r[2] == "Absent"
            )

            return (
                f"📅 Attendance for "
                f"{format_date(requested_date)}:\n\n"
                f"Present: {present_count}\n"
                f"Absent: {absent_count}"
            )

        return calendar_answer_for_date(
            requested_date
        )

    # ========================================================
    # GENERAL HOLIDAY / WORKING DAY
    # ========================================================

    if (
        "working day" in q
        or "holiday" in q
        or "today working" in q
        or "today holiday" in q
        or "is today a holiday" in q
        or "is today working" in q
        or "college today" in q
    ):

        return calendar_answer_for_date(
            today_date()
        )

    # ========================================================
    # ATTENDANCE HISTORY
    # ========================================================

    if student and (
        "history" in q
        or "records" in q
        or "attendance history" in q
    ):

        records = []

        all_records = get_all_attendance()

        for record in all_records:

            if record[0] == student[0]:

                records.append(record)

        if not records:

            return (
                f"There is no attendance history available "
                f"for **{student[1]}** yet."
            )

        lines = [
            f"📚 Attendance history for "
            f"**{student[1]}**:"
        ]

        for record in records:

            lines.append(
                f"• {format_date(record[2])} — "
                f"{record[4]}"
            )

        return "\n".join(lines)

    # ========================================================
    # WHO IS REGISTERED
    # ========================================================

    if (
        "list students" in q
        or "show students" in q
        or "all students" in q
        or "student list" in q
        or "registered list" in q
    ):

        lines = [
            f"Here are all {len(STUDENTS)} registered students:"
        ]

        for index, (roll_no, name) in enumerate(
            STUDENTS,
            start=1
        ):

            lines.append(
                f"{index}. {roll_no} — {name}"
            )

        return "\n".join(lines)

    # ========================================================
    # DATABASE STATUS
    # ========================================================

    if (
        "database" in q
        or "data available" in q
        or "how much data" in q
    ):

        total_records = len(
            get_all_attendance()
        )

        return (
            "SmartAttend currently has:\n\n"
            f"👩‍🎓 Registered students: {len(STUDENTS)}\n"
            f"📚 Attendance records: {total_records}\n"
            f"📊 Minimum attendance: "
            f"{MIN_ATTENDANCE:.0f}%"
        )

    # ========================================================
    # UNKNOWN QUESTION
    # ========================================================

    return None


# ============================================================
# CONVERSATIONAL ASSISTANT RESPONSE
# ============================================================

def assistant_response(question):

    question_lower = question.lower().strip()

    context_student = (
        st.session_state.get(
            "last_student"
        )
    )

    if (
        "tell me about the attendance app" in question_lower
        or "tell me about smartattend" in question_lower
        or "what is smartattend" in question_lower
        or "what is the attendance app" in question_lower
        or "about the attendance system" in question_lower
        or "about the attendance application" in question_lower
    ):

        return (
            "SmartAttend AI is a college attendance management system "
            "designed to make attendance tracking simple, accurate and automated. 🎓🤖\n\n"

            "The system allows registered students to verify their identity "
            "using their roll number and name and mark attendance during the "
            "specified attendance window.\n\n"

            "SmartAttend automatically prevents duplicate attendance for the "
            "same session and records students who do not mark attendance as "
            "Absent when the attendance session is finalized.\n\n"

            "The system also provides:\n\n"
            "• Student attendance tracking\n"
            "• Attendance percentage calculation\n"
            "• 75% minimum attendance monitoring\n"
            "• At-risk student identification\n"
            "• Daily present and absent reports\n"
            "• Complete attendance history\n"
            "• College calendar and holiday information\n"
            "• Automatic attendance finalization\n"
            "• AI-powered attendance assistance\n"
            "• Attendance analysis and insights\n\n"

            "The AI Attendance Assistant can answer questions about students, "
            "attendance, attendance requirements, working days, holidays, "
            "attendance history and other information available in SmartAttend."
        )

    answer = database_answer(
        question,
        context_student
    )

    student = find_student_from_question(
        question
    )

    if student:

        st.session_state[
            "last_student"
        ] = student

    if answer:

        return answer

    return (
        "I can help you with SmartAttend AI. 🤖🎓\n\n"

        "You can ask me about:\n\n"
        "• Student names and roll numbers\n"
        "• Individual attendance\n"
        "• Present and absent students\n"
        "• Attendance percentage\n"
        "• Students below 75%\n"
        "• Highest and lowest attendance\n"
        "• Attendance history\n"
        "• Today's attendance\n"
        "• Holidays and working days\n"
        "• College calendar events\n"
        "• Attendance timing\n"
        "• What happens after 1:15 PM\n"
        "• Attendance risk analysis\n"
        "• How many classes a student needs to attend to reach 75%\n"
        "• Department, year and shift\n"
        "• Registered student information\n\n"

        "Try asking questions such as:\n\n"
        "• What is the attendance requirement?\n"
        "• What time can students mark attendance?\n"
        "• Who is absent today?\n"
        "• Who is below 75% attendance?\n"
        "• Who has the highest attendance?\n"
        "• Is tomorrow a working day?\n"
        "• What happens after 1:15 PM?\n"
        "• Show attendance history for a student.\n\n"

        "You can also ask follow-up questions such as "
        "\"What about that student?\" when student context is available."
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