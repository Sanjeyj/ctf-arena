from flask import render_template, request, redirect, make_response, jsonify, session, url_for
from app.challenges import challenges_bp
from app.services.challenge_service import ChallengeService
from app.utils.decorators import require_login

@challenges_bp.route("/")
@require_login
def index():
    username = session["user"]
    challenges, solved, total_pts, registered_at = ChallengeService.get_dashboard_context(username)
    return render_template(
        "index.html",
        challenges=challenges,
        solved=solved,
        total_pts=total_pts,
        username=username,
        registered_at=registered_at
    )

@challenges_bp.route("/challenge/<ch_id>")
@require_login
def challenge(ch_id):
    username = session["user"]
    ch, solved = ChallengeService.get_challenge(ch_id, username)
    if not ch:
        return redirect(url_for("challenges.index"))
    
    # We load challenges list so that template namespace resolved checks work perfectly
    from app.repositories.challenge_repository import ChallengeRepository
    challenges = ChallengeRepository.get_all()
    
    return render_template(f"ch_{ch_id}.html", ch=ch, solved=solved, username=username, challenges=challenges)

@challenges_bp.route("/submit/<ch_id>", methods=["POST"])
@require_login
def submit(ch_id):
    username = session["user"]
    flag = request.form.get("flag", "")
    success, msg, points = ChallengeService.submit_flag(ch_id, username, flag)
    return jsonify({"success": success, "msg": msg, "points": points})

@challenges_bp.route("/cookie-check")
def cookie_check():
    role = request.cookies.get("role", "guest")
    data, is_admin = ChallengeService.verify_admin_cookie(role)
    if is_admin:
        return jsonify(data)
    resp = make_response(jsonify(data))
    resp.set_cookie("role", "guest")
    return resp

@challenges_bp.route("/vault-search")
def vault_search():
    query = request.args.get("query", "")
    results = ChallengeService.search_vault(query)
    # Match exact return JSON format
    if query.strip():
        return jsonify({"success": True, "results": results})
    return jsonify({"results": []})

@challenges_bp.route("/reset")
@require_login
def reset():
    username = session["user"]
    ChallengeService.reset_progress(username)
    return redirect(url_for("challenges.index"))

@challenges_bp.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "version": "v2"
    })
