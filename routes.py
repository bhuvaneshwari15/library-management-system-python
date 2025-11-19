# ================================
# IMPORTS
# ================================
from flask import Flask, render_template, redirect, url_for, Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import Book, Borrow, User
from fuzzywuzzy import fuzz
from sqlalchemy import or_
from datetime import date

# ================================
# APP SETUP
# ================================
app = Flask(__name__)

# ================================
# STUDENT BLUEPRINT
# ================================
student = Blueprint('student', __name__, url_prefix='/student')

@student.route('/dashboard')
@login_required
def dashboard():
    # Replace with real DB queries if needed
    total_books = Book.query.count()
    borrowed_books = Borrow.query.filter_by(user_id=current_user.id).count()
    overdue_books = Borrow.query.filter(
        Borrow.user_id == current_user.id,
        Borrow.due_date < date.today()
    ).count()

    return render_template('student_dashboard.html',
                           total_books=total_books,
                           borrowed_books=borrowed_books,
                           overdue_books=overdue_books)

@student.route('/books')
@login_required
def books():
    book_list = Book.query.all()
    return render_template('books.html', books=book_list)

@student.route('/borrowed-books')
@login_required
def borrowed_books():
    borrowed_list = Borrow.query.filter_by(user_id=current_user.id).all()
    return render_template('borrowed_books.html', borrowed_books=borrowed_list)

@student.route('/fines')
@login_required
def fines():
    borrows = Borrow.query.filter_by(user_id=current_user.id).all()
    fines_list = [{"reason": "Overdue Book", "amount": b.fine_amount} for b in borrows if b.fine_amount > 0]
    return render_template('fines.html', fines=fines_list)

# ================================
# GENERAL ROUTES
# ================================
@app.route('/')
def home():
    return redirect(url_for('student.dashboard'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    # your logout logic here
    return redirect(url_for('login'))

# ================================
# REGISTER BLUEPRINT
# ================================
app.register_blueprint(student)

# ================================
# CHATBOT API (AI / NLP Assistant)
# ================================
@app.route("/chatbot_api", methods=["POST"])
def chatbot_api():
    user_msg = request.json.get("message", "").lower().strip()

    def meaning(text, keywords):
        """Simple NLP matching using fuzzy search."""
        return any(fuzz.partial_ratio(text, k) > 70 for k in keywords)

    # ------------------------------------------------------
    # 1. BOOK SEARCH
    # ------------------------------------------------------
    if meaning(user_msg, ["search", "find book", "look for", "book about", "search book"]):
        keyword = user_msg.split()[-1]

        books = Book.query.filter(
            or_(
                Book.title.ilike(f"%{keyword}%"),
                Book.author.ilike(f"%{keyword}%")
            )
        ).all()

        if not books:
            return jsonify({"reply": f"No books found for '{keyword}'."})

        reply = "<b>Books found:</b><br><br>"
        for b in books:
            reply += f"• <b>{b.title}</b> by {b.author}<br>"
        return jsonify({"reply": reply})

    # ------------------------------------------------------
    # 2. USER BORROWED BOOKS
    # ------------------------------------------------------
    if meaning(user_msg, ["my books", "issued", "borrowed", "what did i borrow"]):

        if not current_user.is_authenticated:
            return jsonify({"reply": "Please log in to view borrowed books."})

        borrows = Borrow.query.filter_by(user_id=current_user.id).all()

        if not borrows:
            return jsonify({"reply": "You have no borrowed books."})

        reply = "<b>Your borrowed books:</b><br><br>"
        for b in borrows:
            status = "Overdue" if b.due_date < date.today() else "On time"
            reply += f"• {b.book.title} — Due: {b.due_date} ({status})<br>"
        return jsonify({"reply": reply})

    # ------------------------------------------------------
    # 3. OVERDUE BOOKS
    # ------------------------------------------------------
    if meaning(user_msg, ["overdue", "late", "due date", "expired"]):

        if not current_user.is_authenticated:
            return jsonify({"reply": "Log in to check overdue books."})

        overdue = Borrow.query.filter(
            Borrow.user_id == current_user.id,
            Borrow.due_date < date.today()
        ).all()

        if not overdue:
            return jsonify({"reply": "You have no overdue books."})

        reply = "<b>Your overdue books:</b><br><br>"
        for o in overdue:
            reply += f"• {o.book.title} — Fine: ₹{o.fine_amount}<br>"
        return jsonify({"reply": reply})

    # ------------------------------------------------------
    # 4. FINE CHECK
    # ------------------------------------------------------
    if meaning(user_msg, ["fine", "penalty", "how much fine"]):

        if not current_user.is_authenticated:
            return jsonify({"reply": "Please log in to view your fines."})

        total_fine = sum(b.fine_amount for b in Borrow.query.filter_by(user_id=current_user.id).all())
        return jsonify({"reply": f"Your total fine is <b>₹{total_fine}</b>."})

    # ------------------------------------------------------
    # 5. LIBRARY STATS
    # ------------------------------------------------------
    if meaning(user_msg, ["how many books", "total books"]):
        return jsonify({"reply": f"The library has <b>{Book.query.count()}</b> books."})

    if meaning(user_msg, ["how many users", "total users"]):
        return jsonify({"reply": f"There are <b>{User.query.count()}</b> registered users."})

    if meaning(user_msg, ["how many borrowed", "borrowed count"]):
        return jsonify({"reply": f"<b>{Borrow.query.count()}</b> books are currently borrowed."})

    # ------------------------------------------------------
    # 6. ADMIN COMMANDS
    # ------------------------------------------------------
    if meaning(user_msg, ["admin", "overdue users", "all borrowed books"]):

        if not current_user.is_authenticated or current_user.role != "admin":
            return jsonify({"reply": "Admin access required."})

        # list all borrowed books
        if meaning(user_msg, ["all borrowed", "borrowed list"]):
            borrowed = Borrow.query.all()
            reply = "<b>All borrowed books:</b><br><br>"
            for b in borrowed:
                reply += f"• {b.user.username} → {b.book.title}<br>"
            return jsonify({"reply": reply})

        # list overdue users
        if meaning(user_msg, ["overdue users", "late users"]):
            overdue_users = Borrow.query.filter(Borrow.due_date < date.today()).all()
            reply = "<b>Users with overdue books:</b><br><br>"
            for b in overdue_users:
                reply += f"• {b.user.username} — {b.book.title}<br>"
            return jsonify({"reply": reply})

    # ------------------------------------------------------
    # DEFAULT FALLBACK
    # ------------------------------------------------------
    return jsonify({
        "reply": 
        "<b>I can help you with:</b><br><br>"
        "• Search books<br>"
        "• Your borrowed books<br>"
        "• Overdue status<br>"
        "• Fine details<br>"
        "• Library statistics<br>"
        "• Admin reports (admin only)<br>"
    })


# ================================
# RUN APP
# ================================
if __name__ == "__main__":
    app.secret_key = "supersecretkey"
    app.run(debug=True)
