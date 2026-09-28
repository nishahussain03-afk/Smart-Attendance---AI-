import re
from datetime import datetime

import streamlit as st

from config import *
from database import *
from ai_assistant import ask_smartattend

# ============================================================
# AI ATTENDANCE LOGIC
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
        return len(get_all_students()), present, absent, records

    records = get_today_records(SUBJECT)
    present = sum(1 for r in records if r[2] == "Present")
    absent = sum(1 for r in records if r[2] == "Absent")
    return len(get_all_students()), present, absent, records


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
            f"Total Students: {len(get_all_students())}\n"
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
            f"Total Students: {len(get_all_students())}\n"
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

    rate = len(present) / len(get_all_students()) * 100 if STUDENTS else 0
    return (
        f"📊 **Attendance — {_date_label(date_value)}**\n\n"
        f"Total Students: {len(get_all_students())}\n"
        f"Present: {len(present)}\n"
        f"Absent: {len(absent)}\n"
        f"Attendance Rate: **{rate:.2f}%**\n\n"
        "Ask **who was present** or **who was absent** if you want the complete list."
    )


def _history_matrix_data(start_date=None, end_date=None):
    try:
        result = (
            supabase
            .table("attendance")
            .select("attendance_date")
            .eq("subject", SUBJECT)
            .order("attendance_date")
            .execute()
        )
        dates = sorted({
            str(row["attendance_date"])
            for row in (result.data or [])
        })
    except Exception as e:
        st.error(f"Unable to load attendance dates from Supabase: {e}")
        return []

    if start_date:
        dates = [d for d in dates if d >= start_date]
    if end_date:
        dates = [d for d in dates if d <= end_date]

    return dates


def build_attendance_matrix(start_date=None, end_date=None):
    dates = _history_matrix_data(
        start_date,
        end_date
    )

    if not dates:
        return []

    try:
        result = (
            supabase
            .table("attendance")
            .select("roll_no, attendance_date, status")
            .eq("subject", SUBJECT)
            .execute()
        )
        rows = result.data or []
    except Exception as e:
        st.error(f"Unable to build attendance register: {e}")
        return []

    lookup = {}

    for row in rows:
        attendance_date = str(row["attendance_date"])
        if attendance_date in dates:
            lookup[(row["roll_no"], attendance_date)] = (
                "P"
                if row["status"] == "Present"
                else "A"
            )

    matrix = []

    for roll_no, name in get_all_students():
        row = {
            "Roll No": roll_no,
            "Name": name
        }

        for d in dates:
            row[_date_label(d)] = lookup.get(
                (roll_no, d),
                "-"
            )

        completed = [
            lookup.get((roll_no, d))
            for d in dates
            if lookup.get((roll_no, d))
        ]

        if completed:
            p_count = completed.count("P")
            row["Attendance %"] = round(
                p_count / len(completed) * 100,
                2
            )
        else:
            row["Attendance %"] = None

        matrix.append(row)

    return matrix


def _llm_fallback(question, context_student=None):
    """Use Hugging Face + Groq for natural-language answers.

    Database-specific answers are handled first by database_answer().
    The LLM only receives summarized application context and must not
    invent attendance facts.
    """
    try:
        today = today_date()
        total, present, absent, records = _get_class_stats()

        context = {
            "application": "SmartAttend AI",
            "department": DEPARTMENT,
            "year": YEAR,
            "shift": SHIFT,
            "minimum_attendance": MIN_ATTENDANCE,
            "attendance_window": "1:00 PM to 1:15 PM",
            "registered_students": len(get_all_students()),
            "today": today,
            "today_is_working_day": is_working_day(today),
            "today_reason": (
                get_non_working_day_reason(today)
                if not is_working_day(today)
                else "Working Day"
            ),
            "today_present": present,
            "today_absent": absent,
            "today_records_available": bool(records),
            "context_student": context_student,
        }

        prompt = (
            "Answer the user's question using only the SmartAttend context below. "
            "Never invent student names, attendance records, dates, percentages, or rules. "
            "If the requested database fact is not supplied, say it is not available. "
            "Keep the response concise and student-friendly.\n\n"
            f"APPLICATION CONTEXT:\n{context}\n\n"
            f"USER QUESTION:\n{question}"
        )

        return ask_smartattend(prompt)

    except Exception as e:
        print("SmartAttend AI fallback error:", e)
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
            f"👩‍🎓 Registered Students: {len(get_all_students())}\n"
            f"📊 Minimum Attendance: {MIN_ATTENDANCE:.0f}%\n"
            "⏰ Attendance Window: 1:00 PM–1:15 PM"
        )

    if any(x in q for x in ["how many students", "total students", "number of students", "registered students"]):
        return f"There are **{len(get_all_students())} registered students** in SmartAttend."

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
        return f"🗄️ **SmartAttend Data Status**\n\nRegistered students: {len(get_all_students())}\nAttendance records: {total_records}\nMinimum attendance: {MIN_ATTENDANCE:.0f}%"

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


