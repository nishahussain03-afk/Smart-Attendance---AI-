import streamlit as st

from config import *
from database import *
from calendar_manager import *
from attendance import *
from whatsapp import *
from ai_logic import *
from ui_components import *

# ============================================================
# STUDENT_PORTAL
# ============================================================

def show_student_portal():
    """Render the student_portal page."""

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
    # ATTENDANCE REGISTER
