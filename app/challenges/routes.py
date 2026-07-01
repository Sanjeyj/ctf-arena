import os
from flask import render_template, request, redirect, make_response, jsonify, url_for, send_from_directory, current_app
from flask_login import current_user
from app.challenges import challenges_bp
from app.services.challenge_service import ChallengeService
from app.services.hint_service import HintService
from app.utils.decorators import require_login

@challenges_bp.route("/")
@require_login
def index():
    username = current_user.username
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
    from jinja2 import TemplateNotFound
    username = current_user.username
    ch, solved = ChallengeService.get_challenge(ch_id, username)
    if not ch:
        return redirect(url_for("challenges.index"))
    
    # We load challenges list so that template namespace resolved checks work perfectly
    from app.repositories.challenge_repository import ChallengeRepository
    challenges = ChallengeRepository.get_all(include_hidden=False)
    
    # Fetch active hints mapped for active user
    challenge_record = ChallengeService.get_challenge_by_any_id(ch_id)
    hints = HintService.get_hints_for_challenge(challenge_record.id, current_user.id) if challenge_record else []
    
    # Fetch files list
    files = challenge_record.files if challenge_record else []
    
    # Try per-challenge template first; fall back to generic template for CMS-created challenges
    specific_template = f"ch_{ch_id}.html"
    try:
        current_app.jinja_env.get_template(specific_template)
        template_name = specific_template
    except TemplateNotFound:
        template_name = "ch_generic.html"

    return render_template(
        template_name,
        ch=ch,
        ch_id=ch_id,
        solved=solved,
        username=username,
        challenges=challenges,
        hints=hints,
        files=files
    )

from app.extensions import limiter

def get_submit_limit():
    from flask import current_app
    return current_app.config.get("RATE_LIMIT_SUBMIT", "10 per minute")

@challenges_bp.route("/submit/<ch_id>", methods=["POST"])
@require_login
@limiter.limit(get_submit_limit)
def submit(ch_id):
    username = current_user.username
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
    if query.strip():
        return jsonify({"success": True, "results": results})
    return jsonify({"results": []})

@challenges_bp.route("/reset")
@require_login
def reset():
    username = current_user.username
    ChallengeService.reset_progress(username)
    return redirect(url_for("challenges.index"))

# Secure download tracker route
@challenges_bp.route("/uploads/<filename>")
@require_login
def download_file(filename):
    from app.models.challenge_file import ChallengeFile
    from app.services.file_service import FileService
    
    safe_name = os.path.basename(filename)
    file_record = ChallengeFile.query.filter_by(stored_filename=safe_name).first()
    if file_record:
        FileService.track_download(file_record.id)
        
    upload_folder = os.path.join(current_app.root_path, "..", "instance", "uploads")
    response = send_from_directory(
        upload_folder,
        safe_name,
        as_attachment=True,
        download_name=file_record.original_filename if file_record else safe_name
    )
    response.headers["Content-Security-Policy"] = "default-src 'none'"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

# Hint unlock route
@challenges_bp.route("/hints/<int:hint_id>/unlock", methods=["POST"])
@require_login
def unlock_hint(hint_id):
    success, err = HintService.unlock_hint(hint_id, current_user.id)
    if success:
        h = HintService.get_hint_by_id(hint_id)
        return jsonify({"success": True, "content": h.content})
    return jsonify({"success": False, "msg": err})
