# type: ignore
# pyright: ignore

from flask import Blueprint, request, jsonify
from flask_login import current_user
from models import Book, BorrowRecord, User
from fuzzywuzzy import fuzz
from sqlalchemy import or_, func
from datetime import datetime, date
from extension import db

chatbot_bp = Blueprint("chatbot_bp", __name__)

# -------------------------------
# Intent Keywords
# -------------------------------
INTENT_KEYWORDS = {
    # counts
    "count_books": ["how many books", "total books", "books count", "number of books"],
    "count_users": ["how many users", "total users", "users count", "number of users"],
    "count_borrowed": ["how many borrowed", "borrowed count", "how many issued"],

    # user activity
    "my_borrowed": ["my books", "what did i borrow", "borrowed", "issued"],
    "check_fines": ["fine", "fines", "penalty", "how much fine"],
    "overdue": ["overdue", "late", "due date", "expired"],
    "my_due_date": ["return date", "when should i return", "due date"],

    # search & browse
    "search_book": ["search", "find book", "look for", "book about", "search book"],
    "available_books": ["available books", "books available", "in stock", "can i borrow"],
    "books_by_author": ["books by", "written by", "author"],
    "books_by_category": ["ai books", "programming books", "database books", "category"],

    # recommendation
    "recommend_book": [
        "suggest me a book", "recommend a book", "what should i read",
        "book recommendation", "suggest book", "recommend book"
    ],

    # role based
    "admin_stats": ["system stats", "admin stats", "library stats"],
    "teacher_report": ["borrow report", "students borrowing", "borrowed books report"],

    # greetings
    "greeting": ["hi", "hello", "hey", "help"]
}

FUZZY_THRESHOLD = 70


# -------------------------------
# Intent Detection
# -------------------------------
def detect_intent(text: str):
    t = text.lower().strip()

    # direct keyword match
    for intent, keywords in INTENT_KEYWORDS.items():
        for k in keywords:
            if k in t:
                return intent

    # fuzzy match
    for intent, keywords in INTENT_KEYWORDS.items():
        for k in keywords:
            if fuzz.partial_ratio(t, k) >= FUZZY_THRESHOLD:
                return intent

    # fallback heuristics
    if "user" in t or "member" in t:
        return "count_users"
    if "book" in t:
        if "search" in t or "find" in t:
            return "search_book"
        return "count_books"

    return None


