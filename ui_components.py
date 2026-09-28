import streamlit as st
from html import escape

from config import *
from database import *

# ============================================================
# COMMON UI COMPONENTS
# ============================================================

def apply_custom_style():
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

def show_today_status():
    today = today_date()

    if not is_working_day(today):
        reason = get_non_working_day_reason(today)

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

def show_sidebar():
    st.sidebar.title("🎓 SmartAttend AI")
    st.sidebar.write(f"**{DEPARTMENT}**")
    st.sidebar.write(f"**{YEAR} • {SHIFT}**")

    page = st.sidebar.radio(
        "Navigation",
        [
            "🏠 Home",
            "🎓 Student Portal",
            "🔐 Admin Dashboard",
            "📊 Attendance Register",
            "🤖 AI Attendance Assistant"
        ]
    )

    st.sidebar.divider()

    st.sidebar.info(
        "Attendance Window\n\n"
        "1:00 PM – 1:15 PM\n\n"
        "Minimum Attendance: 75%"
    )

    return page

def render_html_table(data, columns=None):
    if not data:
        return

    if columns is None:
        columns = list(data[0].keys())

    parts = [
        '<div style="overflow-x:auto; width:100%;">',
        '<table style="width:100%; border-collapse:collapse; font-size:14px;">',
        '<thead><tr>'
    ]

    for column in columns:
        parts.append(
            '<th style="padding:10px; border:1px solid #ddd; '
            'text-align:left; font-weight:700;">'
            + escape(str(column))
            + '</th>'
        )

    parts.append('</tr></thead><tbody>')

    for row in data:
        parts.append('<tr>')
        for column in columns:
            value = row.get(column, "")
            if value is None:
                value = ""
            parts.append(
                '<td style="padding:10px; border:1px solid #ddd; '
                'text-align:left;">'
                + escape(str(value))
                + '</td>'
            )
        parts.append('</tr>')

    parts.append('</tbody></table></div>')
    st.html("".join(parts))
