from flask import render_template, request, redirect, session, url_for
from app.auth import auth_bp
from app.services.auth_service import AuthService

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user" in session:
        return redirect(url_for("challenges.index"))

    error = None
    if request.method == "POST":
        name = request.form.get("name", "")
        user, err = AuthService.register_user(name)
        if err:
            error = err
        else:
            return redirect(url_for("challenges.index"))

    return render_template("register.html", error=error)

@auth_bp.route("/logout")
def logout():
    AuthService.logout()
    return redirect(url_for("auth.register"))
