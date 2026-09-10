import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, time
from zoneinfo import ZoneInfo
from urllib.parse import quote

try:
    from transformers import pipeline
except Exception:
    pipeline = None

st.set_page_config(
    page_title="SmartAttend AI",
    page_icon="🎓",
    layout="wide"
)

DB_FILE = "attendance.db"

IST = ZoneInfo("Asia/Kolkata")

ATTENDANCE_START = time(13, 0)
ATTENDANCE_END = time(13, 15)

MIN_ATTENDANCE = 75.0

CLASS_MAAM_NUMBER = "916381494411"
ADMIN_NUMBER = "918428800487"

DEPARTMENT = "B.Sc Computer Science with AI"
SHIFT = "Shift 2"
YEAR = "2nd Year"

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
    ("E25AI249", "NIKITHA R")
]

TIMETABLE = {
    "Monday": "Attendance Session",
    "Tuesday": "Attendance Session",
    "Wednesday": "Attendance Session",
    "Thursday": "Attendance Session",
    "Friday": "Attendance Session",
    "Saturday": "Attendance Session"
}


def get_now():
    return datetime.now(IST)


def normalize(value):
    return " ".join(str(value).strip().upper().split())


def get_subject():
    day = get_now().strftime("%A")
    return TIMETABLE.get(day, "Attendance Session")


def db_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


def init_db():
    conn = db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            roll_no TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT NOT NULL,
            attendance_date TEXT NOT NULL,
            subject TEXT NOT NULL,
            status TEXT NOT NULL,
            marked_time TEXT NOT NULL,
            UNIQUE(roll_no, attendance_date, subject)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attendance_date TEXT NOT NULL,
            subject TEXT NOT NULL,
            generated_time TEXT NOT NULL,
            present_count INTEGER NOT NULL,
            absent_count INTEGER NOT NULL,
            UNIQUE(attendance_date, subject)
        )
    """)

    cursor.executemany(
        "INSERT OR IGNORE INTO students (roll_no, name) VALUES (?, ?)",
        STUDENTS
    )

    conn.commit()
    conn.close()


def verify_student(roll_no, name):
    roll_no = normalize(roll_no)
    name = normalize(name)

    conn = db_connection()

    student = conn.execute(
        "SELECT roll_no, name FROM students WHERE roll_no = ?",
        (roll_no,)
    ).fetchone()

    conn.close()

    if student is None:
        return False, None

    if normalize(student[1]) != name:
        return False, None

    return True, student


def check_existing_attendance(roll_no, date_value, subject):
    conn = db_connection()

    result = conn.execute(
        """
        SELECT status, marked_time
        FROM attendance
        WHERE roll_no = ?
        AND attendance_date = ?
        AND subject = ?
        """,
        (roll_no, date_value, subject)
    ).fetchone()

    conn.close()

    return result


def mark_attendance(roll_no, date_value, subject):
    now = get_now()

    conn = db_connection()

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
                date_value,
                subject,
                "Present",
                now.strftime("%H:%M:%S")
            )
        )

        conn.commit()
        success = True

    except sqlite3.IntegrityError:
        success = False

    conn.close()

    return success


def get_attendance_window_status():
    current_time = get_now().time()

    if current_time < ATTENDANCE_START:
        return "before"

    if ATTENDANCE_START <= current_time <= ATTENDANCE_END:
        return "open"

    return "closed"


def get_today_attendance(date_value, subject):
    conn = db_connection()

    df = pd.read_sql_query(
        """
        SELECT
            s.roll_no,
            s.name,
            COALESCE(a.status, 'Absent') AS status,
            a.marked_time
        FROM students s
        LEFT JOIN attendance a
        ON s.roll_no = a.roll_no
        AND a.attendance_date = ?
        AND a.subject = ?
        ORDER BY s.roll_no
        """,
        conn,
        params=(date_value, subject)
    )

    conn.close()

    return df


def get_all_attendance():
    conn = db_connection()

    df = pd.read_sql_query(
        """
        SELECT
            a.attendance_date,
            a.subject,
            a.roll_no,
            s.name,
            a.status,
            a.marked_time
        FROM attendance a
        JOIN students s
        ON s.roll_no = a.roll_no
        ORDER BY
            a.attendance_date DESC,
            a.subject,
            a.roll_no
        """,
        conn
    )

    conn.close()

    return df


def get_attendance_summary():
    students_df = pd.DataFrame(
        STUDENTS,
        columns=["roll_no", "name"]
    )

    attendance_df = get_all_attendance()

    if attendance_df.empty:
        students_df["present"] = 0
        students_df["total_sessions"] = 0
        students_df["percentage"] = 0.0

        return students_df

    sessions = attendance_df[
        ["attendance_date", "subject"]
    ].drop_duplicates()

    total_sessions = len(sessions)

    present_counts = (
        attendance_df[
            attendance_df["status"] == "Present"
        ]
        .groupby("roll_no")
        .size()
        .rename("present")
    )

    students_df["present"] = (
        students_df["roll_no"]
        .map(present_counts)
        .fillna(0)
        .astype(int)
    )

    students_df["total_sessions"] = total_sessions

    if total_sessions > 0:
        students_df["percentage"] = (
            students_df["present"]
            / total_sessions
            * 100
        )
    else:
        students_df["percentage"] = 0.0

    return students_df


def generate_report(date_value, subject):
    df = get_today_attendance(
        date_value,
        subject
    )

    present = df[
        df["status"] == "Present"
    ]

    absent = df[
        df["status"] == "Absent"
    ]

    percentage = (
        len(present) / len(df) * 100
        if len(df) > 0
        else 0
    )

    report = []

    report.append(
        "SMARTATTEND AI - DAILY ATTENDANCE REPORT"
    )

    report.append("")

    report.append(f"Date: {date_value}")
    report.append(f"Subject/Session: {subject}")
    report.append(f"Department: {DEPARTMENT}")
    report.append(f"Year: {YEAR}")
    report.append(f"Shift: {SHIFT}")

    report.append("")

    report.append(
        f"Total Students: {len(df)}"
    )

    report.append(
        f"Present: {len(present)}"
    )

    report.append(
        f"Absent: {len(absent)}"
    )

    report.append(
        f"Attendance Percentage: {percentage:.2f}%"
    )

    report.append("")

    report.append("PRESENT STUDENTS:")

    if present.empty:
        report.append("None")
    else:
        for _, row in present.iterrows():
            report.append(
                f"{row['roll_no']} - {row['name']}"
            )

    report.append("")

    report.append("ABSENT STUDENTS:")

    if absent.empty:
        report.append("None")
    else:
        for _, row in absent.iterrows():
            report.append(
                f"{row['roll_no']} - {row['name']}"
            )

    return "\n".join(report), df


def save_session_report(date_value, subject):
    if get_now().time() <= ATTENDANCE_END:
        return

    df = get_today_attendance(
        date_value,
        subject
    )

    present_count = int(
        (df["status"] == "Present").sum()
    )

    absent_count = int(
        (df["status"] == "Absent").sum()
    )

    conn = db_connection()

    conn.execute(
        """
        INSERT OR REPLACE INTO session_reports
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
            date_value,
            subject,
            get_now().strftime("%H:%M:%S"),
            present_count,
            absent_count
        )
    )

    conn.commit()
    conn.close()


