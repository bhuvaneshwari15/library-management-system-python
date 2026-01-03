# type: ignore
# pyright: ignore

import os
from urllib.parse import quote_plus

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# ================= DATABASE =================
# MySQL connection (password safely encoded if needed)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:admin123@localhost/library_db"
)

# ================= SECURITY =================
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

# ================= FILE UPLOADS =================
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB max upload

# ================= FLASK SETTINGS =================
DEBUG = True

# ================= ENSURE UPLOAD DIR EXISTS =================
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
