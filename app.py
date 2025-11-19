# app.py
from flask import Flask, render_template, flash, redirect, url_for
from config import DATABASE_URL, SECRET_KEY
from extension import db, login_manager
from models import User

# Import Flask-Migrate
from flask_migrate import Migrate

# Import all blueprints
from blueprints.auth import auth_bp
from blueprints.admin import admin_bp
from blueprints.teacher import teacher_bp
from blueprints.student import student_bp
from blueprints.chatbot import chatbot_bp   # Chatbot Blueprint


def create_app():
    app = Flask(__name__)

    # ------------------------------------
    # APP CONFIG
    # ------------------------------------
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = SECRET_KEY

    # ------------------------------------
    # INITIALIZE EXTENSIONS
    # ------------------------------------
    db.init_app(app)
    login_manager.init_app(app)

    # 🔥 Enable Flask-Migrate (Required for flask db commands)
    Migrate(app, db)

    login_manager.login_view = 'auth.login'

    # ------------------------------------
    # USER LOADER (Flask-Login)
    # ------------------------------------
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ------------------------------------
    # UNAUTHORIZED HANDLER
    # ------------------------------------
    @login_manager.unauthorized_handler
    def unauthorized():
        flash('Please log in to access that page.', 'warning')
        return redirect(url_for('index'))

    # ------------------------------------
    # REGISTER ALL BLUEPRINTS
    # ------------------------------------
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(teacher_bp, url_prefix='/teacher')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(chatbot_bp)  # Chatbot

    # ------------------------------------
    # ROOT ROUTE
    # ------------------------------------
    @app.route('/')
    def index():
        return render_template('index.html')

    return app


# ------------------------------------
# RUN THE APPLICATION
# ------------------------------------
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