def create_whatsapp_link(number, message):
    return (
        f"https://wa.me/{number}"
        f"?text={quote(message)}"
    )


@st.cache_resource(show_spinner=False)
def load_ai_model():
    if pipeline is None:
        return None

    try:
        model = pipeline(
            "text-generation",
            model="HuggingFaceTB/SmolLM2-360M-Instruct"
        )

        return model

    except Exception:
        return None


def generate_ai_insight(summary_df):
    below_75 = summary_df[
        summary_df["percentage"] < MIN_ATTENDANCE
    ]

    warning_students = summary_df[
        (summary_df["percentage"] >= MIN_ATTENDANCE)
        &
        (summary_df["percentage"] < MIN_ATTENDANCE + 10)
    ]

    total_students = len(summary_df)

    if total_students == 0:
        return "No attendance data available."

    basic_analysis = (
        f"There are {total_students} registered students. "
        f"{len(below_75)} students are below "
        f"{MIN_ATTENDANCE:.0f}% attendance. "
        f"{len(warning_students)} students are close to the "
        f"minimum attendance requirement."
    )

    if len(below_75) > 0:
        names = ", ".join(
            below_75["name"].head(8).tolist()
        )

        basic_analysis += (
            f" Students needing immediate attention include "
            f"{names}."
        )

    else:
        basic_analysis += (
            " No student is currently below the minimum attendance requirement."
        )

    model = load_ai_model()

    if model is None:
        return (
            basic_analysis
            + " Regular attendance monitoring is recommended."
        )

    prompt = (
        "You are an AI college attendance analyst. "
        "Analyze the following attendance situation and give "
        "a short professional recommendation. "
        + basic_analysis
    )

    try:
        result = model(
            prompt,
            max_new_tokens=100,
            do_sample=True,
            temperature=0.4
        )

        generated = result[0]["generated_text"]

        if generated.startswith(prompt):
            generated = generated[len(prompt):]

        return generated.strip()

    except Exception:
        return (
            basic_analysis
            + " Regular attendance monitoring is recommended."
        )


