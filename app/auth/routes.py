from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, current_user
from app.auth import auth_bp
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.utils.decorators import require_login
from app.extensions import limiter

def get_login_limit():
    return current_app.config.get("RATE_LIMIT_LOGIN", "5 per minute")

def get_register_limit():
    # Enforce registering limit
    return "3 per hour"

@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit(get_register_limit)
def register():
    if current_user.is_authenticated:
        return redirect(url_for("challenges.index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        display_name = request.form.get("display_name", "")
        email = request.form.get("email", "")

        user, err = AuthService.register_user(
            username=username,
            password=password,
            confirm_password=confirm_password,
            display_name=display_name,
            email=email
        )
        if err:
            error = err
        else:
            login_user(user)
            return redirect(url_for("challenges.index"))

    return render_template("register.html", error=error)

@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit(get_login_limit)
def login():
    if current_user.is_authenticated:
        return redirect(url_for("challenges.index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        ip = request.remote_addr
        ua = request.user_agent.string if request.user_agent else "Unknown"

        user, err = AuthService.authenticate_user(
            username=username,
            password=password,
            ip_address=ip,
            user_agent=ua
        )
        if err:
            error = err
        else:
            login_user(user, remember=remember)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("challenges.index"))

    return render_template("login.html", error=error)

@auth_bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        AuthService.logout(
            user_id=current_user.id,
            username=current_user.username,
            ip_address=request.remote_addr
        )
        logout_user()
    return redirect(url_for("auth.login"))

@auth_bp.route("/profile")
@require_login
def profile():
    profile_data = UserService.get_user_profile_data(current_user.username)
    if not profile_data:
        return redirect(url_for("challenges.index"))
    return render_template("profile.html", **profile_data)
