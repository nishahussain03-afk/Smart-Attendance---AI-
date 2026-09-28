import streamlit as st
from datetime import datetime

from config import *
from database import (
    current_time,
    today_date,
    format_date,
    get_college_calendar_status,
    is_working_day,
    get_non_working_day_reason,
    supabase,
)

# ============================================================
# CALENDAR / HOLIDAY FUNCTIONS
# ============================================================

# Calendar functions are implemented in database.py.
# This module provides a clean import point for calendar-related code.

def calendar_answer_for_date(date_value):
    working, reason = get_college_calendar_status(date_value)

    date_object = datetime.fromisoformat(date_value)
    day_name = date_object.strftime("%A")

    if working:
        return (
            f"📅 {format_date(date_value)} ({day_name}) is a working day.\n\n"
            f"Calendar information: {reason}"
        )

    return (
        f"🏖️ {format_date(date_value)} ({day_name}) is a holiday/non-working day.\n\n"
        f"Reason: {reason}"
    )
