# blueprints/chatbot.py
from flask import Blueprint, request, jsonify
from flask_login import current_user
from models import Book, BorrowRecord, User
from fuzzywuzzy import fuzz
from sqlalchemy import or_
from datetime import datetime, date

chatbot_bp = Blueprint('chatbot_bp', __name__)

# --- Intent keywords (first try simple substring checks, then fuzzy)
INTENT_KEYWORDS = {
    "count_books": ["how many books", "total books", "books count", "number of books"],
    "count_users": ["how many users", "total users", "users count", "number of users"],
    "my_borrowed": ["my books", "what did i borrow", "borrowed", "issued"],
    "search_book": ["search", "find book", "look for", "book about", "search book"],
    "check_fines": ["fine", "fines", "penalty", "how much fine"],
    "overdue": ["overdue", "late", "due date", "expired"],
    "count_borrowed": ["how many borrowed", "borrowed count", "how many issued"],
}

FUZZY_THRESHOLD = 70  # adjust as needed


def detect_intent(text: str):
    t = text.lower().strip()

    # 1) direct substring matching (high priority)
    for intent, keywords in INTENT_KEYWORDS.items():
        for k in keywords:
            if k in t:
                return intent

    # 2) fuzzy matching of whole keywords (handles misspellings / missing spaces)
    for intent, keywords in INTENT_KEYWORDS.items():
        for k in keywords:
            score = fuzz.partial_ratio(t, k)
            if score >= FUZZY_THRESHOLD:
                return intent

    # 3) fallback: look for important words
    if "user" in t or "users" in t or "member" in t:
        return "count_users"
    if "book" in t or "books" in t:
        # differentiate between counting and searching if "search" or "find" present
        if "search" in t or "find" in t or "look for" in t:
            return "search_book"
        return "count_books"

    return None


@chatbot_bp.route("/chatbot_api", methods=["POST"])
def chatbot_api():
    msg = request.json.get("message", "") or ""
    msg = msg.strip()

    if not msg:
        return jsonify({"reply": "Please ask a question (e.g. 'How many books?' or 'How much fine do I have?')."})

    intent = detect_intent(msg)

    # --- BOOK COUNT
    if intent == "count_books":
        try:
            total = Book.query.count()
        except Exception:
            total = 0
        return jsonify({"reply": f"There are <b>{total}</b> books in the library."})

    # --- USER COUNT
    if intent == "count_users":
        try:
            total = User.query.count()
        except Exception:
            total = 0
        return jsonify({"reply": f"There are <b>{total}</b> registered users."})

    # --- BORROWED COUNT (all borrow records)
    if intent == "count_borrowed":
        try:
            total = BorrowRecord.query.count()
        except Exception:
            total = 0
        return jsonify({"reply": f"There are <b>{total}</b> borrow records (books currently borrowed or previously borrowed)."})


    # --- SEARCH BOOK (simple keyword extraction)
    if intent == "search_book":
        # attempt to extract a search phrase
        words = msg.split()
        # find the longest word group after keywords like 'search', 'find', 'for', 'about'
        for marker in ("search", "find", "for", "about", "book"):
            if marker in words:
                idx = words.index(marker)
                # take everything after the marker as keyword
                keyword = " ".join(words[idx + 1:]) or words[-1]
                break
        else:
            keyword = words[-1]

        keyword = keyword.strip()
        if not keyword:
            return jsonify({"reply": "Please give a keyword to search (e.g. 'Search Harry Potter')."})

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
            reply += f"• {b.title} by {b.author or 'Unknown'}<br>"
        return jsonify({"reply": reply})

    # --- USER BORROWED BOOKS
    if intent == "my_borrowed":
        if not current_user.is_authenticated:
            return jsonify({"reply": "Please log in to check your borrowed books."})

        records = BorrowRecord.query.filter_by(user_id=current_user.id).all()
        if not records:
            return jsonify({"reply": "You currently have no borrowed books."})

        reply = "<b>Your borrowed books:</b><br>"
        for r in records:
            due = r.due_date.date() if r.due_date else "No due date"
            status = "Returned" if r.returned else ("Overdue" if (r.due_date and r.due_date.date() < date.today()) else "Borrowed")
            reply += f"• {r.book.title} — Due: {due} ({status})<br>"
        return jsonify({"reply": reply})

    # --- FINES
    if intent == "check_fines":
        if not current_user.is_authenticated:
            return jsonify({"reply": "Please log in to check fines."})

        records = BorrowRecord.query.filter_by(user_id=current_user.id).all()
        total_fine = sum(r.fine or 0.0 for r in records)
        return jsonify({"reply": f"Your total fine is <b>₹{total_fine}</b>."})

    # --- OVERDUE
    if intent == "overdue":
        if not current_user.is_authenticated:
            return jsonify({"reply": "Please log in to check overdue books."})

        overdue = BorrowRecord.query.filter(
            BorrowRecord.user_id == current_user.id,
            BorrowRecord.due_date.isnot(None),
            BorrowRecord.returned == False,
            BorrowRecord.due_date < datetime.utcnow()
        ).all()

        if not overdue:
            return jsonify({"reply": "You have no overdue books."})

        reply = "<b>Your overdue books:</b><br>"
        for r in overdue:
            reply += f"• {r.book.title} — Fine: ₹{r.fine}<br>"
        return jsonify({"reply": reply})

    # --- fallback: try to infer "count_books" or "count_users" more carefully
    lowered = msg.lower()
    if "how many" in lowered or "how much" in lowered or "number of" in lowered:
        if "user" in lowered or "member" in lowered:
            total = User.query.count()
            return jsonify({"reply": f"There are <b>{total}</b> registered users."})
        if "book" in lowered:
            total = Book.query.count()
            return jsonify({"reply": f"There are <b>{total}</b> books in the library."})

    # Default reply
    return jsonify({
        "reply":
        "<b>I can help with:</b><br>"
        "• How many books/users?<br>"
        "• Search books (e.g. 'Search Harry Potter')<br>"
        "• Your borrowed books<br>"
        "• Overdue books and fines<br>"
    })
