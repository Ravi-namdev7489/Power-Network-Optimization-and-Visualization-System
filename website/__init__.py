from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_session import Session
import pymysql
from config import Config

pymysql.install_as_MySQLdb()

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_class=Config):   # ← default Config class
    app = Flask(__name__)

    # -------------------------------
    # Load configuration from config.py
    # -------------------------------
    app.config.from_object(config_class)

    # -------------------------------
    # Initialize extensions
    # -------------------------------
    db.init_app(app)
    login_manager.init_app(app)
    Session(app)

    # -------------------------------
    # Import models
    # -------------------------------
    from .models import Signupuser

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Signupuser, user_id)

    login_manager.login_view = "auth.login"

    # -------------------------------
    # Register Blueprints
    # -------------------------------
    from .auth import auth_bp
    from .views import views_bp
    from .admin import admin_bp
    from .modling import modling_bp
    from .history import history_bp
    from .map import bp_map

    app.register_blueprint(auth_bp)
    app.register_blueprint(views_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(modling_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(bp_map)

    # -------------------------------
    # Create DB tables
    # -------------------------------
    with app.app_context():
        db.create_all()

    return app
