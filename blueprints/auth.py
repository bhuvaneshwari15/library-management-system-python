# type: ignore
# pyright: ignore
from flask import Blueprint, render_template, request, redirect, url_for, flash # type: ignore
from flask_login import login_user, logout_user, login_required, current_user # pyright: ignore
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Role
from extension import db
from sqlalchemy import or_

auth_bp = Blueprint('auth', __name__, template_folder='templates/auth')


# ---------------------------------------------
# LOGIN
# ---------------------------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If user already logged in → send to their dashboard
    if current_user.is_authenticated:
        if current_user.role == Role.ADMIN:
            return redirect(url_for('admin.dashboard')) # type: ignore
        elif current_user.role == Role.TEACHER:
            return redirect(url_for('teacher.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')

        # Allow login via username OR email
        user = User.query.filter(
            or_(User.username == username, User.email == username)
        ).first()

        if not user:
            flash("❌ User not found. Check your username or email.", "danger")
            return render_template('login.html')

        if not check_password_hash(user.password_hash, password):
            flash("❌ Incorrect password. Try again.", "danger")
            return render_template('login.html')

        # Login successful
        login_user(user)
        flash("✅ Login successful!", "success")

        # Redirect based on role
        if user.role == Role.ADMIN:
            return redirect(url_for('admin.dashboard'))
        elif user.role == Role.TEACHER:
            return redirect(url_for('teacher.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))

    return render_template('login.html')


# ---------------------------------------------
# LOGOUT
# ---------------------------------------------
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("ℹ️ You have been logged out.", "info")
    return redirect(url_for('auth.login'))



# ---------------------------------------------
# REGISTER
# ---------------------------------------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip()
        password = request.form.get('password')
        role = request.form.get('role', 'student').lower()  # default: student

        # Validation
        if not username or not email or not password:
            flash("⚠️ All fields are required.", "warning")
            return render_template('register.html')

        # Validate role value
        if role not in [Role.ADMIN, Role.TEACHER, Role.STUDENT]:
            role = Role.STUDENT

        # Check existing user
        user_exists = User.query.filter(
            or_(User.username == username, User.email == email)
        ).first()

        if user_exists:
            flash("❌ Username or email already exists!", "danger")
            return render_template('register.html')

        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        flash("🎉 Registration successful! Please log in.", "success")
        return redirect(url_for('auth.login'))

    return render_template('register.html')
