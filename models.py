# models.py
# type: ignore
# pyright: ignore

from extension import db
from flask_login import UserMixin
from datetime import datetime,date


# ------------------------
# User Roles
# ------------------------
class Role:
    ADMIN = 'admin'
    TEACHER = 'teacher'
    STUDENT = 'student'


# ------------------------
# Users
# ------------------------
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)  # AUTO USER ID
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    transactions = db.relationship('BorrowRecord', backref='user', lazy=True)
    recommendations = db.relationship('BookRecommendation', backref='user', lazy=True)

    # Role helpers
    def is_admin(self):
        return self.role == Role.ADMIN

    def is_teacher(self):
        return self.role == Role.TEACHER

    def is_student(self):
        return self.role == Role.STUDENT


# ------------------------
# Books
# ------------------------
class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)

    isbn = db.Column(db.String(20), unique=True, nullable=True)
    title = db.Column(db.String(150), nullable=True, unique=True)
    author = db.Column(db.String(120), nullable=False)
    publisher = db.Column(db.String(120), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, default=0)
    copies_total = db.Column(db.Integer, nullable=False, default=1)
    copies_available = db.Column(db.Integer, nullable=False, default=1)

    category = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text)

    # ✅ ADD THIS (CRITICAL)
    cover_url = db.Column(db.String(300))

    transactions = db.relationship('BorrowRecord', backref='book', lazy=True)

    __table_args__ = (
        db.UniqueConstraint(
            'title',
            'author',
            'publisher',
            'year',
            'category',
            name='unique_book_details'
        ),
    )




# ------------------------
# Borrow Records
# ------------------------
class BorrowRecord(db.Model):
    __tablename__ = 'borrow_records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)

    borrow_date = db.Column(db.Date, default=date.today)
    due_date = db.Column(db.Date)
    return_date = db.Column(db.Date)

    returned = db.Column(db.Boolean, default=False)
    fine = db.Column(db.Float, default=0.0)

# ------------------------
# Book Recommendations
# ------------------------
class BookRecommendation(db.Model):
    __tablename__ = 'book_recommendations'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    reason = db.Column(db.Text, nullable=False)

    status = db.Column(
        db.String(20),
        default="pending"
    )  # pending | approved | rejected

    date = db.Column(db.DateTime, default=datetime.utcnow)

