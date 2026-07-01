from app.extensions import db
from app.models.user import User
from app.models.role import Role

class UserRepository:
    @staticmethod
    def get_by_id(user_id):
        return User.query.filter_by(id=user_id, is_deleted=False).first()

    @staticmethod
    def get_by_name(username):
        return User.query.filter_by(username=username, is_deleted=False).first()

    @staticmethod
    def get_by_email(email):
        if not email:
            return None
        return User.query.filter_by(email=email, is_deleted=False).first()

    @staticmethod
    def create(username, password_hash=None, display_name=None, email=None, role_name="Participant"):
        role = Role.query.filter_by(name=role_name).first()
        user = User(
            username=username,
            password_hash=password_hash,
            display_name=display_name,
            email=email
        )
        if role:
            user.roles.append(role)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def get_all_participants():
        return User.query.join(User.roles).filter(
            Role.name == "Participant",
            User.is_deleted == False
        ).all()

    @staticmethod
    def list_all_users():
        return User.query.filter_by(is_deleted=False).all()
