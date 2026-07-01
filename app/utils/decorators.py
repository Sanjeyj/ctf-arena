from functools import wraps
from flask import abort, redirect, url_for
from flask_login import current_user
from app.services.permission_service import PermissionService

def require_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not PermissionService.has_permission(current_user, "manage_settings"):
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    return require_admin(f)

def moderator_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not PermissionService.has_permission(current_user, "manage_challenges"):
            abort(403)
        return f(*args, **kwargs)
    return decorated

def author_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not PermissionService.has_permission(current_user, "create_challenge"):
            abort(403)
        return f(*args, **kwargs)
    return decorated

def participant_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not PermissionService.has_permission(current_user, "submit_flag"):
            abort(403)
        return f(*args, **kwargs)
    return decorated

def permission_required(permission_name):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated or not PermissionService.has_permission(current_user, permission_name):
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator
