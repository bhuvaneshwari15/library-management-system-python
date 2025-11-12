from flask import Flask, render_template, flash, redirect, url_for
from config import DATABASE_URL, SECRET_KEY
from extension import db, login_manager
from models import User

# Import blueprints
from blueprints.auth import auth_bp
from blueprints.admin import admin_bp
from blueprints.teacher import teacher_bp
from blueprints.student import student_bp


def create_app():
    app = Flask(__name__)

    # ----------------------------
    # App Configuration
    # ----------------------------
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = SECRET_KEY

    # ----------------------------
    # Initialize Extensions
    # ----------------------------
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # ----------------------------
    # User Loader
    # ----------------------------
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ----------------------------
    # Unauthorized Handler
    # ----------------------------
    @login_manager.unauthorized_handler
    def unauthorized():
        flash('Please log in to access that page.', 'warning')
        return redirect(url_for('index'))  # Redirect to index.html, not login page

    # ----------------------------
    # Register Blueprints
    # ----------------------------
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(teacher_bp, url_prefix='/teacher')
    app.register_blueprint(student_bp, url_prefix='/student')

    # ----------------------------
    # Root Route
    # ----------------------------
    @app.route('/')
    def index():
        return render_template('index.html')

    return app


# ----------------------------
# Run the Application
# ----------------------------
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