# -------------------------------
# Chatbot API
# -------------------------------
@chatbot_bp.route("/chatbot_api", methods=["POST"])
def chatbot_api():
    msg = request.json.get("message", "").strip()
    if not msg:
        return jsonify({"reply": "Please ask a question (e.g. 'How many books?' or 'Suggest me a book')."})

    intent = detect_intent(msg)

    # -------------------------------
    # Greetings
    # -------------------------------
    if intent == "greeting":
        return jsonify({
            "reply":
            "Hello 👋 I can help you with:<br>"
            "• Searching books<br>"
            "• Borrowed books & due dates<br>"
            "• Fines & overdue books<br>"
            "• Book recommendations<br>"
            "• Library statistics (Admin / Teacher)"
        })

    # -------------------------------
    # Counts
    # -------------------------------
    if intent == "count_books":
        return jsonify({"reply": f"There are <b>{Book.query.count()}</b> books in the library."})

    if intent == "count_users":
        return jsonify({"reply": f"There are <b>{User.query.count()}</b> registered users."})

    if intent == "count_borrowed":
        total = BorrowRecord.query.count()
        return jsonify({"reply": f"There are <b>{total}</b> borrow records."})

    # -------------------------------
    # Available Books
    # -------------------------------
    if intent == "available_books":
        books = Book.query.filter(Book.copies_available > 0).all()
        if not books:
            return jsonify({"reply": "No books are currently available."})

        reply = "<b>Available books:</b><br>"
        for b in books:
            reply += f"• {b.title} ({b.copies_available} copies)<br>"
        return jsonify({"reply": reply})

    # -------------------------------
    # Search Books
    # -------------------------------
    if intent == "search_book":
        words = msg.split()
        keyword = words[-1]

        books = Book.query.filter(
            or_(
                Book.title.ilike(f"%{keyword}%"),
                Book.author.ilike(f"%{keyword}%")
            )
        ).all()

        if not books:
            return jsonify({"reply": f"No books found for '<b>{keyword}</b>'."})

        reply = "<b>Books found:</b><br>"
        for b in books:
            reply += f"• {b.title} by {b.author}<br>"
        return jsonify({"reply": reply})

    # -------------------------------
    # Books by Author
    # -------------------------------
    if intent == "books_by_author":
        author = msg.split("by")[-1].strip()
        books = Book.query.filter(Book.author.ilike(f"%{author}%")).all()

        if not books:
            return jsonify({"reply": f"No books found by <b>{author}</b>."})

        reply = f"<b>Books by {author}:</b><br>"
        for b in books:
            reply += f"• {b.title} ({b.year})<br>"
        return jsonify({"reply": reply})

    # -------------------------------
    # Books by Category
    # -------------------------------
    if intent == "books_by_category":
        categories = ["ai", "programming", "databases", "cloud", "security", "software"]
        found = next((c for c in categories if c in msg.lower()), None)

        if not found:
            return jsonify({"reply": "Please specify a category (e.g. AI, Programming, Databases)."})

        books = Book.query.filter(Book.category.ilike(f"%{found}%")).all()
        if not books:
            return jsonify({"reply": f"No books found in <b>{found}</b> category."})

        reply = f"<b>{found.title()} books:</b><br>"
        for b in books:
            reply += f"• {b.title}<br>"
        return jsonify({"reply": reply})

    # -------------------------------
    # My Borrowed Books
    # -------------------------------
    if intent == "my_borrowed":
        if not current_user.is_authenticated:
            return jsonify({"reply": "Please log in to check your borrowed books."})

        records = BorrowRecord.query.filter_by(user_id=current_user.id).all()
        if not records:
            return jsonify({"reply": "You have not borrowed any books."})

        reply = "<b>Your borrowed books:</b><br>"
        for r in records:
            status = "Returned" if r.returned else (
                "Overdue" if r.due_date and r.due_date.date() < date.today() else "Borrowed"
            )
            reply += f"• {r.book.title} ({status})<br>"
        return jsonify({"reply": reply})

    # -------------------------------
    # Due Dates
    # -------------------------------
    if intent == "my_due_date":
        if not current_user.is_authenticated:
            return jsonify({"reply": "Please log in to check due dates."})

        records = BorrowRecord.query.filter_by(user_id=current_user.id, returned=False).all()
        if not records:
            return jsonify({"reply": "You have no active borrowed books."})

        reply = "<b>Your due dates:</b><br>"
        for r in records:
            reply += f"• {r.book.title}: {r.due_date.date()}<br>"
        return jsonify({"reply": reply})

    # -------------------------------
    # Fines
    # -------------------------------
    if intent == "check_fines":
        if not current_user.is_authenticated:
            return jsonify({"reply": "Please log in to check fines."})

        total = sum(r.fine or 0 for r in BorrowRecord.query.filter_by(user_id=current_user.id))
        return jsonify({"reply": f"Your total fine is <b>₹{total}</b>."})

    # -------------------------------
    # Overdue
    # -------------------------------
    if intent == "overdue":
        if not current_user.is_authenticated:
            return jsonify({"reply": "Please log in to check overdue books."})

        overdue = BorrowRecord.query.filter(
            BorrowRecord.user_id == current_user.id,
            BorrowRecord.returned == False,
            BorrowRecord.due_date < datetime.utcnow()
        ).all()

        if not overdue:
            return jsonify({"reply": "You have no overdue books."})

        reply = "<b>Your overdue books:</b><br>"
        for r in overdue:
            reply += f"• {r.book.title} — Fine: ₹{r.fine}<br>"
        return jsonify({"reply": reply})

    # -------------------------------
    # Recommendation
    # -------------------------------
    if intent == "recommend_book":
        categories = ["ai", "programming", "databases", "cloud", "security", "software"]
        preferred = next((c for c in categories if c in msg.lower()), None)

        if preferred:
            books = Book.query.filter(
                Book.category.ilike(f"%{preferred}%"),
                Book.copies_available > 0
            ).limit(5).all()
        else:
            books = Book.query.filter(Book.copies_available > 0).limit(5).all()

        if not books:
            return jsonify({"reply": "No books available for recommendation."})

        reply = "<b>📚 Recommended books:</b><br>"
        for b in books:
            reply += f"• {b.title} by {b.author}<br>"
        return jsonify({"reply": reply})

    # -------------------------------
    # Admin Stats
    # -------------------------------
    if intent == "admin_stats":
        if not current_user.is_authenticated or not current_user.is_admin():
            return jsonify({"reply": "⚠️ Admin access required."})

        return jsonify({
            "reply":
            "<b>📊 Library Statistics:</b><br>"
            f"• Total Books: {Book.query.count()}<br>"
            f"• Total Users: {User.query.count()}<br>"
            f"• Active Borrows: {BorrowRecord.query.filter_by(returned=False).count()}"
        })

    # -------------------------------
    # Teacher Report
    # -------------------------------
    if intent == "teacher_report":
        if not current_user.is_authenticated or not current_user.is_teacher():
            return jsonify({"reply": "⚠️ Teacher access required."})

        records = BorrowRecord.query.filter_by(returned=False).all()
        if not records:
            return jsonify({"reply": "No active borrow records."})

        reply = "<b>📋 Students currently borrowing:</b><br>"
        for r in records:
            reply += f"• {r.user.username} → {r.book.title}<br>"
        return jsonify({"reply": reply})

    # -------------------------------
    # Default
    # -------------------------------
    return jsonify({
        "reply":
        "<b>I can help with:</b><br>"
        "• Searching books<br>"
        "• Book recommendations<br>"
        "• Borrowed books & due dates<br>"
        "• Fines & overdue books<br>"
        "• Library statistics"
    })
