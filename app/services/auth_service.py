from app.repositories.user_repository import UserRepository
from flask import session

class AuthService:
    @staticmethod
    def register_user(username):
        username = username.strip()
        if not username:
            return None, "Please enter a display name."
        if len(username) > 32:
            return None, "Name must be 32 characters or fewer."
        if username.lower() == "admin":
            return None, "That name is reserved."
        
        user = UserRepository.create(username)
        session["user"] = username
        return user, None

    @staticmethod
    def admin_login(username, password, admin_user, admin_pass):
        if username == admin_user and password == admin_pass:
            session["is_admin"] = True
            return True
        return False

    @staticmethod
    def logout():
        session.pop("user", None)

    @staticmethod
    def admin_logout():
        session.pop("is_admin", None)
