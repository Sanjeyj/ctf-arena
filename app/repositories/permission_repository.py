from app.extensions import db
from app.models.role import Role, Permission

class PermissionRepository:
    @staticmethod
    def get_by_name(name):
        return Permission.query.filter_by(name=name).first()

    @staticmethod
    def create(name):
        perm = Permission.query.filter_by(name=name).first()
        if not perm:
            perm = Permission(name=name)
            db.session.add(perm)
            db.session.commit()
        return perm

    @staticmethod
    def setup_default_permissions_and_roles_map():
        # Setup all default permissions
        permissions_list = [
            "view_challenges",
            "submit_flag",
            "create_challenge",
            "manage_challenges",
            "manage_users",
            "manage_settings",
            "full_access"
        ]
        
        perm_objs = {}
        for p_name in permissions_list:
            perm = Permission.query.filter_by(name=p_name).first()
            if not perm:
                perm = Permission(name=p_name)
                db.session.add(perm)
                db.session.flush()
            perm_objs[p_name] = perm
        db.session.commit()

        # Define default role mappings
        role_assignments = {
            "Guest": ["view_challenges"],
            "Spectator": ["view_challenges"],
            "Participant": ["view_challenges", "submit_flag"],
            "Challenge Author": ["view_challenges", "submit_flag", "create_challenge"],
            "Moderator": ["view_challenges", "submit_flag", "create_challenge", "manage_challenges"],
            "Admin": ["view_challenges", "submit_flag", "create_challenge", "manage_challenges", "manage_users", "manage_settings"],
            "Super Admin": ["view_challenges", "submit_flag", "create_challenge", "manage_challenges", "manage_users", "manage_settings", "full_access"]
        }

        for r_name, p_names in role_assignments.items():
            role = Role.query.filter_by(name=r_name).first()
            if role:
                current_perms = [p.name for p in role.permissions]
                for p_name in p_names:
                    if p_name not in current_perms:
                        role.permissions.append(perm_objs[p_name])
        db.session.commit()
