import streamlit as st

from config import *
from database import *
from calendar_manager import *
from attendance import *
from whatsapp import *
from ai_logic import *
from ui_components import *

# ============================================================
# HOME
# ============================================================

def show_home():
    """Render the home page."""

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
        "☁️ Permanent Supabase cloud attendance database"
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
