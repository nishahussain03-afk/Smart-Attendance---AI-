import sqlite3

DB_NAME = "attendance.db"

CALENDAR_DATA = [
    # =========================
    # SEPTEMBER 2026
    # =========================
    ("2026-09-01", "Working", ""),
    ("2026-09-02", "Working", ""),
    ("2026-09-03", "Working", ""),
    ("2026-09-04", "Holiday", "Krishna Jayanthi - Holiday"),
    ("2026-09-05", "Holiday", "Holiday"),
    ("2026-09-06", "Holiday", "Sunday - Holiday"),
    ("2026-09-07", "Working", ""),
    ("2026-09-08", "Working", ""),
    ("2026-09-09", "Working", ""),
    ("2026-09-10", "Working", ""),
    ("2026-09-11", "Working", ""),
    ("2026-09-12", "Holiday", "Holiday"),
    ("2026-09-13", "Holiday", "Sunday - Holiday"),
    ("2026-09-14", "Holiday", "Vinayagar Chathurthi - Holiday"),
    ("2026-09-15", "Working", ""),
    ("2026-09-16", "Working", ""),
    ("2026-09-17", "Working", ""),
    ("2026-09-18", "Working", ""),
    ("2026-09-19", "Holiday", "Saturday - Holiday"),
    ("2026-09-20", "Holiday", "Sunday - Holiday"),
    ("2026-09-21", "Working", ""),
    ("2026-09-22", "Working", ""),
    ("2026-09-23", "Working", ""),
    ("2026-09-24", "Working", ""),
    ("2026-09-25", "Working", "SMRITI"),
    ("2026-09-26", "Holiday", "Saturday - Holiday"),
    ("2026-09-27", "Holiday", "Sunday - Holiday"),
    ("2026-09-28", "Working", ""),
    ("2026-09-29", "Working", ""),
    ("2026-09-30", "Working", ""),

    # =========================
    # OCTOBER 2026
    # =========================
    ("2026-10-01", "Working", ""),
    ("2026-10-02", "Holiday", "Gandhi Jayanthi - Holiday; Daan Utsav Begins"),
    ("2026-10-03", "Holiday", "Saturday - Holiday"),
    ("2026-10-04", "Holiday", "Sunday - Holiday"),
    ("2026-10-05", "Working", ""),
    ("2026-10-06", "Working", ""),
    ("2026-10-07", "Working", ""),
    ("2026-10-08", "Working", "Daan Utsav Ends"),
    ("2026-10-09", "Working", ""),
    ("2026-10-10", "Holiday", "Saturday - Holiday"),
    ("2026-10-11", "Holiday", "Sunday - Holiday"),
    ("2026-10-12", "Working", "CAT II"),
    ("2026-10-13", "Working", "CAT II"),
    ("2026-10-14", "Working", "CAT II"),
    ("2026-10-15", "Working", "CAT II"),
    ("2026-10-16", "Working", "CAT II"),
    ("2026-10-17", "Holiday", "Saturday - Holiday"),
    ("2026-10-18", "Holiday", "Sunday - Holiday"),
    ("2026-10-19", "Holiday", "Ayutha Pooja - Holiday"),
    ("2026-10-20", "Holiday", "Vijaya Dasami - Holiday"),
    ("2026-10-21", "Working", ""),
    ("2026-10-22", "Working", ""),
    ("2026-10-23", "Working", ""),
    ("2026-10-24", "Holiday", "Saturday - Holiday"),
    ("2026-10-25", "Holiday", "Sunday - Holiday"),
    ("2026-10-26", "Working", "ESE - Practical Exam Begins"),
    ("2026-10-27", "Working", ""),
    ("2026-10-28", "Working", ""),
    ("2026-10-29", "Working", ""),
    ("2026-10-30", "Working", ""),
    ("2026-10-31", "Holiday", "Saturday - Holiday"),

    # =========================
    # NOVEMBER 2026
    # =========================
    ("2026-11-01", "Holiday", "Sunday - Holiday"),
    ("2026-11-02", "Working", ""),
    ("2026-11-03", "Working", ""),
    ("2026-11-04", "Working", ""),
    ("2026-11-05", "Working", "ESE - Practical Exam Ends"),
    ("2026-11-06", "Working", ""),
    ("2026-11-07", "Holiday", "Saturday - Holiday"),
    ("2026-11-08", "Holiday", "Sunday - Deepavali - Holiday"),
    ("2026-11-09", "Holiday", "Deepavali Nombu - Holiday"),
    ("2026-11-10", "Holiday", "Gujarathi New Year - Holiday"),
    ("2026-11-11", "Working", ""),
    ("2026-11-12", "Working", "Founder's Day"),
    ("2026-11-13", "Working", ""),
    ("2026-11-14", "Holiday", "Saturday - Holiday; Last working day for I year"),
    ("2026-11-15", "Holiday", "Sunday - Holiday"),
    ("2026-11-16", "Working", "ESE - Theory Exam Begins"),
    ("2026-11-17", "Working", ""),
    ("2026-11-18", "Working", ""),
    ("2026-11-19", "Working", ""),
    ("2026-11-20", "Working", ""),
    ("2026-11-21", "Holiday", "Saturday - Holiday"),
    ("2026-11-22", "Holiday", "Sunday - Holiday"),
    ("2026-11-23", "Working", ""),
    ("2026-11-24", "Working", ""),
    ("2026-11-25", "Working", ""),
    ("2026-11-26", "Working", ""),
    ("2026-11-27", "Working", "ESE - Theory Exam Ends"),
    ("2026-11-28", "Holiday", "Saturday - Holiday"),
    ("2026-11-29", "Holiday", "Sunday - Holiday"),
    ("2026-11-30", "Working", ""),

    # =========================
    # DECEMBER 2026
    # =========================
    ("2026-12-01", "Working", ""),
    ("2026-12-02", "Working", ""),
    ("2026-12-03", "Working", "College Reopens"),
    ("2026-12-04", "Working", ""),
    ("2026-12-05", "Holiday", "Saturday - Holiday"),
    ("2026-12-06", "Holiday", "Sunday - Holiday"),
    ("2026-12-07", "Working", ""),
    ("2026-12-08", "Working", ""),
    ("2026-12-09", "Working", ""),
    ("2026-12-10", "Working", ""),
    ("2026-12-11", "Working", ""),
    ("2026-12-12", "Holiday", "Saturday - Holiday"),
    ("2026-12-13", "Holiday", "Sunday - Holiday"),
    ("2026-12-14", "Working", ""),
    ("2026-12-15", "Working", ""),
    ("2026-12-16", "Working", ""),
    ("2026-12-17", "Working", ""),
    ("2026-12-18", "Working", ""),
    ("2026-12-19", "Holiday", "Saturday - Holiday"),
    ("2026-12-20", "Holiday", "Sunday - Vaikunda Ekathesi"),
    ("2026-12-21", "Working", ""),
    ("2026-12-22", "Working", ""),
    ("2026-12-23", "Working", ""),
    ("2026-12-24", "Working", ""),
    ("2026-12-25", "Holiday", "Christmas - Holiday"),
    ("2026-12-26", "Holiday", "Saturday - Holiday"),
    ("2026-12-27", "Holiday", "Sunday - Holiday"),
    ("2026-12-28", "Working", ""),
    ("2026-12-29", "Working", ""),
    ("2026-12-30", "Working", ""),
    ("2026-12-31", "Working", ""),

    # =========================
    # JANUARY 2027
    # =========================
    ("2027-01-01", "Holiday", "New Year's Day - Holiday"),
    ("2027-01-02", "Holiday", "Saturday - Holiday"),
    ("2027-01-03", "Holiday", "Sunday - Holiday"),
    ("2027-01-04", "Working", ""),
    ("2027-01-05", "Working", ""),
    ("2027-01-06", "Working", ""),
    ("2027-01-07", "Working", ""),
    ("2027-01-08", "Working", ""),
    ("2027-01-09", "Holiday", "Saturday - Holiday; SANDHAI"),
    ("2027-01-10", "Holiday", "Sunday - Holiday"),
    ("2027-01-11", "Working", ""),
    ("2027-01-12", "Working", ""),
    ("2027-01-13", "Working", ""),
    ("2027-01-14", "Working", ""),
    ("2027-01-15", "Holiday", "Pongal - Holiday"),
    ("2027-01-16", "Holiday", "Thiruvalluvar Day - Holiday"),
    ("2027-01-17", "Holiday", "Uzhavar Day - Holiday"),
    ("2027-01-18", "Working", ""),
    ("2027-01-19", "Working", ""),
    ("2027-01-20", "Working", ""),
    ("2027-01-21", "Working", ""),
    ("2027-01-22", "Holiday", "Thai Poosam - Holiday"),
    ("2027-01-23", "Holiday", "Saturday - Holiday"),
    ("2027-01-24", "Holiday", "Sunday - Holiday"),
    ("2027-01-25", "Working", "CAT I"),
    ("2027-01-26", "Holiday", "Republic Day - Holiday"),
    ("2027-01-27", "Working", "CAT I"),
    ("2027-01-28", "Working", "CAT I"),
    ("2027-01-29", "Working", "CAT I"),
    ("2027-01-30", "Holiday", "Saturday - Holiday; CAT I"),
    ("2027-01-31", "Holiday", "Sunday - Holiday"),

    # =========================
    # FEBRUARY 2027
    # =========================
    ("2027-02-01", "Working", ""),
    ("2027-02-02", "Working", ""),
    ("2027-02-03", "Working", ""),
    ("2027-02-04", "Working", ""),
    ("2027-02-05", "Working", ""),
    ("2027-02-06", "Holiday", "Saturday - Holiday"),
    ("2027-02-07", "Holiday", "Sunday - Holiday"),
    ("2027-02-08", "Working", ""),
    ("2027-02-09", "Working", ""),
    ("2027-02-10", "Working", ""),
    ("2027-02-11", "Working", ""),
    ("2027-02-12", "Working", "Sports Day"),
    ("2027-02-13", "Holiday", "Saturday - Holiday"),
    ("2027-02-14", "Holiday", "Sunday - Holiday"),
    ("2027-02-15", "Working", ""),
    ("2027-02-16", "Working", ""),
    ("2027-02-17", "Working", ""),
    ("2027-02-18", "Working", ""),
    ("2027-02-19", "Working", ""),
    ("2027-02-20", "Holiday", "Saturday - Holiday"),
    ("2027-02-21", "Holiday", "Sunday - Holiday"),
    ("2027-02-22", "Working", ""),
    ("2027-02-23", "Working", ""),
    ("2027-02-24", "Working", ""),
    ("2027-02-25", "Working", ""),
    ("2027-02-26", "Working", ""),
    ("2027-02-27", "Holiday", "Saturday - Holiday"),
    ("2027-02-28", "Holiday", "Sunday - Holiday"),

    # =========================
    # MARCH 2027
    # =========================
    ("2027-03-01", "Working", "CAT II"),
    ("2027-03-02", "Working", "CAT II"),
    ("2027-03-03", "Working", "CAT II"),
    ("2027-03-04", "Working", "CAT II"),
    ("2027-03-05", "Working", "CAT II"),
    ("2027-03-06", "Holiday", "Saturday - Holiday"),
    ("2027-03-07", "Holiday", "Sunday - Holiday"),
    ("2027-03-08", "Working", ""),
    ("2027-03-09", "Working", ""),
    ("2027-03-10", "Holiday", "Ramzan - Holiday"),
    ("2027-03-11", "Working", ""),
    ("2027-03-12", "Working", ""),
    ("2027-03-13", "Holiday", "Saturday - Holiday"),
    ("2027-03-14", "Holiday", "Sunday - Holiday"),
    ("2027-03-15", "Working", ""),
    ("2027-03-16", "Working", ""),
    ("2027-03-17", "Working", ""),
    ("2027-03-18", "Working", ""),
    ("2027-03-19", "Working", ""),
    ("2027-03-20", "Holiday", "Saturday - Holiday"),
    ("2027-03-21", "Holiday", "Sunday - Holiday"),
    ("2027-03-22", "Working", "ESE - Practical Exam Begins"),
    ("2027-03-23", "Working", ""),
    ("2027-03-24", "Working", ""),
    ("2027-03-25", "Working", ""),
    ("2027-03-26", "Holiday", "Good Friday - Holiday"),
    ("2027-03-27", "Holiday", "Saturday - Holiday"),
    ("2027-03-28", "Holiday", "Sunday - Holiday"),
    ("2027-03-29", "Working", ""),
    ("2027-03-30", "Working", ""),
    ("2027-03-31", "Working", ""),

    # =========================
    # APRIL 2027
    # =========================
    ("2027-04-01", "Working", ""),
    ("2027-04-02", "Working", ""),
    ("2027-04-03", "Holiday", "Saturday - Holiday; ESE - Practical Exam Ends"),
    ("2027-04-04", "Holiday", "Sunday - Holiday"),
    ("2027-04-05", "Working", ""),
    ("2027-04-06", "Working", ""),
    ("2027-04-07", "Holiday", "Telugu New Year - Holiday"),
    ("2027-04-08", "Working", ""),
    ("2027-04-09", "Working", "Last working day for students"),
    ("2027-04-10", "Holiday", "Saturday - Holiday"),
    ("2027-04-11", "Holiday", "Sunday - Holiday"),
    ("2027-04-12", "Working", ""),
    ("2027-04-13", "Working", ""),
    ("2027-04-14", "Holiday", "Tamil New Year's Day / Dr. B. R. Ambedkar's Birthday"),
    ("2027-04-15", "Working", "ESE - Theory Exam Begins"),
    ("2027-04-16", "Working", ""),
    ("2027-04-17", "Holiday", "Saturday - Holiday"),
    ("2027-04-18", "Holiday", "Sunday - Holiday"),
    ("2027-04-19", "Holiday", "Mahavir Jayanthi - Holiday"),
    ("2027-04-20", "Working", ""),
    ("2027-04-21", "Working", ""),
    ("2027-04-22", "Working", ""),
    ("2027-04-23", "Working", ""),
    ("2027-04-24", "Holiday", "Saturday - Holiday"),
    ("2027-04-25", "Holiday", "Sunday - Holiday"),
    ("2027-04-26", "Working", ""),
    ("2027-04-27", "Working", ""),
    ("2027-04-28", "Working", "ESE - Theory Exam Ends"),
    ("2027-04-29", "Working", ""),
    ("2027-04-30", "Working", ""),
]


