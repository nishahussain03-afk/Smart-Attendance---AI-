import streamlit as st

from config import *
from database import *
from calendar_manager import *
from attendance import *
from whatsapp import *
from ai_logic import *
from ui_components import *

# ============================================================
# ATTENDANCE_REGISTER
# ============================================================

def show_attendance_register():
    """Render the attendance_register page."""

    st.title("📊 Attendance Register")

    st.caption(
        "Complete student attendance sheet • P = Present • A = Absent • "
        "Holiday = non-working day • - = no finalized record / future date"
    )

    st.info(
        "The register is loaded from the permanent Supabase attendance database. "
        "The default range covers 15-09-2026 to 30-04-2027."
    )

    c1, c2 = st.columns(2)

    with c1:
        register_from = st.date_input(
            "From Date",
            value=datetime(2026, 9, 15).date(),
            min_value=datetime(2026, 9, 15).date(),
            max_value=datetime(2027, 4, 30).date(),
            key="standalone_register_from"
        )

    with c2:
        register_to = st.date_input(
            "To Date",
            value=datetime(2027, 4, 30).date(),
            min_value=datetime(2026, 9, 15).date(),
            max_value=datetime(2027, 4, 30).date(),
            key="standalone_register_to"
        )

    if register_from > register_to:
        st.error("From Date cannot be later than To Date.")
    else:
        register = build_full_attendance_register(
            register_from.isoformat(),
            register_to.isoformat()
        )

        if register:
            st.success(
                f"Showing {len(register)} students from "
                f"{register_from.strftime('%d-%m-%Y')} to "
                f"{register_to.strftime('%d-%m-%Y')}."
            )
            # Use Streamlit's native dataframe renderer instead of a huge
            # custom HTML table. The full register can contain 200+ date
            # columns, and generating one large HTML DOM can make the page
            # appear blank or unresponsive in the browser.
            st.dataframe(
                register,
                use_container_width=True,
                hide_index=True,
                height=650,
            )
        else:
            st.warning("No student or attendance data is available.")


    # ============================================================
    # ADMIN DASHBOARD
    # ============================================================
