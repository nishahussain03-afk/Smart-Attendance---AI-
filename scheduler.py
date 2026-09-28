import streamlit as st
from apscheduler.schedulers.background import BackgroundScheduler

from database import automatic_finalize_attendance

@st.cache_resource
def start_attendance_scheduler():
    scheduler = BackgroundScheduler(timezone="Asia/Kolkata")

    scheduler.add_job(
        automatic_finalize_attendance,
        trigger="cron",
        hour=13,
        minute=15,
        id="daily_attendance_finalization",
        replace_existing=True
    )

    scheduler.start()
    return scheduler
