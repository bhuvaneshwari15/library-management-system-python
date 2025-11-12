from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Role
from extension import db
from sqlalchemy import or_

auth_bp = Blueprint('auth', __name__, template_folder='templates/auth')

# ----------------------------
# LOGIN
# ----------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirect already logged-in user by role
        if current_user.role == Role.ADMIN:
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == Role.TEACHER:
            return redirect(url_for('teacher.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if not user:
            flash('User not found.', 'danger')
            return render_template('login.html')

        if check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Logged in successfully.', 'success')

            # Redirect based on role
            if user.role == Role.ADMIN:
                return redirect(url_for('admin.dashboard'))
            elif user.role == Role.TEACHER:
                return redirect(url_for('teacher.dashboard'))
            else:
                return redirect(url_for('student.dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')


# ----------------------------
# LOGOUT
# ----------------------------
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))  # ✅ Redirects to index.html (not login page)


# ----------------------------
# REGISTER
# ----------------------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        role = request.form.get('role', 'student').lower()

        if not username or not email or not password:
            flash('All fields are required!', 'warning')
            return render_template('register.html')

        # Validate role
        if role not in [Role.ADMIN, Role.TEACHER, Role.STUDENT]:
            role = Role.STUDENT

        # Check if user exists
        existing_user = User.query.filter(
            or_(User.username == username, User.email == email)
        ).first()
        if existing_user:
            flash('Username or email already registered.', 'danger')
            return render_template('register.html')

        # Create user
        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, email=email, password_hash=hashed_pw, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')
