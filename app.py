import streamlit as st

from config import APP_TITLE
from database import initialize_database
from scheduler import start_attendance_scheduler
from ui_components import apply_custom_style, show_today_status, show_sidebar

from home import show_home
from student_portal import show_student_portal
from admin_dashboard import show_admin_dashboard
from attendance_register import show_attendance_register
from ai_attendance_assistant import show_ai_attendance_assistant

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🎓",
    layout="wide"
)

# ============================================================
# DATABASE INITIALIZATION
# ============================================================

initialize_database()

try:
    from config import supabase
    supabase.table("students").select("roll_no").limit(1).execute()
except Exception as e:
    st.error(
        "Supabase connection failed. Check your .env values and "
        f"Supabase table permissions. Details: {e}"
    )
    st.stop()

# ============================================================
# AUTOMATIC ATTENDANCE SCHEDULER
# ============================================================

start_attendance_scheduler()

# ============================================================
# COMMON UI
# ============================================================

apply_custom_style()
show_today_status()

page = show_sidebar()

# ============================================================
# PAGE ROUTING
# ============================================================

if page == "🏠 Home":
    show_home()

elif page == "🎓 Student Portal":
    show_student_portal()

elif page == "🔐 Admin Dashboard":
    show_admin_dashboard()

elif page == "📊 Attendance Register":
    show_attendance_register()

elif page == "🤖 AI Attendance Assistant":
    show_ai_attendance_assistant()
