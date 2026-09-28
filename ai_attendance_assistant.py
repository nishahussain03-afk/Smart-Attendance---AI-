import streamlit as st

from config import *
from database import *
from calendar_manager import *
from attendance import *
from whatsapp import *
from ai_logic import *
from ui_components import *

# ============================================================
# AI_ATTENDANCE_ASSISTANT
# ============================================================

def show_ai_attendance_assistant():
    """Render the ai_attendance_assistant page."""

    st.title(
        "🤖 AI Attendance Assistant"
    )

    st.write(
        "Your conversational assistant for SmartAttend AI."
    )

    st.info(
        "Examples: What is the attendance requirement? • "
        "What time can I mark attendance? • "
        "Who is absent today? • "
        "Explain the attendance rules. • "
        "How does SmartAttend work?"
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
