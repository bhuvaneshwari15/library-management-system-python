# type: ignore
# pyright: ignore

import os
from io import BytesIO
from functools import wraps
from datetime import datetime

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, Response, current_app
)
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from models import User, Role, Book, BorrowRecord, BookRecommendation
from extension import db

# PDF
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


# =================================================
# BLUEPRINT
# =================================================
admin_bp = Blueprint(
    "admin",
    __name__,
    template_folder="templates/admin",
    url_prefix="/admin"
)


# =================================================
# ADMIN ACCESS DECORATOR
# =================================================
def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != Role.ADMIN:
            flash("Admin access required", "danger")
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)
    return wrapper


# =================================================
# FILE VALIDATION
# =================================================
def allowed_file(filename):
    return (
        "." in filename and
        filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


# =================================================
# DASHBOARD
# =================================================
@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    return render_template(
        "admin/dashboard.html",
        total_books=Book.query.count(),
        total_users=User.query.count(),
        total_available=db.session.query(
            func.coalesce(func.sum(Book.copies_available), 0)
        ).scalar(),
        total_borrowed=BorrowRecord.query.filter_by(returned=False).count(),
        overdue=BorrowRecord.query.filter(
            BorrowRecord.returned.is_(False),
            BorrowRecord.due_date < datetime.utcnow()
        ).count(),
        admin_count=User.query.filter_by(role=Role.ADMIN).count(),
        teacher_count=User.query.filter_by(role=Role.TEACHER).count(),
        student_count=User.query.filter_by(role=Role.STUDENT).count(),
        pending_recommendations=BookRecommendation.query.filter_by(
            status="pending"
        ).count(),
        recent_recommendations=BookRecommendation.query.order_by(
            BookRecommendation.date.desc()
        ).limit(5).all()
    )


# =================================================
# BOOK RECOMMENDATIONS
# =================================================
@admin_bp.route("/recommendations")
@login_required
@admin_required
def recommendations():
    return render_template(
        "admin/recommendations.html",
        recommendations=BookRecommendation.query.order_by(
            BookRecommendation.date.desc()
        ).all(),
        pending_recommendations=BookRecommendation.query.filter_by(
            status="pending"
        ).count()
    )


@admin_bp.route("/recommendations/<int:rec_id>/<action>")
@login_required
@admin_required
def update_recommendation_status(rec_id, action):
    rec = BookRecommendation.query.get_or_404(rec_id)

    if action not in ("approved", "rejected"):
        flash("Invalid action", "danger")
        return redirect(url_for("admin.recommendations"))

    rec.status = action
    db.session.commit()
    flash(f"Recommendation {action}", "success")
    return redirect(url_for("admin.recommendations"))


# =================================================
# BOOKS
# =================================================
@admin_bp.route("/books")
@login_required
@admin_required
def books():
    return render_template(
        "admin/books.html",
        books=Book.query.order_by(Book.title).all()
    )


@admin_bp.route("/books/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_book():
    if request.method == "POST":
        try:
            # ---------------- BASIC DATA ----------------
            isbn = request.form.get("isbn") or None
            title = request.form["title"].strip()
            author = request.form["author"].strip()
            publisher = request.form["publisher"].strip()
            year = int(request.form["year"])
            copies_total = int(request.form["copies_total"])
            category = request.form["category"].strip()
            description = request.form.get("description", "")[:500]

            # ---------------- RATING ----------------
            rating = request.form.get("rating")
            rating = int(rating) if rating else 0

            # ---------------- COVER LOGIC ----------------
            cover_url = None
            file = request.files.get("cover_image")

            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                path = os.path.join(
                    current_app.config["UPLOAD_FOLDER"], filename
                )
                file.save(path)
                cover_url = f"/static/uploads/{filename}"

            elif isbn:
                cover_url = (
                    f"https://covers.openlibrary.org/b/isbn/"
                    f"{isbn}-L.jpg?default=false"
                )

            # ---------------- CREATE BOOK ----------------
            book = Book(
                isbn=isbn,
                title=title,
                author=author,
                publisher=publisher,
                year=year,
                copies_total=copies_total,
                copies_available=copies_total,
                category=category,
                description=description,
                cover_url=cover_url,
                rating=rating
            )

            db.session.add(book)
            db.session.commit()

            flash("Book added successfully", "success")
            return redirect(url_for("admin.books"))

        except (IntegrityError, ValueError):
            db.session.rollback()
            flash("Error adding book. Please check inputs.", "danger")
            return redirect(url_for("admin.add_book"))

    return render_template("admin/add_book.html")


@admin_bp.route("/books/edit/<int:book_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)

    if request.method == "POST":
        isbn = request.form.get("isbn") or None
        book.isbn = isbn

        book.title = request.form["title"]
        book.author = request.form["author"]
        book.publisher = request.form["publisher"]
        book.year = int(request.form["year"])
        book.category = request.form["category"]
        book.description = request.form.get("description", "")
        rating = request.form.get("rating")
        book.rating = int(rating) if rating else 0

        # ---------- COVER LOGIC ----------
        file = request.files.get("cover_image")
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(
                current_app.config["UPLOAD_FOLDER"], filename
            )
            file.save(path)
            book.cover_url = f"/static/uploads/{filename}"

        elif isbn:
            book.cover_url = (
                f"https://covers.openlibrary.org/b/isbn/"
                f"{isbn}-L.jpg?default=false"
            )

        # ---------- COPIES ----------
        new_total = int(request.form["copies_total"])
        borrowed = book.copies_total - book.copies_available
        book.copies_total = new_total
        book.copies_available = max(new_total - borrowed, 0)

        db.session.commit()
        flash("Book updated successfully", "success")
        return redirect(url_for("admin.books"))

    return render_template("admin/edit_book.html", book=book)


@admin_bp.route("/books/delete/<int:book_id>")
@login_required
@admin_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)

    if BorrowRecord.query.filter_by(
        book_id=book.id, returned=False
    ).count():
        flash("Cannot delete book. It is currently borrowed.", "danger")
        return redirect(url_for("admin.books"))

    db.session.delete(book)
    db.session.commit()
    flash("Book deleted successfully", "success")
    return redirect(url_for("admin.books"))


# =================================================
# USERS
# =================================================
@admin_bp.route("/users")
@login_required
@admin_required
def users():
    return render_template(
        "admin/users.html",
        users=User.query.order_by(User.username).all()
    )


@admin_bp.route("/users/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_user():
    if request.method == "POST":
        if User.query.filter(
            (User.username == request.form["username"]) |
            (User.email == request.form["email"])
        ).first():
            flash("User already exists", "danger")
            return redirect(url_for("admin.users"))

        user = User(
            username=request.form["username"].strip(),
            email=request.form["email"].strip(),
            role=request.form["role"],
            password_hash=generate_password_hash(
                request.form["password"]
            )
        )

        db.session.add(user)
        db.session.commit()
        flash("User added successfully", "success")
        return redirect(url_for("admin.users"))

    return render_template("admin/add_user.html")


@admin_bp.route("/users/delete/<int:user_id>")
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.role == Role.ADMIN:
        flash("Cannot delete admin user", "danger")
        return redirect(url_for("admin.users"))

    db.session.delete(user)
    db.session.commit()
    flash("User deleted", "success")
    return redirect(url_for("admin.users"))


# =================================================
# REPORTS
# =================================================
@admin_bp.route("/reports")
@login_required
@admin_required
def reports():
    return render_template(
        "admin/reports.html",
        borrowed_books=BorrowRecord.query.order_by(
            BorrowRecord.borrow_date.desc()
        ).all(),
        current_date=datetime.utcnow()
    )


# -------------------------------------------------
# EXPORT FULL REPORT (PDF)
# -------------------------------------------------
@admin_bp.route("/export/full-report/pdf")
@login_required
@admin_required
def export_full_report_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    elements = []

    elements.append(
        Paragraph("📊 Library Full Detailed Report", styles["Title"])
    )
    elements.append(Spacer(1, 20))

    # ---------------- USERS ----------------
    elements.append(Paragraph("👥 Users", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    for u in User.query.order_by(User.username).all():
        elements.append(
            Paragraph(
                f"""
                <b>Username:</b> {u.username}<br/>
                <b>Email:</b> {u.email}<br/>
                <b>Role:</b> {u.role}<br/>
                <b>Joined:</b> {u.created_at.date()}
                """,
                styles["Normal"]
            )
        )
        elements.append(Spacer(1, 12))

    # ---------------- BOOKS ----------------
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("📚 Books", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    for b in Book.query.order_by(Book.title).all():
        elements.append(
            Paragraph(
                f"""
                <b>Title:</b> {b.title}<br/>
                <b>Author:</b> {b.author}<br/>
                <b>Publisher:</b> {b.publisher}<br/>
                <b>Year:</b> {b.year}<br/>
                <b>Category:</b> {b.category}<br/>
                <b>Total Copies:</b> {b.copies_total}<br/>
                <b>Available Copies:</b> {b.copies_available}
                """,
                styles["Normal"]
            )
        )
        elements.append(Spacer(1, 12))

    # ---------------- BORROWED ----------------
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("📖 Borrowed Books", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    for br in BorrowRecord.query.order_by(
        BorrowRecord.borrow_date.desc()
    ).all():
        status = "Returned" if br.returned else "Not Returned"
        overdue = (
            " (OVERDUE)"
            if not br.returned and br.due_date < datetime.utcnow()
            else ""
        )

        elements.append(
            Paragraph(
                f"""
                <b>Book:</b> {br.book.title}<br/>
                <b>User:</b> {br.user.username}<br/>
                <b>Borrowed On:</b> {br.borrow_date.date()}<br/>
                <b>Due Date:</b> {br.due_date.date()}<br/>
                <b>Status:</b> {status}{overdue}
                """,
                styles["Normal"]
            )
        )
        elements.append(Spacer(1, 12))

    # ---------------- FINES ----------------
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("💰 Fines / Overdue List", styles["Heading2"]))
    elements.append(Spacer(1, 10))

    overdue_records = BorrowRecord.query.filter(
        BorrowRecord.returned.is_(False),
        BorrowRecord.due_date < datetime.utcnow()
    ).all()

    if not overdue_records:
        elements.append(
            Paragraph("No overdue fines 🎉", styles["Normal"])
        )
    else:
        for o in overdue_records:
            days_overdue = (datetime.utcnow() - o.due_date).days
            fine_amount = days_overdue * 5

            elements.append(
                Paragraph(
                    f"""
                    <b>User:</b> {o.user.username}<br/>
                    <b>Book:</b> {o.book.title}<br/>
                    <b>Days Overdue:</b> {days_overdue}<br/>
                    <b>Fine Amount:</b> ₹{fine_amount}
                    """,
                    styles["Normal"]
                )
            )
            elements.append(Spacer(1, 12))

    doc.build(elements)
    buffer.seek(0)

    return Response(
        buffer,
        mimetype="application/pdf",
        headers={
            "Content-Disposition":
            "attachment; filename=library_full_detailed_report.pdf"
        }
    )
