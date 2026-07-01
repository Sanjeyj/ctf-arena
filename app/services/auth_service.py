import re
import bcrypt
from flask import current_app, request
from app.repositories.user_repository import UserRepository
from app.services.session_service import SessionService

def validate_password_strength(password, config):
    min_len = config.get("PASSWORD_MIN_LENGTH", 8)
    if len(password) < min_len:
        return f"Password must be at least {min_len} characters long."
        
    if config.get("PASSWORD_REQUIRE_UPPER", True) and not any(c.isupper() for c in password):
        return "Password must contain at least one uppercase letter."
        
    if config.get("PASSWORD_REQUIRE_LOWER", True) and not any(c.islower() for c in password):
        return "Password must contain at least one lowercase letter."
        
    if config.get("PASSWORD_REQUIRE_DIGIT", True) and not any(c.isdigit() for c in password):
        return "Password must contain at least one digit."
        
    if config.get("PASSWORD_REQUIRE_SPECIAL", True) and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "Password must contain at least one special character."
        
    return None

def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def check_password(password, hashed):
    if not hashed:
        return False
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

class AuthService:
    @staticmethod
    def register_user(username, password, confirm_password, display_name=None, email=None, role_name="Participant"):
        username = username.strip()
        if not username:
            return None, "Please enter a username."
        if len(username) > 32:
            return None, "Username must be 32 characters or fewer."
        if username.lower() == "admin":
            return None, "That username is reserved."
            
        if UserRepository.get_by_name(username):
            return None, "That username is already taken."
            
        if email:
            email = email.strip()
            if UserRepository.get_by_email(email):
                return None, "That email is already registered."

        if not password:
            return None, "Please enter a password."
        if password != confirm_password:
            return None, "Passwords do not match."
            
        err = validate_password_strength(password, current_app.config)
        if err:
            return None, err
            
        hashed = hash_password(password)
        
        user = UserRepository.create(
            username=username,
            password_hash=hashed,
            display_name=display_name.strip() if display_name else None,
            email=email or None,
            role_name=role_name
        )
        
        ip = request.remote_addr if request else None
        SessionService.log_audit_event(
            user_id=user.id,
            action="user_registered",
            details=f"Username: {username} registered as {role_name}.",
            ip_address=ip
        )
        
        return user, None

    @staticmethod
    def authenticate_user(username, password, ip_address=None, user_agent=None):
        username = username.strip()
        user = UserRepository.get_by_name(username)
        
        if user and SessionService.is_user_locked_out(user):
            SessionService.record_login_attempt(username, False, ip_address, user_agent)
            return None, "Account is locked. Please contact an administrator."

        if user and check_password(password, user.password_hash):
            SessionService.record_login_attempt(username, True, ip_address, user_agent)
            return user, None
        else:
            SessionService.record_login_attempt(username, False, ip_address, user_agent)
            if user and SessionService.is_user_locked_out(user):
                return None, "Invalid credentials. Your account is now locked."
            return None, "Invalid credentials."

    @staticmethod
    def logout(user_id, username, ip_address=None):
        SessionService.log_logout(user_id, username, ip_address)
