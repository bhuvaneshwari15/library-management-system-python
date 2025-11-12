import os
from urllib.parse import quote_plus

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Correct MySQL connection URL (with encoded password)
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'mysql+pymysql://root:admin%40123@localhost/library_db'
)

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
