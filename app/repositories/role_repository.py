from app.extensions import db
from app.models.role import Role

class RoleRepository:
    @staticmethod
    def get_by_name(name):
        return Role.query.filter_by(name=name).first()

    @staticmethod
    def get_all():
        return Role.query.all()

    @staticmethod
    def create(name):
        role = Role.query.filter_by(name=name).first()
        if not role:
            role = Role(name=name)
            db.session.add(role)
            db.session.commit()
        return role

    @staticmethod
    def setup_default_roles():
        default_roles = [
            "Super Admin",
            "Admin",
            "Moderator",
            "Challenge Author",
            "Participant",
            "Spectator",
            "Guest"
        ]
        roles_created = []
        for name in default_roles:
            role = Role.query.filter_by(name=name).first()
            if not role:
                role = Role(name=name)
                db.session.add(role)
                roles_created.append(name)
        if roles_created:
            db.session.commit()
        return roles_created
