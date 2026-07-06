import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, jsonify, request
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import config_by_name
from app.context_processors import utility_processors
from app.cli import register_cli_commands
from app.services.logging_service import LoggingService
from app.services.metrics_service import MetricsService

def create_app(config_name="default"):
    # Point templates and static folders back to root directories
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates"))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))
    
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    
    # Load config
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))
    
    # Configure Flask-Limiter settings
    app.config["RATELIMIT_DEFAULT"] = app.config.get("RATE_LIMIT_GLOBAL", "100 per minute")
    if app.config.get("TESTING"):
        app.config["RATELIMIT_ENABLED"] = False

    # Initialize Extensions
    from app.extensions import db, migrate, login_manager, csrf, limiter
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
    limiter.init_app(app)
    
    # Configure Jinja override template loader for plugins
    if app.jinja_loader:
        old_loader = app.jinja_loader
        class OverrideLoader(object):
            def get_source(self, environment, template):
                from app.services.plugin_service import PluginService
                target = PluginService.get_template_override(template)
                if os.path.isabs(target) or "plugins" in target.replace("\\", "/"):
                    if os.path.exists(target):
                        with open(target, 'r', encoding='utf-8') as f:
                            source = f.read()
                        return source, target, lambda: True
                return old_loader.get_source(environment, target)
            def list_templates(self):
                return old_loader.list_templates()
        app.jinja_loader = OverrideLoader()
    
    # Setup directories
    os.makedirs(os.path.join(app.root_path, "..", "logs"), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, "..", "instance"), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, "..", "uploads"), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, "..", "plugins"), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, "..", "themes"), exist_ok=True)
    
    # Setup structured JSON logging
    LoggingService.init_app(app)
    
    # Context processors
    app.context_processor(utility_processors)
    
    # Apply ProxyFix middleware if configured
    proxies_count = app.config.get("TRUSTED_PROXIES", 0)
    if proxies_count > 0:
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=proxies_count,
            x_proto=proxies_count,
            x_host=proxies_count,
            x_port=proxies_count,
            x_prefix=proxies_count
        )

    # Register blueprints
    register_blueprints(app)
    
    # Exempt API from CSRF protection
    from app.api import api_bp
    from app.ai import ai_bp
    from app.organization import org_bp
    from app.cyberrange import cyberrange_bp
    from app.lms import lms_bp
    from app.soc import soc_bp
    from app.research import research_bp
    from app.ecosystem import ecosystem_bp
    from app.autonomous import autonomous_bp
    from app.defense import defense_bp
    from app.secos import secos_bp
    from app.cloud import cloud_bp
    from app.resilience import resilience_bp
    from app.enterprise import enterprise_bp
    from app.intelligence import intelligence_bp
    from app.civilization import civilization_bp
    from app.command import command_bp
    from app.universe import universe_bp
    from app.control_plane import control_plane_bp
    from app.assurance import assurance_bp
    from app.operations import operations_bp
    csrf.exempt(api_bp)
    csrf.exempt(ai_bp)
    csrf.exempt(org_bp)
    csrf.exempt(cyberrange_bp)
    csrf.exempt(lms_bp)
    csrf.exempt(soc_bp)
    csrf.exempt(research_bp)
    csrf.exempt(ecosystem_bp)
    csrf.exempt(autonomous_bp)
    csrf.exempt(defense_bp)
    csrf.exempt(secos_bp)
    csrf.exempt(cloud_bp)
    csrf.exempt(resilience_bp)
    csrf.exempt(enterprise_bp)
    csrf.exempt(intelligence_bp)
    csrf.exempt(civilization_bp)
    csrf.exempt(command_bp)
    csrf.exempt(universe_bp)
    csrf.exempt(control_plane_bp)
    csrf.exempt(assurance_bp)
    csrf.exempt(operations_bp)



    # Hook up HTTP security headers after request
    @app.after_request
    def inject_security_headers(response):
        # Strict-Transport-Security (HSTS)
        if app.config.get("PREFERRED_URL_SCHEME") == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content-Security-Policy (CSP)
        if "Content-Security-Policy" not in response.headers:
            csp_config = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data:; "
                "frame-src 'none'; "
                "connect-src 'self'"
            )
            response.headers["Content-Security-Policy"] = csp_config
        
        # Permissions-Policy
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        
        return response

    # Metrics Hookups
    from app.middleware.tenant_middleware import OrganizationResolverMiddleware
    app.before_request(OrganizationResolverMiddleware.resolve_tenant)
    app.before_request(MetricsService.before_request)

    
    @app.after_request
    def log_and_metrics_after_request(response):
        response = MetricsService.after_request(response)
        LoggingService.log_access(response.status_code)
        return response

    # --- Health & Observability Routes ---
    
    @app.route("/live", methods=["GET"])
    def liveness_probe():
        """Liveness check endpoint."""
        return jsonify({"status": "live", "ok": True}), 200

    @app.route("/ready", methods=["GET"])
    def readiness_probe():
        """Readiness check verifying database and disk writes."""
        # Check database connectivity
        try:
            db.session.execute(db.select(1)).first()
        except Exception as e:
            return jsonify({"status": "unready", "error": f"Database: {str(e)}", "ok": False}), 503
        
        # Check filesystem write access
        try:
            inst_dir = os.path.abspath(os.path.join(app.root_path, "..", "instance"))
            os.makedirs(inst_dir, exist_ok=True)
            test_file = os.path.join(inst_dir, ".write_probe")
            with open(test_file, "w") as f:
                f.write("probe")
            os.remove(test_file)
        except Exception as e:
            return jsonify({"status": "unready", "error": f"Filesystem: {str(e)}", "ok": False}), 503

        return jsonify({"status": "ready", "ok": True}), 200

    @app.route("/health", methods=["GET"])
    def health_check():
        """Detailed health check endpoint."""
        # 1. DB check
        db_ok = True
        db_err = None
        try:
            db.session.execute(db.select(1)).first()
        except Exception as e:
            db_ok = False
            db_err = str(e)

        # 2. Docker check
        from app.services.docker_service import DockerService, _probe_docker
        docker_mode = DockerService.mode()
        docker_ok = True
        if docker_mode == "real":
            if not _probe_docker():
                docker_ok = False

        # 3. Uploads directory check
        uploads_dir = os.path.abspath(os.path.join(app.root_path, "..", "uploads"))
        uploads_ok = os.path.exists(uploads_dir) and os.access(uploads_dir, os.W_OK)

        # 4. Configuration Check
        config_ok = bool(app.config.get("SECRET_KEY") and app.config.get("SECRET_KEY") != "ctf_super_secret_2024")

        overall_ok = db_ok and docker_ok and uploads_ok

        return jsonify({
            "status": "healthy" if overall_ok else "unhealthy",
            "ok": overall_ok,
            "database": {"ok": db_ok, "error": db_err},
            "docker": {"ok": docker_ok, "mode": docker_mode},
            "uploads": {"ok": uploads_ok},
            "configuration": {"ok": config_ok}
        }), (200 if overall_ok else 503)

    @app.route("/metrics", methods=["GET"])
    def prometheus_metrics():
        """Prometheus compatible metrics endpoint."""
        if not app.config.get("METRICS_ENABLED", True):
            return "Metrics disabled", 403
        return MetricsService.get_prometheus_metrics(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    # --- Database Transaction Safety ---
    @app.teardown_request
    def rollback_on_exception(exc):
        """Ensure DB session is rolled back if an exception occurred during the request."""
        if exc is not None:
            try:
                db.session.rollback()
            except Exception:
                pass

    # Register error handlers
    register_error_handlers(app)
    
    # Register CLI
    register_cli_commands(app)
    
    # Load enabled plugins on startup
    with app.app_context():
        try:
            from app.services.plugin_service import PluginService
            PluginService.load_enabled_plugins()
        except Exception as e:
            app.logger.error(f"Error loading enabled plugins: {str(e)}")

    return app

def register_blueprints(app):
    # Core Blueprints containing logic
    from app.auth import auth_bp
    from app.challenges import challenges_bp
    from app.scoreboard import scoreboard_bp
    from app.admin import admin_bp
    from app.api import api_bp
    from app.docker import docker_bp
    from app.ai import ai_bp
    from app.organization import org_bp
    from app.cyberrange import cyberrange_bp
    from app.lms import lms_bp
    from app.soc import soc_bp
    from app.research import research_bp
    from app.ecosystem import ecosystem_bp
    
    from app.research import research_bp
    from app.ecosystem import ecosystem_bp
    from app.autonomous import autonomous_bp
    from app.defense import defense_bp
    from app.secos import secos_bp
    from app.cloud import cloud_bp
    from app.resilience import resilience_bp
    from app.enterprise import enterprise_bp
    from app.intelligence import intelligence_bp
    from app.civilization import civilization_bp
    from app.command import command_bp
    from app.universe import universe_bp
    from app.control_plane import control_plane_bp
    from app.assurance import assurance_bp
    from app.operations import operations_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(challenges_bp)
    app.register_blueprint(scoreboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(docker_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(org_bp)
    app.register_blueprint(cyberrange_bp)
    app.register_blueprint(lms_bp)
    app.register_blueprint(soc_bp)
    app.register_blueprint(research_bp)
    app.register_blueprint(ecosystem_bp)
    app.register_blueprint(autonomous_bp)
    app.register_blueprint(defense_bp)
    app.register_blueprint(secos_bp)
    app.register_blueprint(cloud_bp)
    app.register_blueprint(resilience_bp)
    app.register_blueprint(enterprise_bp)
    app.register_blueprint(intelligence_bp)
    app.register_blueprint(civilization_bp)
    app.register_blueprint(command_bp)
    app.register_blueprint(universe_bp)
    app.register_blueprint(control_plane_bp)
    app.register_blueprint(assurance_bp)
    app.register_blueprint(operations_bp)


    
    # Blueprint Skeletons for future milestones
    skeletons = [
        "analytics", "announcements", "audit", "categories", "certificates",
        "competitions", "files", "flags", "hints", "notifications",
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
