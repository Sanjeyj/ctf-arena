from functools import wraps
from flask import session, redirect, url_for, abort

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.register"))
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)
    return decorated_function
