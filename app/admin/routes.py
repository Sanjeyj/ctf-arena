from flask import render_template, request, redirect, jsonify, session, url_for, current_app
from app.admin import admin_bp
from app.services.auth_service import AuthService
from app.services.admin_service import AdminService
from app.services.scoreboard_service import ScoreboardService
from app.utils.decorators import require_admin

@admin_bp.route("/admin/login", methods=["GET", "POST"])
def login():
    if session.get("is_admin"):
        return redirect(url_for("admin.dashboard"))
    error = None
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        admin_user = current_app.config["ADMIN_USER"]
        admin_pass = current_app.config["ADMIN_PASSWORD"]
        if AuthService.admin_login(u, p, admin_user, admin_pass):
            return redirect(url_for("admin.dashboard"))
        error = "Invalid credentials."
    return render_template("admin_login.html", error=error)

@admin_bp.route("/admin/logout")
def logout():
    AuthService.admin_logout()
    return redirect(url_for("admin.login"))

@admin_bp.route("/admin")
@require_admin
def dashboard():
    leaderboard, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        "admin.html",
        challenges=challenges,
        leaderboard=leaderboard,
        stats=stats
    )

@admin_bp.route("/admin/api/stats")
@require_admin
def api_stats():
    leaderboard, stats, _, challenges = ScoreboardService.get_scoreboard_data()
    return jsonify({
        "leaderboard": leaderboard,
        "stats": stats,
        "challenges": {k: {"title": v["title"], "points": v["points"]} for k, v in challenges.items()},
    })

@admin_bp.route("/admin/reset", methods=["POST"])
@require_admin
def reset():
    AdminService.reset_all()
    return jsonify({"success": True})
