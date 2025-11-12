# routes.py
from flask import Flask, render_template, redirect, url_for, Blueprint
from flask_login import login_required, current_user

app = Flask(__name__)

# ========================
# Student Blueprint
# ========================
student = Blueprint('student', __name__, url_prefix='/student')

@student.route('/dashboard')
@login_required
def dashboard():
    # Example data, replace with real queries
    total_books = 120
    borrowed_books = 5
    overdue_books = 1
    return render_template('student_dashboard.html',
                           total_books=total_books,
                           borrowed_books=borrowed_books,
                           overdue_books=overdue_books)

@student.route('/books')
@login_required
def books():
    # Replace with real book query
    book_list = [
        {"title": "Book 1", "author": "Author A"},
        {"title": "Book 2", "author": "Author B"}
    ]
    return render_template('books.html', books=book_list)

@student.route('/borrowed-books')
@login_required
def borrowed_books():
    # Replace with actual borrowed books query
    borrowed_list = [
        {"title": "Book 1", "due_date": "2025-11-20"},
        {"title": "Book 3", "due_date": "2025-11-25"}
    ]
    return render_template('borrowed_books.html', borrowed_books=borrowed_list)

@student.route('/fines')
@login_required
def fines():
    # Replace with actual fines query
    fines_list = [
        {"reason": "Overdue Book", "amount": 10},
        {"reason": "Damaged Book", "amount": 20}
    ]
    return render_template('fines.html', fines=fines_list)


# ========================
# General Routes
# ========================
@app.route('/')
def home():
    return redirect(url_for('student.dashboard'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    # Implement logout logic
    return redirect(url_for('login'))


# ========================
# Register Blueprint
# ========================
app.register_blueprint(student)

if __name__ == "__main__":
    app.secret_key = "supersecretkey"  # Needed for Flask-Login sessions
    app.run(debug=True)
