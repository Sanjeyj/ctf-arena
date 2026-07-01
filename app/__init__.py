import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, jsonify

from app.config import config_by_name
from app.context_processors import utility_processors
from app.cli import register_cli_commands

def create_app(config_name="default"):
    # Point templates and static folders back to root directories
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    
    # Load config
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))
    
    # Initialize Extensions
    from app.extensions import db, migrate, login_manager, csrf
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Configure Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "error"
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        # Return active, non-deleted user
        return User.query.filter_by(id=int(user_id), is_deleted=False).first()
        
    csrf.init_app(app)
    
    # Setup directories
    os.makedirs(os.path.join(app.root_path, "..", "logs"), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, "..", "instance"), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, "..", "uploads"), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, "..", "plugins"), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, "..", "themes"), exist_ok=True)
    
    # Setup logging
    setup_logging(app)
    
    # Context processors
    app.context_processor(utility_processors)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register CLI
    register_cli_commands(app)
    
    return app

def register_blueprints(app):
    # Core Blueprints containing logic
    from app.auth import auth_bp
    from app.challenges import challenges_bp
    from app.scoreboard import scoreboard_bp
    from app.admin import admin_bp
    from app.api import api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(challenges_bp)
    app.register_blueprint(scoreboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    
    # Blueprint Skeletons for future milestones
    skeletons = [
        "analytics", "announcements", "audit", "categories", "certificates",
        "competitions", "docker", "files", "flags", "hints", "notifications",
        "plugins", "scheduler", "submissions", "teams", "themes", "users"
    ]
    
    # Dynamically import and register skeletons to keep clean
    for bp_name in skeletons:
        module = __import__(f"app.{bp_name}", fromlist=[f"{bp_name}_bp"])
        bp = getattr(module, f"{bp_name}_bp")
        app.register_blueprint(bp)

def register_error_handlers(app):
    @app.errorhandler(401)
    def unauthorized(e):
        return render_template("errors/401.html"), 401
        
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403
        
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404
        
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("errors/500.html"), 500

def setup_logging(app):
    log_dir = os.path.abspath(os.path.join(app.root_path, "..", "logs"))
    
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )
    
    # General app log
    app_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"), maxBytes=1024000, backupCount=10
    )
    app_handler.setFormatter(formatter)
    app_handler.setLevel(logging.INFO)
    app.logger.addHandler(app_handler)
    
    # Error log
    err_handler = RotatingFileHandler(
        os.path.join(log_dir, "error.log"), maxBytes=1024000, backupCount=10
    )
    err_handler.setFormatter(formatter)
    err_handler.setLevel(logging.ERROR)
    app.logger.addHandler(err_handler)
    
    # Access log
    access_handler = RotatingFileHandler(
        os.path.join(log_dir, "access.log"), maxBytes=1024000, backupCount=10
    )
    access_handler.setFormatter(formatter)
    access_handler.setLevel(logging.INFO)
    
    # Set logger to INFO globally
    app.logger.setLevel(logging.INFO)
    app.logger.info("CTF Arena Enterprise startup initialized.")
