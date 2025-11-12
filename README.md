# Advanced Library Management System (Flask + MySQL)
Skeleton project for an advanced LMS with roles: Admin, Teacher, Student.

## What's included
- Flask app with blueprint structure (auth, admin, teacher, student)
- SQLAlchemy models for MySQL
- Basic HTML templates (Jinja2)
- Static assets (CSS, JS)
- init_db.sql with schema + sample data
- requirements.txt

## How to run (local)
1. Create a Python venv:
   python3 -m venv venv
   source venv/bin/activate
2. Install requirements:
   pip install -r requirements.txt
3. Create MySQL database and user, then update `config.py` or set env var DATABASE_URL
4. Initialize DB:
   mysql -u root -p < init_db.sql
   or use `flask db` migrations if you add Alembic
5. Run:
   export FLASK_APP=app.py
   export FLASK_ENV=development
   flask run

## Notes
- This is a functional scaffold. Expand features (fine payments, email, search) based on provided models and blueprints.
