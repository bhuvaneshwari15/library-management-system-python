# init_db.py
# type: ignore
# pyright: ignore

from app import create_app
from extension import db
from models import *

app = create_app()

with app.app_context():
    db.create_all()
    print("✅ All tables created successfully!")