def build_full_attendance_register(start_date="2026-09-15", end_date="2027-04-30"):
    """Build the complete attendance register with bulk Supabase reads."""

    start = datetime.fromisoformat(start_date).date()
    end = datetime.fromisoformat(end_date).date()

    if start > end:
        return []

    # Build the date range locally.
    dates = []
    current = start
    while current <= end:
        dates.append(current.isoformat())
        current += timedelta(days=1)

    try:
        # ------------------------------------------------------------
        # IMPORTANT PERFORMANCE FIX:
        # Load each required dataset ONCE instead of making a
        # Supabase request for every date/student combination.
        # ------------------------------------------------------------

        students = get_all_students()

        attendance_result = (
            supabase
            .table("attendance")
            .select("roll_no, attendance_date, status")
            .eq("subject", SUBJECT)
            .gte("attendance_date", start_date)
            .lte("attendance_date", end_date)
            .execute()
        )
        attendance_rows = attendance_result.data or []

        calendar_result = (
            supabase
            .table("college_calendar")
            .select("calendar_date, status, description")
            .gte("calendar_date", start_date)
            .lte("calendar_date", end_date)
            .execute()
        )
        calendar_rows = calendar_result.data or []

        holiday_result = (
            supabase
            .table("holidays")
            .select("holiday_date")
            .gte("holiday_date", start_date)
            .lte("holiday_date", end_date)
            .execute()
        )
        holiday_rows = holiday_result.data or []

    except Exception as e:
        st.error(f"Unable to load attendance register from Supabase: {e}")
        return []

    # Fast in-memory lookups.
    attendance_lookup = {}
    for row in attendance_rows:
        date_value = str(row.get("attendance_date"))[:10]
        attendance_lookup[(row.get("roll_no"), date_value)] = (
            "P" if row.get("status") == "Present" else "A"
        )

    calendar_lookup = {
        str(row.get("calendar_date"))[:10]: row.get("status", "Working")
        for row in calendar_rows
    }

    holiday_dates = {
        str(row.get("holiday_date"))[:10]
        for row in holiday_rows
    }

    today = current_time().date()
    matrix = []

    for roll_no, name in students:
        row = {"Roll No": roll_no, "Name": name}
        completed = []

        for date_value in dates:
            date_obj = datetime.fromisoformat(date_value).date()
            label = _date_label(date_value)
            value = attendance_lookup.get((roll_no, date_value))

            if value:
                row[label] = value
                completed.append(value)
            else:
                # Saturdays and Sundays are always holidays.
                if date_obj.weekday() in (5, 6):
                    row[label] = "Holiday"
                # College calendar has priority for Monday-Friday.
                elif calendar_lookup.get(date_value, "Working").lower() == "holiday":
                    row[label] = "Holiday"
                elif date_value in holiday_dates:
                    row[label] = "Holiday"
                elif date_obj > today:
                    row[label] = "-"
                else:
                    row[label] = "-"

        if completed:
            row["Attendance %"] = round(
                completed.count("P") / len(completed) * 100,
                2
            )
        else:
            row["Attendance %"] = None

        matrix.append(row)

    return matrix