def create_calendar_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS college_calendar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            calendar_date TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL,
            description TEXT DEFAULT '',
            academic_year TEXT NOT NULL
        )
    """)
    conn.commit()


def import_calendar(conn):
    inserted = 0
    updated = 0

    for calendar_date, status, description in CALENDAR_DATA:
        existing = conn.execute(
            "SELECT id FROM college_calendar WHERE calendar_date = ?",
            (calendar_date,)
        ).fetchone()

        if existing:
            conn.execute("""
                UPDATE college_calendar
                SET status = ?, description = ?, academic_year = ?
                WHERE calendar_date = ?
            """, (
                status,
                description,
                "2026-2027",
                calendar_date
            ))
            updated += 1
        else:
            conn.execute("""
                INSERT INTO college_calendar
                (calendar_date, status, description, academic_year)
                VALUES (?, ?, ?, ?)
            """, (
                calendar_date,
                status,
                description,
                "2026-2027"
            ))
            inserted += 1

    conn.commit()
    return inserted, updated


def show_summary(conn):
    total = conn.execute(
        "SELECT COUNT(*) FROM college_calendar"
    ).fetchone()[0]

    working = conn.execute(
        "SELECT COUNT(*) FROM college_calendar WHERE status = 'Working'"
    ).fetchone()[0]

    holidays = conn.execute(
        "SELECT COUNT(*) FROM college_calendar WHERE status = 'Holiday'"
    ).fetchone()[0]

    print()
    print("=" * 60)
    print("SMARTATTEND COLLEGE CALENDAR")
    print("=" * 60)
    print(f"Academic Year : 2026-2027")
    print(f"Total Dates   : {total}")
    print(f"Working Dates : {working}")
    print(f"Holiday Dates : {holidays}")
    print("=" * 60)


def main():
    conn = sqlite3.connect(DB_NAME)

    try:
        create_calendar_table(conn)

        inserted, updated = import_calendar(conn)

        print()
        print("CALENDAR IMPORT SUCCESSFUL")
        print("-" * 60)
        print(f"New dates inserted : {inserted}")
        print(f"Existing dates updated : {updated}")

        show_summary(conn)

    finally:
        conn.close()


if __name__ == "__main__":
    main()