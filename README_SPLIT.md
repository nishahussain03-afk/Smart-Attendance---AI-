# SmartAttend AI - Split Project Structure

The original large `app.py` has been separated into focused modules.

- `app.py` - main entry point and page routing
- `config.py` - application configuration, Supabase client, registered students
- `database.py` - Supabase/database and attendance data operations
- `calendar_manager.py` - calendar/holiday helper
- `attendance.py` - attendance operations
- `whatsapp.py` - WhatsApp report/link generation
- `ai_logic.py` - database-aware AI assistant logic
- `ai_assistant.py` - Hugging Face + Groq LLM client
- `ui_components.py` - shared UI/style/table components
- `scheduler.py` - automatic attendance finalization scheduler
- `home.py` - Home page
- `student_portal.py` - Student Portal page
- `admin_dashboard.py` - Admin Dashboard page
- `attendance_register.py` - Attendance Register page
- `ai_attendance_assistant.py` - AI Attendance Assistant page

Keep `.env` in the project root. Do not upload `.env`, `venv/`, SQLite backups, or secrets to GitHub.

Run:

    venv\Scripts\python.exe -m streamlit run app.py
