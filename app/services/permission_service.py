from app.models.role import Role

class PermissionService:
    @staticmethod
    def has_permission(user, permission_name):
        if user is None or user.is_anonymous:
            # Check anonymous permissions (mapped to Guest)
            guest_role = Role.query.filter_by(name="Guest").first()
            if guest_role:
                return any(p.name == permission_name for p in guest_role.permissions)
            return permission_name == "view_challenges"
            
        # Admin / Super Admin override
        user_roles = [r.name for r in user.roles]
        if "Super Admin" in user_roles or "Admin" in user_roles:
            return True

        # Check permissions assigned to user's roles
        for role in user.roles:
            for perm in role.permissions:
                if perm.name == permission_name or perm.name == "full_access":
                    return True
        return False

    @staticmethod
    def has_role(user, role_name):
        if user is None or user.is_anonymous:
            return role_name == "Guest"
        return any(r.name == role_name for r in user.roles)
