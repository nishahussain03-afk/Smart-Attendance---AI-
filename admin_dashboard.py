import streamlit as st

from config import *
from database import *
from calendar_manager import *
from attendance import *
from whatsapp import *
from ai_logic import *
from ui_components import *

# ============================================================
# ADMIN_DASHBOARD
# ============================================================

def show_admin_dashboard():
    """Render the admin_dashboard page."""

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

            render_html_table(
                holiday_table,
                ["Date", "Holiday"]
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
                len(get_all_students())
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

            render_html_table(
                table_data,
                ["Roll No", "Name", "Status", "Marked Time"]
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

        render_html_table(
            summary,
            ["Roll No", "Name", "Total Sessions", "Present", "Absent", "Attendance %", "Risk"]
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
                    render_html_table(matrix)
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

            render_html_table(
                history,
                ["Roll No", "Name", "Date", "Subject", "Status", "Time"]
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
