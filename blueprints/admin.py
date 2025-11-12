from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from models import User, Role, Book, BorrowRecord
from extension import db
from werkzeug.security import generate_password_hash

# -----------------------------------
# BLUEPRINT CONFIGURATION
# -----------------------------------
admin_bp = Blueprint('admin', __name__, template_folder='templates/admin')

# -----------------------------------
# ADMIN ROLE CHECK DECORATOR
# -----------------------------------
def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != Role.ADMIN:
            flash('Admin access required', 'danger')
            return redirect(url_for('auth.login'))
        return fn(*args, **kwargs)
    return wrapper

# -----------------------------------
# ADMIN DASHBOARD
# -----------------------------------
@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    total_books = Book.query.count()
    total_users = User.query.count()
    total_borrowed = BorrowRecord.query.filter_by(returned=False).count()
    total_available = db.session.query(db.func.sum(Book.copies_available)).scalar() or 0
    overdue = BorrowRecord.query.filter(
        BorrowRecord.due_date < db.func.current_date(),
        BorrowRecord.returned == False
    ).count()

    return render_template(
        'admin/dashboard.html',
        total_books=total_books,
        total_users=total_users,
        total_borrowed=total_borrowed,
        total_available=total_available,
        overdue=overdue
    )

# -----------------------------------
# MANAGE BOOKS
# -----------------------------------
@admin_bp.route('/books')
@login_required
@admin_required
def books():
    books = Book.query.all()
    return render_template('admin/books.html', books=books)

@admin_bp.route('/books/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_book():
    if request.method == 'POST':
        book = Book(
            isbn=request.form.get('isbn'),
            title=request.form.get('title'),
            author=request.form.get('author'),
            publisher=request.form.get('publisher'),
            year=int(request.form.get('year') or 0),
            copies_total=int(request.form.get('copies_total') or 1),
            copies_available=int(request.form.get('copies_total') or 1),
            category=request.form.get('category'),
            description=request.form.get('description')
        )
        db.session.add(book)
        db.session.commit()
        flash('Book added successfully!', 'success')
        return redirect(url_for('admin.books'))
    return render_template('admin/add_book.html')

@admin_bp.route('/books/edit/<int:book_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    if request.method == 'POST':
        book.isbn = request.form.get('isbn')
        book.title = request.form.get('title')
        book.author = request.form.get('author')
        book.publisher = request.form.get('publisher')
        book.year = int(request.form.get('year') or 0)
        book.copies_total = int(request.form.get('copies_total') or 1)
        book.copies_available = int(request.form.get('copies_available') or book.copies_total)
        book.category = request.form.get('category')
        book.description = request.form.get('description')
        db.session.commit()
        flash('Book updated successfully!', 'success')
        return redirect(url_for('admin.books'))
    return render_template('admin/edit_book.html', book=book)

@admin_bp.route('/books/delete/<int:book_id>')
@login_required
@admin_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted successfully!', 'success')
    return redirect(url_for('admin.books'))

# -----------------------------------
# MANAGE USERS
# -----------------------------------
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        if User.query.filter_by(email=email).first():
            flash('User already exists!', 'danger')
            return redirect(url_for('admin.users'))

        new_user = User(
            username=username,
            email=email,
            role=role,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        flash('User added successfully!', 'success')
        return redirect(url_for('admin.users'))
    return render_template('admin/add_user.html')

@admin_bp.route('/users/delete/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == Role.ADMIN:
        flash('Cannot delete another admin!', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
    return redirect(url_for('admin.users'))

# -----------------------------------
# REPORTS
# -----------------------------------
@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    borrowed_books = BorrowRecord.query.all()
    return render_template('admin/reports.html', borrowed_books=borrowed_books)
