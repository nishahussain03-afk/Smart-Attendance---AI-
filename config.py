import os
from datetime import time
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from supabase import create_client

# ============================================================
# CONFIGURATION
# ============================================================

APP_TITLE = "SmartAttend AI"

DEPARTMENT = "B.Sc Computer Science with AI"
YEAR = "2nd Year"
SHIFT = "Shift 2"

MIN_ATTENDANCE = 75.0

ATTENDANCE_START = time(13, 0)
ATTENDANCE_END = time(13, 15)

ADMIN_PASSWORD = "admin123"

CLASS_MAAM_PHONE = "916381494411"
ADMIN_PHONE = "918428800487"

TIMEZONE = ZoneInfo("Asia/Kolkata")

SUBJECT = "Attendance Session"

# ============================================================
# SUPABASE CLOUD DATABASE
# ============================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY are required in .env")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================
# REGISTERED STUDENTS
# ============================================================

STUDENTS = [
    ("E25AI201", "AARTHY V"),
    ("E25AI202", "AFREEN NISHA M"),
    ("E25AI203", "AKSHAYA K"),
    ("E25AI204", "ASENIYA SHINY A"),
    ("E25AI205", "ASWINI S"),
    ("E25AI206", "AYESHA AFROZE M"),
    ("E25AI207", "HARI PRIYA B"),
    ("E25AI208", "BHAVATHARANI T"),
    ("E25AI209", "DEVISREE T"),
    ("E25AI210", "HARINI N"),
    ("E25AI212", "HEMADHARSHINI S"),
    ("E25AI213", "HEMALATHA K"),
    ("E25AI214", "HEMALATHA M"),
    ("E25AI215", "HEMAMALINI S"),
    ("E25AI216", "HUMAIRUL JASHIRA M"),
    ("E25AI217", "JASCINTH RHEMA R"),
    ("E25AI218", "JENITA ROSELIN S"),
    ("E25AI219", "RIYAVALLI K"),
    ("E25AI220", "KAVIYA SHREE V"),
    ("E25AI221", "KEERTHANA P"),
    ("E25AI222", "KEERTHIGA K U"),
    ("E25AI223", "KEERTHIKA M"),
    ("E25AI224", "MADHUMITHA U"),
    ("E25AI225", "MYTHILI K"),
    ("E25AI226", "NANDHINI SRI L V"),
    ("E25AI228", "POOJA SHREE S S"),
    ("E25AI229", "POOJA V"),
    ("E25AI230", "RENUKA DEVI S"),
    ("E25AI231", "SAGI SRUTHI"),
    ("E25AI232", "SANDHIYA R"),
    ("E25AI233", "SHALINI DEVI V"),
    ("E25AI234", "SIBIRAL R"),
    ("E25AI235", "SRUDHYA S"),
    ("E25AI236", "THANSILA BEGAM F"),
    ("E25AI237", "THIRIJA R"),
    ("E25AI238", "VAISHNAVI S"),
    ("E25AI239", "VARALAKSHMI K"),
    ("E25AI240", "YUVASHRI H"),
    ("E25AI241", "DODDI HASINI"),
    ("E25AI242", "RUPA S"),
    ("E25AI243", "MANISHA D"),
    ("E25AI244", "PRIYADARSHINI D"),
    ("E25AI245", "NIVETHITHA D"),
    ("E25AI246", "SNOWFER AMEENA A"),
    ("E25AI247", "LATTIKHASHRI N"),
    ("E25AI248", "PORKODI K"),
    ("E25AI249", "NIKITHA R"),
]