def home_page():
    st.title("🎓 SmartAttend AI")

    st.subheader(
        "AI-Powered College Attendance Management "
        "& Risk Prediction System"
    )

    st.write(
        "SmartAttend AI is a smart college attendance platform "
        "that allows students to verify themselves and mark "
        "attendance during a fixed time window. "
        "Administrators can monitor attendance, generate daily "
        "reports and identify students at attendance risk."
    )

    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Registered Students",
        len(STUDENTS)
    )

    col2.metric(
        "Minimum Attendance",
        "75%"
    )

    col3.metric(
        "Attendance Time",
        "1:00–1:15 PM"
    )

    col4.metric(
        "Department",
        "CS + AI"
    )

    st.markdown("---")

    st.subheader("✨ Main Features")

    features = [
        "Student login using Roll Number and Name",
        "Student verification using registered data",
        "Attendance available only from 1:00 PM to 1:15 PM",
        "One attendance entry per student per session",
        "Students cannot manually select Absent",
        "Students who do not mark attendance become Absent",
        "Daily Present and Absent report",
        "WhatsApp report option for Class Ma'am",
        "WhatsApp report option for Admin",
        "SQLite database for persistent attendance storage",
        "75% attendance risk analysis",
        "AI-generated attendance insights",
        "CSV attendance history download"
    ]

    for feature in features:
        st.write("✅ " + feature)

    st.markdown("---")

    st.info(
        "Department: B.Sc Computer Science with AI | "
        "Year: 2nd Year | Shift: Shift 2"
    )


def student_portal():
    st.title("🎓 Student Attendance Portal")

    st.write(
        f"**{DEPARTMENT} | {YEAR} | {SHIFT}**"
    )

    now = get_now()

    date_value = now.strftime("%Y-%m-%d")
    subject = get_subject()

    status = get_attendance_window_status()

    st.info(
        f"📚 Current Session: **{subject}**\n\n"
        f"🕐 Attendance Window: **1:00 PM - 1:15 PM IST**"
    )

    if status == "before":

        st.warning(
            "⏳ Attendance is not open yet. "
            "It will open at 1:00 PM."
        )

    elif status == "open":

        st.success(
            "🟢 Attendance is OPEN. "
            "You can mark your attendance now."
        )

    else:

        st.error(
            "🔴 Attendance window is CLOSED. "
            "Students who did not mark attendance "
            "during the allowed time are considered Absent."
        )

    st.markdown("---")

    st.subheader("Student Verification")

    with st.form("student_login_form"):

        roll_no = st.text_input(
            "Roll Number",
            placeholder="Example: E25AI202"
        )

        name = st.text_input(
            "Name",
            placeholder="Enter your registered full name"
        )

        submit = st.form_submit_button(
            "Verify & Mark Attendance",
            type="primary"
        )

    if submit:

        valid, student = verify_student(
            roll_no,
            name
        )

        if not valid:

            st.error(
                "❌ Verification failed. "
                "Please check your Roll Number and Name."
            )

            return

        st.success(
            f"Student verified: {student[1]}"
        )

        if status == "before":

            st.warning(
                "Attendance is not open yet. "
                "Please return between 1:00 PM and 1:15 PM."
            )

            return

        if status == "closed":

            st.error(
                "Attendance time is over. "
                "You cannot mark attendance now."
            )

            return

        existing = check_existing_attendance(
            student[0],
            date_value,
            subject
        )

        if existing:

            st.warning(
                "⚠️ Attendance already marked for "
                "this session."
            )

            st.info(
                f"Marked at: {existing[1]}"
            )

            return

        success = mark_attendance(
            student[0],
            date_value,
            subject
        )

        if success:

            st.success(
                f"✅ Attendance marked successfully for "
                f"{student[1]}!"
            )

            st.info(
                f"Time: {get_now().strftime('%I:%M:%S %p')}"
            )

            st.balloons()

        else:

            st.warning(
                "⚠️ Attendance was already marked "
                "for this session."
            )


