import os
import json
import logging
from logging.handlers import RotatingFileHandler
import uuid
from flask import has_request_context, g, request

class JSONFormatter(logging.Formatter):
    """Formats log records as JSON, incorporating request ID, correlation ID and structured metadata."""
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }

        # Inject context information if inside request
        if has_request_context():
            # Generate or retrieve Request/Correlation ID
            request_id = getattr(g, "request_id", None)
            if not request_id:
                request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
                g.request_id = request_id
            
            correlation_id = request.headers.get("X-Correlation-ID", request_id)
            
            log_entry["request_id"] = request_id
            log_entry["correlation_id"] = correlation_id
            log_entry["path"] = request.path
            log_entry["method"] = request.method
            log_entry["remote_ip"] = request.remote_addr
        else:
            log_entry["request_id"] = None
            log_entry["correlation_id"] = None

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Merge extra fields if passed via extra={}
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry)


class LoggingService:
    """Configures structured JSON logging with rotation for CTF Arena."""
    _initialized = False

    @classmethod
    def init_app(cls, app):
        if cls._initialized:
            return
        
        is_vercel = os.environ.get("VERCEL")
        
        if not is_vercel:
            log_dir = os.path.abspath(os.path.join(app.root_path, "..", "logs"))
            os.makedirs(log_dir, exist_ok=True)

        formatter = JSONFormatter()

        # Helper to setup rotating file handler or stream handler
        def _setup_handler(filename, level):
            if is_vercel:
                import sys
                handler = logging.StreamHandler(sys.stdout)
            else:
                handler = RotatingFileHandler(
                    os.path.join(log_dir, filename),
                    maxBytes=10 * 1024 * 1024,  # 10MB
                    backupCount=5,
                    encoding="utf-8"
                )
            handler.setFormatter(formatter)
            handler.setLevel(level)
            return handler

        # Define application logs handlers
        app_handler = _setup_handler("app.log", logging.INFO)
        error_handler = _setup_handler("error.log", logging.ERROR)
        access_handler = _setup_handler("access.log", logging.INFO)
        audit_handler = _setup_handler("audit.log", logging.INFO)
        container_handler = _setup_handler("container.log", logging.INFO)

        # Hook to root/app loggers
        app.logger.setLevel(logging.INFO)
        app.logger.addHandler(app_handler)
        app.logger.addHandler(error_handler)

        # Prevent double logs on root loggers
        app.logger.propagate = False

        # Set up custom loggers
        access_logger = logging.getLogger("ctf.access")
        access_logger.setLevel(logging.INFO)
        access_logger.addHandler(access_handler)
        access_logger.propagate = False

        audit_logger = logging.getLogger("ctf.audit")
        audit_logger.setLevel(logging.INFO)
        audit_logger.addHandler(audit_handler)
        audit_logger.propagate = False

        container_logger = logging.getLogger("ctf.container")
        container_logger.setLevel(logging.INFO)
        container_logger.addHandler(container_handler)
        container_logger.propagate = False

        cls._initialized = True

    @staticmethod
    def log_access(status_code):
        """Logs HTTP request details to access.log."""
        logger = logging.getLogger("ctf.access")
        if has_request_context():
            logger.info(
                f"HTTP {request.method} {request.path} -> {status_code}",
                extra={"extra_fields": {"status_code": status_code}}
            )

    @staticmethod
    def log_audit(action, user_id=None, username=None, details=None):
        """Logs business/security event to audit.log."""
        logger = logging.getLogger("ctf.audit")
        extra_info = {
            "action": action,
            "user_id": user_id,
            "username": username,
            "details": details or {}
        }
        logger.info(
            f"Audit event: {action} (user: {username or 'anonymous'})",
            extra={"extra_fields": extra_info}
        )

    @staticmethod
    def log_container(instance_id, message, level="info"):
        """Logs container engine event to container.log."""
        logger = logging.getLogger("ctf.container")
        extra_info = {
            "instance_id": instance_id,
            "level": level
        }
        logger.info(
            f"[Instance #{instance_id}] {message}",
            extra={"extra_fields": extra_info}
        )
