# ================================
# IMPORTS
# ================================
from flask import (
    Flask, render_template, redirect,
    url_for, Blueprint, request, jsonify, flash
)
from flask_login import login_required, current_user
from models import (
    Book, BorrowRecord, User, BookRecommendation
)
from fuzzywuzzy import fuzz
from sqlalchemy import or_
from datetime import date
from extension import db

# ================================
# APP SETUP
# ================================
app = Flask(__name__)
app.secret_key = "supersecretkey"

# ================================
# STUDENT BLUEPRINT
# ================================
student = Blueprint("student", __name__, url_prefix="/student")

@student.route("/dashboard")
@login_required
def dashboard():
    total_books = Book.query.count()

    borrowed_books = BorrowRecord.query.filter_by(
        user_id=current_user.id,
        returned=False
    ).count()

    overdue_books = BorrowRecord.query.filter(
        BorrowRecord.user_id == current_user.id,
        BorrowRecord.returned.is_(False),
        BorrowRecord.due_date < date.today()
    ).count()

    return render_template(
        "student_dashboard.html",
        total_books=total_books,
        borrowed_books=borrowed_books,
        overdue_books=overdue_books
    )

@student.route("/books")
@login_required
def books():
    return render_template(
        "books.html",
        books=Book.query.all()
    )

@student.route("/borrowed-books")
@login_required
def borrowed_books():
    borrowed = BorrowRecord.query.filter_by(
        user_id=current_user.id
    ).all()

    return render_template(
        "borrowed_books.html",
        borrowed_books=borrowed
    )

@student.route("/fines")
@login_required
def fines():
    borrows = BorrowRecord.query.filter_by(
        user_id=current_user.id
    ).all()

    fines_list = [
        {"reason": "Overdue Book", "amount": b.fine}
        for b in borrows if b.fine > 0
    ]

    return render_template(
        "fines.html",
        fines=fines_list
    )

# ================================
# 📚 BOOK RECOMMENDATION (Teacher)
# ================================
@student.route("/recommend", methods=["GET", "POST"])
@login_required
def recommend_book():
    if request.method == "POST":
        rec = BookRecommendation(
            title=request.form["title"].strip(),
            author=request.form["author"].strip(),
            reason=request.form["reason"].strip(),
            user_id=current_user.id
        )
        db.session.add(rec)
        db.session.commit()

        flash("Book recommendation submitted!", "success")
        return redirect(url_for("teacher.recommend_book"))

    recommendations = BookRecommendation.query.filter_by(
        user_id=current_user.id
    ).order_by(BookRecommendation.date.desc()).all()

    return render_template(
        "recommend.html",
        recommendations=recommendations
    )

# ================================
# GENERAL ROUTES
# ================================
@app.route("/")
def home():
    return redirect(url_for("student.dashboard"))

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    return redirect(url_for("login"))

# ================================
# REGISTER BLUEPRINT
# ================================
app.register_blueprint(student)

# ================================
# 🤖 CHATBOT API
# ================================
@app.route("/chatbot_api", methods=["POST"])
def chatbot_api():
    user_msg = request.json.get("message", "").lower().strip()

    def meaning(text, keywords):
        return any(
            fuzz.partial_ratio(text, k) > 70
            for k in keywords
        )

    # ------------------------------------------------------
    # BOOK SEARCH
    # ------------------------------------------------------
    if meaning(user_msg, ["search", "find book", "book about"]):
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
    # BORROWED BOOKS
    # ------------------------------------------------------
    if meaning(user_msg, ["my books", "borrowed"]):
        if not current_user.is_authenticated:
            return jsonify({"reply": "Please log in."})

        borrows = BorrowRecord.query.filter_by(
            user_id=current_user.id
        ).all()

        if not borrows:
            return jsonify({"reply": "No borrowed books."})

        reply = "<b>Your borrowed books:</b><br><br>"
        for b in borrows:
            status = (
                "Overdue"
                if b.due_date < date.today()
                else "On time"
            )
            reply += (
                f"• {b.book.title} — Due: "
                f"{b.due_date} ({status})<br>"
            )

        return jsonify({"reply": reply})

    # ------------------------------------------------------
    # FINES
    # ------------------------------------------------------
    if meaning(user_msg, ["fine", "penalty"]):
        if not current_user.is_authenticated:
            return jsonify({"reply": "Login required."})

        total_fine = sum(
            b.fine for b in BorrowRecord.query.filter_by(
                user_id=current_user.id
            )
        )

        return jsonify({
            "reply": f"Your total fine is <b>₹{total_fine}</b>."
        })

    # ------------------------------------------------------
    # DEFAULT
    # ------------------------------------------------------
    return jsonify({
        "reply":
        "<b>I can help with:</b><br>"
        "• Book search<br>"
        "• Borrowed books<br>"
        "• Overdue status<br>"
        "• Fine details<br>"
    })

# ================================
# RUN APP
# ================================
if __name__ == "__main__":
    app.run(debug=True)
