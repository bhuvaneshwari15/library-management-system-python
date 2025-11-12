# blueprints/student.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from models import Role, Book, BorrowRecord
from extension import db
from datetime import datetime, timedelta, timezone

# ----------------------------
# Blueprint
# ----------------------------
student_bp = Blueprint(
    'student', __name__,
    url_prefix='/student',
    template_folder='templates/student'
)

# ----------------------------
# Student role decorator
# ----------------------------
def student_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != Role.STUDENT:
            flash('Student access only', 'danger')
            return redirect(url_for('auth.login'))
        return fn(*args, **kwargs)
    return wrapper

# ----------------------------
# Dashboard
# ----------------------------
@student_bp.route('/')
@login_required
@student_required
def dashboard():
    total_books = Book.query.count()
    borrowed_books = BorrowRecord.query.filter_by(user_id=current_user.id, returned=False).count()
    overdue_books = BorrowRecord.query.filter(
        BorrowRecord.user_id == current_user.id,
        BorrowRecord.due_date < datetime.now(timezone.utc),
        BorrowRecord.returned == False
    ).count()

    return render_template('student/dashboard.html',
                           total_books=total_books,
                           borrowed_books=borrowed_books,
                           overdue_books=overdue_books)

# ----------------------------
# View all books
# ----------------------------
@student_bp.route('/books')
@login_required
@student_required
def books():
    query = request.args.get('q', '')
    if query:
        books = Book.query.filter(
            (Book.title.ilike(f'%{query}%')) |
            (Book.author.ilike(f'%{query}%')) |
            (Book.category.ilike(f'%{query}%'))
        ).all()
    else:
        books = Book.query.all()
    return render_template('student/books.html', books=books, query=query)

# ----------------------------
# Borrow a book
# ----------------------------
@student_bp.route('/books/borrow/<int:book_id>')
@login_required
@student_required
def borrow_book(book_id):
    book = Book.query.get_or_404(book_id)

    if book.copies_available <= 0:
        flash('Book not available for borrowing!', 'danger')
        return redirect(url_for('student.books'))

    existing = BorrowRecord.query.filter_by(
        user_id=current_user.id,
        book_id=book_id,
        returned=False
    ).first()
    if existing:
        flash('You already borrowed this book!', 'warning')
        return redirect(url_for('student.books'))

    now_utc = datetime.now(timezone.utc)
    borrow = BorrowRecord(
        user_id=current_user.id,
        book_id=book.id,
        borrow_date=now_utc,
        due_date=now_utc + timedelta(days=7),
        returned=False
    )
    book.copies_available -= 1
    db.session.add(borrow)
    db.session.commit()

    flash('Book borrowed successfully!', 'success')
    return redirect(url_for('student.borrowed_books'))

# ----------------------------
# Return a book
# ----------------------------
@student_bp.route('/books/return/<int:record_id>')
@login_required
@student_required
def return_book(record_id):
    record = BorrowRecord.query.get_or_404(record_id)
    if record.user_id != current_user.id:
        flash('Unauthorized return attempt!', 'danger')
        return redirect(url_for('student.borrowed_books'))

    record.returned = True
    record.return_date = datetime.now(timezone.utc)
    record.book.copies_available += 1
    db.session.commit()

    flash('Book returned successfully!', 'success')
    return redirect(url_for('student.borrowed_books'))

# ----------------------------
# View borrowed books
# ----------------------------
@student_bp.route('/borrowed')
@login_required
@student_required
def borrowed_books():
    records = BorrowRecord.query.filter_by(user_id=current_user.id)\
                .order_by(BorrowRecord.borrow_date.desc()).all()
    
    # Pass current UTC date only
    current_date = datetime.now(timezone.utc).date()
    return render_template('student/borrowed_books.html', records=records, now=current_date)

# ----------------------------
# View fines
# ----------------------------
@student_bp.route('/fines')
@login_required
@student_required
def fines():
    records = BorrowRecord.query.filter_by(user_id=current_user.id).all()
    fine_total = 0
    fine_per_day = 5  # Configurable fine rate

    now_utc = datetime.now(timezone.utc).date()
    for r in records:
        if not r.returned and r.due_date and r.due_date.date() < now_utc:
         days_late = (now_utc - r.due_date.date()).days
         fine_total += days_late * fine_per_day


    return render_template('student/fines.html', fine_total=fine_total, fine_per_day=fine_per_day)
