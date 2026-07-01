import datetime
from flask import current_app, request
from app.extensions import db
from app.models.user import User
from app.models.login_history import LoginHistory
from app.models.audit import AuditLog

class SessionService:
    @staticmethod
    def is_user_locked_out(user):
        if not user:
            return False
        max_attempts = current_app.config.get("MAX_LOGIN_ATTEMPTS", 5)
        return user.failed_login_attempts >= max_attempts

    @staticmethod
    def record_login_attempt(username, success, ip_address=None, user_agent=None):
        user = User.query.filter_by(username=username, is_deleted=False).first()
        user_id = user.id if user else None
        
        # Log to LoginHistory
        attempt = LoginHistory(
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success
        )
        db.session.add(attempt)

        # Log to AuditLog and update lockout status
        if success:
            if user:
                user.failed_login_attempts = 0
                user.last_login = datetime.datetime.utcnow()
                user.last_ip = ip_address
                db.session.add(user)
                
            audit = AuditLog(
                user_id=user_id,
                action="user_login_success" if user else "anonymous_login_success",
                ip_address=ip_address,
                details=f"Username: {username} | UA: {user_agent}"
            )
            db.session.add(audit)
        else:
            if user:
                user.failed_login_attempts += 1
                db.session.add(user)
                # Check if this attempt triggered a lockout
                max_attempts = current_app.config.get("MAX_LOGIN_ATTEMPTS", 5)
                if user.failed_login_attempts >= max_attempts:
                    lockout_audit = AuditLog(
                        user_id=user_id,
                        action="account_locked",
                        ip_address=ip_address,
                        details=f"Account locked due to {user.failed_login_attempts} failed attempts."
                    )
                    db.session.add(lockout_audit)
                    
            audit = AuditLog(
                user_id=user_id,
                action="user_login_failed",
                ip_address=ip_address,
                details=f"Username: {username} | UA: {user_agent}"
            )
            db.session.add(audit)
            
        db.session.commit()

    @staticmethod
    def log_logout(user_id, username, ip_address=None):
        audit = AuditLog(
            user_id=user_id,
            action="user_logout",
            ip_address=ip_address,
            details=f"Username: {username} logged out."
        )
        db.session.add(audit)
        db.session.commit()

    @staticmethod
    def log_audit_event(user_id, action, details=None, ip_address=None):
        audit = AuditLog(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            details=details
        )
        db.session.add(audit)
        db.session.commit()
