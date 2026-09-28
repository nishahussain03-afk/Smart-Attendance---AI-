from urllib.parse import quote

from config import *
from database import *

# ============================================================
# WHATSAPP REPORT FUNCTIONS
# ============================================================

def generate_whatsapp_link(
    phone,
    message
):

    return (
        "https://wa.me/"
        + phone
        + "?text="
        + quote(message)
    )


def generate_daily_report():

    date = today_date()

    records = get_today_records(
        SUBJECT
    )

    present = [
        r
        for r in records
        if r[2] == "Present"
    ]

    absent = [
        r
        for r in records
        if r[2] == "Absent"
    ]

    lines = [
        "SMARTATTEND AI - DAILY ATTENDANCE REPORT",
        "",
        f"Department: {DEPARTMENT}",
        f"Year: {YEAR}",
        f"Shift: {SHIFT}",
        f"Date: {date}",
        "",
        f"Total Students: {len(get_all_students())}",
        f"Present: {len(present)}",
        f"Absent: {len(absent)}",
        "",
        "ABSENT STUDENTS:"
    ]

    for record in absent:

        lines.append(
            f"{record[0]} - {record[1]}"
        )

    return "\n".join(lines)
