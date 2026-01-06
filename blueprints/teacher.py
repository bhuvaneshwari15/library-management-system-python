# type: ignore
# pyright: ignore
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from extension import db
from models import User, Role, Book, BorrowRecord, BookRecommendation
from datetime import datetime, timedelta

# ✅ Use default templates folder (Flask already knows "templates/")
teacher_bp = Blueprint('teacher', __name__)

# -----------------------------------
# DECORATOR: Ensure Teacher Role Only
# -----------------------------------
def teacher_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != Role.TEACHER:
            flash('Access denied: Teachers only.', 'danger')
            return redirect(url_for('auth.login'))
        return fn(*args, **kwargs)
    return wrapper


# ----------------------------
# TEACHER DASHBOARD
# ----------------------------
@teacher_bp.route('/')
@login_required
@teacher_required
def dashboard():
    total_books = Book.query.count()
    borrowed_books = BorrowRecord.query.filter_by(user_id=current_user.id, returned=False).count()
    recommended_books = BookRecommendation.query.filter_by(user_id=current_user.id).count()

    return render_template(
        'teacher/dashboard.html',
        total_books=total_books,
        borrowed_books=borrowed_books,
        recommended_books=recommended_books
    )


# ----------------------------
# VIEW AVAILABLE BOOKS
# ----------------------------
@teacher_bp.route('/books')
@login_required
@teacher_required
def books():
    query = request.args.get('q', '').strip()
    selected_category = request.args.get('category', '').strip()
    page = request.args.get('page', 1, type=int)

    books_query = Book.query

    if query:
        books_query = books_query.filter(
            Book.title.ilike(f'%{query}%') |
            Book.author.ilike(f'%{query}%')
        )

    if selected_category:
        books_query = books_query.filter(Book.category == selected_category)

    pagination = books_query.paginate(page=page, per_page=6, error_out=False)

    categories = db.session.query(Book.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]

    categorized_books = {}
    for book in pagination.items:
        category = book.category or "Others"
        categorized_books.setdefault(category, []).append(book)

    return render_template(
        'teacher/books.html',
        categorized_books=categorized_books,
        categories=categories,
        selected_category=selected_category,
        books=pagination,
        query=query
    )

# ----------------------------
# BORROW A BOOK
# ----------------------------
@teacher_bp.route('/books/borrow/<int:book_id>')
@login_required
@teacher_required
def borrow_book(book_id):
    book = Book.query.get_or_404(book_id)

    if book.copies_available <= 0:
        flash('This book is currently unavailable!', 'danger')
        return redirect(url_for('teacher.books'))

    existing = BorrowRecord.query.filter_by(
        user_id=current_user.id,
        book_id=book_id,
        returned=False
    ).first()

    if existing:
        flash('You already borrowed this book.', 'warning')
        return redirect(url_for('teacher.books'))

    borrow = BorrowRecord(
        user_id=current_user.id,
        book_id=book.id,
        borrow_date=datetime.utcnow(),
        due_date=datetime.utcnow() + timedelta(days=14),
        returned=False
    )

    book.copies_available -= 1
    db.session.add(borrow)
    db.session.commit()

    flash('Book borrowed successfully!', 'success')
    return redirect(url_for('teacher.borrowed_books'))


# ----------------------------
# RETURN A BOOK
# ----------------------------
@teacher_bp.route('/books/return/<int:record_id>')
@login_required
@teacher_required
def return_book(record_id):
    record = BorrowRecord.query.get_or_404(record_id)

    if record.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('teacher.borrowed_books'))

    record.returned = True
    record.return_date = datetime.utcnow()
    record.book.copies_available += 1
    db.session.commit()

    flash('Book returned successfully!', 'success')
    return redirect(url_for('teacher.borrowed_books'))


# ----------------------------
# VIEW BORROWED BOOKS
# ----------------------------
@teacher_bp.route('/borrowed')
@login_required
@teacher_required
def borrowed_books():
    records = (
        BorrowRecord.query.filter_by(user_id=current_user.id)
        .order_by(BorrowRecord.borrow_date.desc())
        .all()
    )
    return render_template('teacher/borrowed_books.html', records=records)


# ----------------------------
# RECOMMEND NEW BOOKS
# ----------------------------
@teacher_bp.route('/recommend', methods=['GET', 'POST'])
@login_required
@teacher_required
def recommend_book():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        reason = request.form.get('reason', '').strip()

        if not title or not author or not reason:
            flash('All fields are required.', 'danger')
            return redirect(url_for('teacher.recommend_book'))

        recommendation = BookRecommendation(
            user_id=current_user.id,
            title=title,
            author=author,
            reason=reason,
            date=datetime.utcnow()
        )
        db.session.add(recommendation)
        db.session.commit()

        flash('Book recommendation sent to the admin.', 'success')
        return redirect(url_for('teacher.recommend_book'))

    recommendations = (
        BookRecommendation.query.filter_by(user_id=current_user.id)
        .order_by(BookRecommendation.date.desc())
        .all()
    )
    return render_template('teacher/recommend.html', recommendations=recommendations)


# ----------------------------
# VIEW CLASS READING REPORT
# ----------------------------
@teacher_bp.route('/reports')
@login_required
@teacher_required
def reports():
    borrowed_books = (
        BorrowRecord.query.join(User)
        .filter(User.role == Role.STUDENT)
        .order_by(BorrowRecord.borrow_date.desc())
        .all()
    )
    return render_template('teacher/reports.html', borrowed_books=borrowed_books)