def admin_dashboard():
    st.title("📊 Admin Dashboard")

    now = get_now()

    date_value = now.strftime("%Y-%m-%d")
    subject = get_subject()

    today_df = get_today_attendance(
        date_value,
        subject
    )

    save_session_report(
        date_value,
        subject
    )

    present_count = int(
        (today_df["status"] == "Present").sum()
    )

    absent_count = int(
        (today_df["status"] == "Absent").sum()
    )

    attendance_percentage = (
        present_count
        / len(today_df)
        * 100
        if len(today_df) > 0
        else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Students",
        len(today_df)
    )

    col2.metric(
        "Present",
        present_count
    )

    col3.metric(
        "Absent",
        absent_count
    )

    col4.metric(
        "Today's Attendance",
        f"{attendance_percentage:.1f}%"
    )

    st.info(
        f"📚 Session: {subject} | "
        f"🕐 Attendance Window: 1:00 PM - 1:15 PM IST"
    )

    st.markdown("---")

    st.subheader("📋 Today's Attendance")

    display_df = today_df.copy()

    display_df["status"] = display_df[
        "status"
    ].replace(
        {
            "Present": "🟢 Present",
            "Absent": "🔴 Absent"
        }
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    report, _ = generate_report(
        date_value,
        subject
    )

    st.subheader("📱 Daily Attendance Report")

    st.text_area(
        "Generated Report",
        report,
        height=400
    )

    col1, col2, col3 = st.columns(3)

    col1.link_button(
        "📱 Send to Class Ma'am",
        create_whatsapp_link(
            CLASS_MAAM_NUMBER,
            report
        )
    )

    col2.link_button(
        "📱 Send to Admin",
        create_whatsapp_link(
            ADMIN_NUMBER,
            report
        )
    )

    col3.download_button(
        "⬇️ Download Report",
        report,
        file_name=f"attendance_{date_value}.txt",
        mime="text/plain"
    )

    st.markdown("---")

    st.subheader(
        "🤖 AI Attendance Risk Analysis"
    )

    summary = get_attendance_summary()

    risk_df = summary.copy()

    risk_df["Risk Level"] = risk_df[
        "percentage"
    ].apply(
        lambda percentage:
        "🔴 Critical"
        if percentage < MIN_ATTENDANCE
        else
        "🟠 Warning"
        if percentage < MIN_ATTENDANCE + 10
        else
        "🟢 Safe"
    )

    risk_df = risk_df.sort_values(
        "percentage"
    )

    st.dataframe(
        risk_df,
        use_container_width=True,
        hide_index=True
    )

    below_75 = risk_df[
        risk_df["percentage"] < MIN_ATTENDANCE
    ]

    warning = risk_df[
        (risk_df["percentage"] >= MIN_ATTENDANCE)
        &
        (risk_df["percentage"] < MIN_ATTENDANCE + 10)
    ]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Below 75%",
        len(below_75)
    )

    col2.metric(
        "Warning Zone",
        len(warning)
    )

    col3.metric(
        "Safe Students",
        len(risk_df) - len(below_75) - len(warning)
    )

    if not below_75.empty:

        st.error(
            f"⚠️ {len(below_75)} student(s) "
            f"are below the required 75% attendance."
        )

    else:

        st.success(
            "✅ All students are currently "
            "at or above 75% attendance."
        )

    if st.button(
        "🤖 Generate AI Attendance Insights"
    ):

        with st.spinner(
            "AI is analyzing attendance data..."
        ):

            insight = generate_ai_insight(
                summary
            )

            st.success(insight)

    st.markdown("---")

    st.subheader(
        "📚 Complete Attendance History"
    )

    history = get_all_attendance()

    if history.empty:

        st.info(
            "No attendance history available yet."
        )

    else:

        st.dataframe(
            history,
            use_container_width=True,
            hide_index=True
        )

        csv_data = history.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "⬇️ Download Full Attendance CSV",
            csv_data,
            file_name="smartattend_attendance_history.csv",
            mime="text/csv"
        )


init_db()

st.sidebar.title("🎓 SmartAttend AI")

page = st.sidebar.radio(
    "Select Portal",
    [
        "🏠 Home",
        "🎓 Student Portal",
        "📊 Admin Dashboard"
    ]
)

st.sidebar.markdown("---")

st.sidebar.write(
    f"**Department:** {DEPARTMENT}"
)

st.sidebar.write(
    f"**Year:** {YEAR}"
)

st.sidebar.write(
    f"**Shift:** {SHIFT}"
)

st.sidebar.write(
    f"**Minimum Attendance:** {MIN_ATTENDANCE:.0f}%"
)

st.sidebar.write(
    "**Attendance:** 1:00 PM - 1:15 PM"
)

st.sidebar.markdown("---")

st.sidebar.caption(
    "SmartAttend AI | College Attendance Management System"
)

if page == "🏠 Home":

    home_page()

elif page == "🎓 Student Portal":

    student_portal()

else:

    admin_dashboard()