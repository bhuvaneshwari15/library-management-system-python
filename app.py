# type: ignore
# pyright: ignore
# app.py

from flask import Flask, render_template, flash, redirect, url_for
from flask_migrate import Migrate

from config import (
    DATABASE_URL,
    SECRET_KEY,
    UPLOAD_FOLDER,
    ALLOWED_EXTENSIONS,
    MAX_CONTENT_LENGTH
)

from extension import db, login_manager
from models import User

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
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = SECRET_KEY

    # 🔥 Upload / Image config (IMPORTANT)
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["ALLOWED_EXTENSIONS"] = ALLOWED_EXTENSIONS
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

    # ------------------------------------
    # INITIALIZE EXTENSIONS
    # ------------------------------------
    db.init_app(app)
    login_manager.init_app(app)

    # Enable Flask-Migrate
    Migrate(app, db)

    login_manager.login_view = "auth.login"

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
        flash("Please log in to access that page.", "warning")
        return redirect(url_for("index"))

    # ------------------------------------
    # REGISTER BLUEPRINTS
    # ------------------------------------
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(teacher_bp, url_prefix="/teacher")
    app.register_blueprint(student_bp, url_prefix="/student")
    app.register_blueprint(chatbot_bp)

    # ------------------------------------
    # ROOT ROUTE
    # ------------------------------------
    @app.route("/")
    def index():
        return render_template("index.html")

    return app


# ------------------------------------
# RUN THE APPLICATION
# ------------------------------------
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
