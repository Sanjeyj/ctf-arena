import os
from flask import render_template, request, redirect, jsonify, url_for, current_app, flash
from flask_login import login_user, logout_user, current_user
from app.admin import admin_bp
from app.services.auth_service import AuthService
from app.services.admin_service import AdminService
from app.services.scoreboard_service import ScoreboardService
from app.services.permission_service import PermissionService
from app.services.challenge_service import ChallengeService
from app.services.category_service import CategoryService
from app.services.flag_service import FlagService
from app.services.hint_service import HintService
from app.services.file_service import FileService
from app.extensions import limiter
from app.utils.decorators import require_admin

def get_login_limit():
    from flask import current_app
    return current_app.config.get("RATE_LIMIT_LOGIN", "5 per minute")

@admin_bp.route("/admin/login", methods=["GET", "POST"])
@limiter.limit(get_login_limit)
def login():
    if current_user.is_authenticated and PermissionService.has_permission(current_user, "manage_settings"):
        return redirect(url_for("admin.dashboard"))
        
    error = None
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        
        ip = request.remote_addr
        ua = request.user_agent.string if request.user_agent else "Unknown"
        
        user, err = AuthService.authenticate_user(u, p, ip_address=ip, user_agent=ua)
        
        if user:
            if PermissionService.has_permission(user, "manage_settings"):
                login_user(user)
                return redirect(url_for("admin.dashboard"))
            else:
                error = "Access denied: Account lacks administrative privileges."
        else:
            error = err or "Invalid credentials."
            
    return render_template("admin_login.html", error=error)

@admin_bp.route("/admin/logout")
def logout():
    if current_user.is_authenticated:
        AuthService.logout(
            user_id=current_user.id,
            username=current_user.username,
            ip_address=request.remote_addr
        )
        logout_user()
    return redirect(url_for("admin.login"))

@admin_bp.route("/admin")
@require_admin
def dashboard():
    leaderboard, stats, challenges = AdminService.get_dashboard_stats()
    
    # Enrich dashboard stats with dynamic CMS logs
    cms_challenges = ChallengeService.list_challenges()
    solved_counts = [ch.solve_count for ch in cms_challenges if ch.solve_count > 0]
    
    most_solved = "None"
    least_solved = "None"
    if cms_challenges:
        active = [c for c in cms_challenges if c.solve_count > 0]
        if active:
            most_solved = max(active, key=lambda c: c.solve_count).title
            least_solved = min(active, key=lambda c: c.solve_count).title
            
    # Inject extra statistics overview parameters
    stats["most_solved_ch"] = most_solved
    stats["least_solved_ch"] = least_solved
    stats["total_challenges_count"] = len(cms_challenges)
    stats["hidden_challenges_count"] = len([c for c in cms_challenges if not c.visible])

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
    # Rebuild challenges solve counts to 0
    ChallengeService.rebuild_all_challenge_points()
    return jsonify({"success": True})

# ── Categories CRUD ──────────────────────────────────────────
@admin_bp.route("/admin/categories", methods=["GET", "POST"])
@require_admin
def categories():
    error = None
    message = None
    if request.method == "POST":
        name = request.form.get("name")
        desc = request.form.get("description")
        color = request.form.get("color", "#00f0ff")
        icon = request.form.get("icon")
        try:
            order = int(request.form.get("display_order", 0))
        except ValueError:
            order = 0
        visible = request.form.get("visible") == "on"

        cat, err = CategoryService.create_category(name, desc, color, icon, order, visible)
        if err:
            error = err
        else:
            message = "Category created successfully."

    all_cats = CategoryService.get_all_categories()
    return render_template("admin_categories.html", categories=all_cats, error=error, message=message)

@admin_bp.route("/admin/categories/<int:cat_id>/delete")
@require_admin
def delete_category(cat_id):
    success, err = CategoryService.delete_category(cat_id)
    return redirect(url_for("admin.categories"))

# ── Challenges CRUD ──────────────────────────────────────────
@admin_bp.route("/admin/challenges", methods=["GET"])
@require_admin
def challenges():
    search = request.args.get("search")
    cat_id = request.args.get("category_id")
    if cat_id:
        try:
            cat_id = int(cat_id)
        except ValueError:
            cat_id = None
    difficulty = request.args.get("difficulty")
    state = request.args.get("state")
    
    # Load all challenges according to search/filter parameters
    ch_list = ChallengeService.list_challenges(
        search=search,
        category_id=cat_id,
        difficulty=difficulty,
        state=state
    )
    categories_list = CategoryService.get_all_categories()
    return render_template("admin_challenges.html", challenges=ch_list, categories=categories_list)

@admin_bp.route("/admin/challenges/new", methods=["GET", "POST"])
@require_admin
def challenge_new():
    error = None
    categories_list = CategoryService.get_all_categories()
    
    if request.method == "POST":
        legacy_id = request.form.get("legacy_id")
        title = request.form.get("title")
        description = request.form.get("description")
        try:
            points = int(request.form.get("points", 50))
        except ValueError:
            points = 50
        difficulty = request.form.get("difficulty", "Easy")
        
        cat_id_raw = request.form.get("category_id")
        cat_id = int(cat_id_raw) if cat_id_raw else None
        
        state = request.form.get("state", "visible")
        try:
            order = int(request.form.get("display_order", 0))
        except ValueError:
            order = 0
            
        visible = request.form.get("visible") == "on"
        connection_info = request.form.get("connection_info")
        requires_connection_info = request.form.get("requires_connection_info") == "on"
        
        flag_content = request.form.get("flag_content")

        if not legacy_id or not title or not flag_content:
            error = "Please fill in all required fields."
        elif ChallengeService.get_challenge_by_any_id(legacy_id):
            error = f"A challenge with legacy ID '{legacy_id}' already exists."
        else:
            # Create challenge
            ch = ChallengeService.create_challenge(
                legacy_id=legacy_id,
                title=title,
                description=description,
                points=points,
                difficulty=difficulty,
                category_id=cat_id,
                state=state,
                display_order=order,
                visible=visible,
                connection_info=connection_info,
                requires_connection_info=requires_connection_info
            )
            # Create initial flag
            FlagService.create_flag(ch.id, flag_content)
            return redirect(url_for("admin.challenges"))

    return render_template("admin_challenge_edit.html", ch=None, categories=categories_list, error=error)

@admin_bp.route("/admin/challenges/<int:ch_id>/edit", methods=["GET", "POST"])
@require_admin
def challenge_edit(ch_id):
    ch = ChallengeService.get_challenge_by_any_id(ch_id)
    if not ch:
        return redirect(url_for("admin.challenges"))
        
    error = None
    message = None
    categories_list = CategoryService.get_all_categories()
    
    if request.method == "POST":
        form_type = request.form.get("form_type")
        
        if form_type == "metadata":
            title = request.form.get("title")
            description = request.form.get("description")
            difficulty = request.form.get("difficulty")
            cat_id_raw = request.form.get("category_id")
            cat_id = int(cat_id_raw) if cat_id_raw else None
            state = request.form.get("state")
            try:
                order = int(request.form.get("display_order", 0))
            except ValueError:
                order = 0
            visible = request.form.get("visible") == "on"
            connection_info = request.form.get("connection_info")
            requires_connection_info = request.form.get("requires_connection_info") == "on"
            
            ChallengeService.update_challenge(ch.id,
                title=title,
                description=description,
                difficulty=difficulty,
                category_id=cat_id,
                state=state,
                display_order=order,
                visible=visible,
                connection_info=connection_info,
                requires_connection_info=requires_connection_info
            )
            message = "Metadata details updated."
            
        elif form_type == "scoring":
            decay_type = request.form.get("decay_type")
            try:
                initial_points = int(request.form.get("initial_points", 50))
                minimum_points = int(request.form.get("minimum_points", 10))
                decay_rate = int(request.form.get("decay_rate", 0))
                max_attempts = int(request.form.get("max_attempts", 0))
            except ValueError:
                initial_points, minimum_points, decay_rate, max_attempts = 50, 10, 0, 0
                
            ChallengeService.update_challenge(ch.id,
                decay_type=decay_type,
                initial_points=initial_points,
                minimum_points=minimum_points,
                decay_rate=decay_rate,
                max_attempts=max_attempts
            )
            message = "Scoring config rules updated."
            
        elif form_type == "add_flag":
            content = request.form.get("content")
            flag_type = request.form.get("flag_type", "exact")
            try:
                priority = int(request.form.get("priority", 0))
            except ValueError:
                priority = 0
            is_case_sensitive = request.form.get("is_case_sensitive") == "on"
            
            _, err = FlagService.create_flag(ch.id, content, flag_type, is_case_sensitive, priority)
            if err:
                error = err
            else:
                message = "Flag added successfully."
                
        elif form_type == "add_hint":
            title = request.form.get("title")
            content = request.form.get("content")
            try:
                cost = int(request.form.get("cost", 0))
                order = int(request.form.get("display_order", 0))
            except ValueError:
                cost, order = 0, 0
                
            _, err = HintService.create_hint(ch.id, content, cost, title, display_order=order)
            if err:
                error = err
            else:
                message = "Hint added successfully."
                
        elif form_type == "upload_file":
            uploaded_file = request.files.get("file")
            upload_folder = os.path.join(current_app.root_path, "..", "instance", "uploads")
            _, err = FileService.upload_file(ch.id, uploaded_file, upload_folder)
            if err:
                error = err
            else:
                message = "File attachment uploaded successfully."

        # Reload challenge representation
        ch = ChallengeService.get_challenge_by_any_id(ch_id)

    return render_template("admin_challenge_edit.html", ch=ch, categories=categories_list, error=error, message=message)

@admin_bp.route("/admin/challenges/<int:ch_id>/delete")
@require_admin
def delete_challenge(ch_id):
    ChallengeService.delete_challenge(ch_id)
    return redirect(url_for("admin.challenges"))

@admin_bp.route("/admin/challenges/<int:ch_id>/clone")
@require_admin
def clone_challenge(ch_id):
    ch = ChallengeService.get_challenge_by_any_id(ch_id)
    if not ch:
        return redirect(url_for("admin.challenges"))
        
    unique_suffix = f"_clone_{os.urandom(2).hex()}"
    new_legacy_id = ch.legacy_id + unique_suffix
    
    # Create clone
    clone = ChallengeService.create_challenge(
        legacy_id=new_legacy_id,
        title=f"{ch.title} (Clone)",
        description=ch.description,
        points=ch.initial_points,
        difficulty=ch.difficulty,
        category_id=ch.category_id,
        initial_points=ch.initial_points,
        minimum_points=ch.minimum_points,
        decay_type=ch.decay_type,
        decay_rate=ch.decay_rate,
        max_attempts=ch.max_attempts,
        visible=False, # default clones hidden initially
        state="hidden"
    )
    
    # Duplicate flags
    for f in ch.flags:
        FlagService.create_flag(clone.id, f.content, f.flag_type, f.is_case_sensitive, f.priority, f.notes)
        
    # Duplicate hints
    for h in ch.hints:
        HintService.create_hint(clone.id, h.content, h.cost, h.title, h.visible, h.enabled, h.display_order)
        
    return redirect(url_for("admin.challenges"))

# ── Inline sub-items deletion route mappings ────────────────
@admin_bp.route("/admin/flags/<int:flag_id>/delete")
@require_admin
def delete_flag(flag_id):
    flag = FlagService.get_flag_by_id(flag_id)
    if flag:
        ch_id = flag.challenge_id
        FlagService.delete_flag(flag_id)
        return redirect(url_for("admin.challenge_edit", ch_id=ch_id))
    return redirect(url_for("admin.challenges"))

@admin_bp.route("/admin/hints/<int:hint_id>/delete")
@require_admin
def delete_hint(hint_id):
    hint = HintService.get_hint_by_id(hint_id)
    if hint:
        ch_id = hint.challenge_id
        HintService.delete_hint(hint_id)
        return redirect(url_for("admin.challenge_edit", ch_id=ch_id))
    return redirect(url_for("admin.challenges"))

@admin_bp.route("/admin/files/<int:file_id>/delete")
@require_admin
def delete_file(file_id):
    file_record = FileService.get_file_by_id(file_id)
    if file_record:
        ch_id = file_record.challenge_id
        upload_folder = os.path.join(current_app.root_path, "..", "instance", "uploads")
        FileService.delete_file(file_id, upload_folder)
        return redirect(url_for("admin.challenge_edit", ch_id=ch_id))
    return redirect(url_for("admin.challenges"))

# ═══════════════════════════════════════════════════════════════
# MILESTONE 5 – COMPETITION MANAGEMENT
# ═══════════════════════════════════════════════════════════════
from app.services.competition_service import CompetitionService
from app.services.announcement_service import AnnouncementService
from app.services.submission_service import SubmissionService
from app.services.live_scoreboard_service import LiveScoreboardService
from app.repositories.announcement_repository import AnnouncementRepository

# ── Competition ──────────────────────────────────────────────
@admin_bp.route("/admin/competition", methods=["GET"])
@require_admin
def competition():
    comp = CompetitionService.get_active_competition()
    state = CompetitionService.get_competition_state(comp)
    return render_template("admin_competition.html", comp=comp, state=state)

@admin_bp.route("/admin/competition/update", methods=["POST"])
@require_admin
def competition_update():
    comp = CompetitionService.get_active_competition()
    import datetime as dt

    def parse_dt(val):
        if not val:
            return None
        for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"):
            try:
                return dt.datetime.strptime(val, fmt)
            except ValueError:
                continue
        return None

    updates = {
        "name": request.form.get("name"),
        "description": request.form.get("description"),
        "start_time": parse_dt(request.form.get("start_time")),
        "end_time": parse_dt(request.form.get("end_time")),
        "registration_open": parse_dt(request.form.get("registration_open")),
        "registration_close": parse_dt(request.form.get("registration_close")),
        "freeze_time": parse_dt(request.form.get("freeze_time")),
        "unfreeze_time": parse_dt(request.form.get("unfreeze_time")),
        "allow_practice": request.form.get("allow_practice") == "on",
        "is_active": request.form.get("is_active") == "on",
    }
    # Remove None to avoid overwriting existing fields with None
    updates = {k: v for k, v in updates.items() if v is not None or k in ("freeze_time", "unfreeze_time")}

    CompetitionService.update_competition(comp.id, **updates)
    flash("Competition settings updated.", "success")
    return redirect(url_for("admin.competition"))

@admin_bp.route("/admin/competition/freeze", methods=["POST"])
@require_admin
def competition_freeze():
    import datetime as dt
    comp = CompetitionService.get_active_competition()
    now = dt.datetime.utcnow()
    # Set freeze to now, unfreeze to end_time (or +1 hour)
    unfreeze = comp.end_time or now + dt.timedelta(hours=1)
    CompetitionService.update_competition(comp.id, freeze_time=now, unfreeze_time=unfreeze)
    flash("Scoreboard frozen.", "success")
    return redirect(url_for("admin.competition"))

@admin_bp.route("/admin/competition/unfreeze", methods=["POST"])
@require_admin
def competition_unfreeze():
    import datetime as dt
    comp = CompetitionService.get_active_competition()
    # Clear freeze window by setting both to None
    CompetitionService.update_competition(comp.id, freeze_time=None, unfreeze_time=None)
    flash("Scoreboard unfrozen.", "success")
    return redirect(url_for("admin.competition"))

@admin_bp.route("/admin/competition/end", methods=["POST"])
@require_admin
def competition_end():
    import datetime as dt
    comp = CompetitionService.get_active_competition()
    CompetitionService.update_competition(comp.id, end_time=dt.datetime.utcnow())
    flash("Competition ended.", "warning")
    return redirect(url_for("admin.competition"))

@admin_bp.route("/admin/competition/stats")
@require_admin
def competition_stats():
    live = LiveScoreboardService.get_live_rankings(is_admin_preview=True)
    comp = CompetitionService.get_active_competition()
    state = CompetitionService.get_competition_state(comp)
    return render_template("admin_competition_stats.html",
                           leaderboard=live["leaderboard"],
                           freeze_active=live["freeze_active"],
                           timer=live["timer"],
                           comp=comp,
                           state=state)

# ── Announcements ────────────────────────────────────────────
@admin_bp.route("/admin/announcements", methods=["GET", "POST"])
@require_admin
def announcements():
    error = None
    message = None
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        pinned = request.form.get("pinned") == "on"
        visible = request.form.get("visible", "on") == "on"
        ann, err = AnnouncementService.create_announcement(
            title=title, content=content, pinned=pinned, visible=visible
        )
        if err:
            error = err
        else:
            message = "Announcement created."

    all_anns = AnnouncementRepository.get_all(include_unpublished=True)
    return render_template("admin_announcements.html",
                           announcements=all_anns, error=error, message=message)

@admin_bp.route("/admin/announcements/<int:ann_id>/delete")
@require_admin
def delete_announcement(ann_id):
    AnnouncementService.delete_announcement(ann_id)
    return redirect(url_for("admin.announcements"))

@admin_bp.route("/admin/announcements/<int:ann_id>/toggle_pin")
@require_admin
def toggle_announcement_pin(ann_id):
    from app.repositories.announcement_repository import AnnouncementRepository
    ann = AnnouncementRepository.get_by_id(ann_id)
    if ann:
        AnnouncementRepository.update(ann_id, pinned=not ann.pinned)
    return redirect(url_for("admin.announcements"))

@admin_bp.route("/admin/announcements/<int:ann_id>/toggle_visibility")
@require_admin
def toggle_announcement_visibility(ann_id):
    from app.repositories.announcement_repository import AnnouncementRepository
    ann = AnnouncementRepository.get_by_id(ann_id)
    if ann:
        AnnouncementRepository.update(ann_id, published=not ann.published)
    return redirect(url_for("admin.announcements"))

# ── Submissions Manager ──────────────────────────────────────
@admin_bp.route("/admin/submissions")
@require_admin
def submissions():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    user_id = request.args.get("user_id", None, type=int)
    challenge_id = request.args.get("challenge_id", None, type=int)
    status = request.args.get("status")
    correct_str = request.args.get("correct")
    correct = None
    if correct_str == "true":
        correct = True
    elif correct_str == "false":
        correct = False

    result = SubmissionService.get_submissions(
        page=page, per_page=per_page,
        user_id=user_id, challenge_id=challenge_id,
        status=status, correct=correct
    )
    from app.repositories.user_repository import UserRepository
    from app.repositories.challenge_repository import ChallengeRepository
    all_users = UserRepository.get_all_participants()
    all_challenges = ChallengeRepository.get_all(include_hidden=True)
    return render_template("admin_submissions.html",
                           result=result,
                           all_users=all_users,
                           all_challenges=all_challenges)

@admin_bp.route("/admin/submissions/<int:sub_id>/delete")
@require_admin
def delete_submission(sub_id):
    SubmissionService.delete(sub_id)
    flash("Submission deleted.", "info")
    return redirect(url_for("admin.submissions"))

@admin_bp.route("/admin/submissions/<int:sub_id>/rejudge")
@require_admin
def rejudge_submission(sub_id):
    ok, msg = SubmissionService.rejudge(sub_id)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("admin.submissions"))

@admin_bp.route("/admin/submissions/<int:sub_id>/mark_correct")
@require_admin
def mark_submission_correct(sub_id):
    ok, msg = SubmissionService.mark_correct(sub_id)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("admin.submissions"))

@admin_bp.route("/admin/submissions/<int:sub_id>/mark_incorrect")
@require_admin
def mark_submission_incorrect(sub_id):
    ok, msg = SubmissionService.mark_incorrect(sub_id)
    flash(msg, "warning" if ok else "danger")
    return redirect(url_for("admin.submissions"))

@admin_bp.route("/admin/submissions/export")
@require_admin
def export_submissions():
    from flask import Response
    csv_data = SubmissionService.export_csv()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=submissions.csv"}
    )


# ============================================================
# Milestone 8 — Admin: Docker Infrastructure Management
# ============================================================

from app.repositories.docker_image_repository import DockerImageRepository
from app.repositories.deployment_profile_repository import DeploymentProfileRepository
from app.repositories.challenge_instance_repository import ChallengeInstanceRepository
from app.services.instance_service import InstanceService
from app.services.docker_service import DockerService


# ---- Docker Images -------------------------------------------------

@admin_bp.route("/admin/docker/images", methods=["GET"])
@require_admin
def admin_docker_images():
    images = DockerImageRepository.get_all()
    return jsonify([
        {"id": img.id, "name": img.name, "tag": img.tag, "registry": img.registry,
         "full_ref": img.full_ref, "description": img.description,
         "default_port": img.default_port, "size_bytes": img.size_bytes,
         "created_at": img.created_at.isoformat()}
        for img in images
    ])


@admin_bp.route("/admin/docker/images", methods=["POST"])
@require_admin
def admin_docker_images_create():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"ok": False, "message": "name is required."}), 400
    img = DockerImageRepository.create(
        name=name, tag=data.get("tag", "latest"),
        registry=data.get("registry"), description=data.get("description"),
        size_bytes=data.get("size_bytes"),
    )
    return jsonify({"ok": True, "id": img.id, "full_ref": img.full_ref}), 201


@admin_bp.route("/admin/docker/images/<int:image_id>", methods=["GET"])
@require_admin
def admin_docker_image_get(image_id):
    img = DockerImageRepository.get_by_id(image_id)
    if not img:
        return jsonify({"ok": False, "message": "Not found."}), 404
    return jsonify({
        "id": img.id, "name": img.name, "tag": img.tag, "registry": img.registry,
        "full_ref": img.full_ref, "description": img.description,
        "default_port": img.default_port, "size_bytes": img.size_bytes,
        "dockerfile_path": img.dockerfile_path, "compose_path": img.compose_path,
        "created_at": img.created_at.isoformat(),
    })


@admin_bp.route("/admin/docker/images/<int:image_id>", methods=["PUT", "PATCH"])
@require_admin
def admin_docker_image_update(image_id):
    data = request.get_json(silent=True) or {}
    allowed = {"name", "tag", "registry", "description", "default_port",
               "size_bytes", "dockerfile_path", "compose_path"}
    updates = {k: v for k, v in data.items() if k in allowed}
    img = DockerImageRepository.update(image_id, **updates)
    if not img:
        return jsonify({"ok": False, "message": "Not found."}), 404
    return jsonify({"ok": True, "full_ref": img.full_ref})


@admin_bp.route("/admin/docker/images/<int:image_id>", methods=["DELETE"])
@require_admin
def admin_docker_image_delete(image_id):
    img = DockerImageRepository.delete(image_id)
    if not img:
        return jsonify({"ok": False, "message": "Not found."}), 404
    return jsonify({"ok": True, "message": "Image deleted."})


@admin_bp.route("/admin/docker/images/<int:image_id>/pull", methods=["POST"])
@require_admin
def admin_docker_image_pull(image_id):
    img = DockerImageRepository.get_by_id(image_id)
    if not img:
        return jsonify({"ok": False, "message": "Not found."}), 404
    ok, message = DockerService.pull_image(img.full_ref)
    return jsonify({"ok": ok, "message": message})


# ---- Deployment Profiles -------------------------------------------

@admin_bp.route("/admin/docker/profiles", methods=["GET"])
@require_admin
def admin_deployment_profiles():
    profiles = DeploymentProfileRepository.get_all()
    return jsonify([
        {"id": p.id, "name": p.name, "description": p.description,
         "cpu_limit": p.cpu_limit, "memory_limit": p.memory_limit,
         "pids_limit": p.pids_limit, "network_disabled": p.network_disabled,
         "ttl_minutes": p.ttl_minutes, "max_instances_per_user": p.max_instances_per_user,
         "port_range_start": p.port_range_start, "port_range_end": p.port_range_end}
        for p in profiles
    ])


@admin_bp.route("/admin/docker/profiles", methods=["POST"])
@require_admin
def admin_deployment_profiles_create():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"ok": False, "message": "name is required."}), 400
    allowed = {"name", "description", "cpu_limit", "memory_limit", "pids_limit",
               "network_disabled", "ttl_minutes", "max_instances_per_user",
               "port_range_start", "port_range_end"}
    kwargs = {k: v for k, v in data.items() if k in allowed}
    profile = DeploymentProfileRepository.create(**kwargs)
    return jsonify({"ok": True, "id": profile.id, "name": profile.name}), 201


@admin_bp.route("/admin/docker/profiles/<int:profile_id>", methods=["PUT", "PATCH"])
@require_admin
def admin_deployment_profile_update(profile_id):
    data = request.get_json(silent=True) or {}
    allowed = {"name", "description", "cpu_limit", "memory_limit", "pids_limit",
               "network_disabled", "ttl_minutes", "max_instances_per_user",
               "port_range_start", "port_range_end"}
    updates = {k: v for k, v in data.items() if k in allowed}
    profile = DeploymentProfileRepository.update(profile_id, **updates)
    if not profile:
        return jsonify({"ok": False, "message": "Not found."}), 404
    return jsonify({"ok": True, "name": profile.name})


@admin_bp.route("/admin/docker/profiles/<int:profile_id>", methods=["DELETE"])
@require_admin
def admin_deployment_profile_delete(profile_id):
    profile = DeploymentProfileRepository.delete(profile_id)
    if not profile:
        return jsonify({"ok": False, "message": "Not found."}), 404
    return jsonify({"ok": True, "message": "Profile deleted."})



# ============================================================
# Milestone 9 — Admin System Observability Endpoints
# ============================================================

@admin_bp.route("/admin/system/health", methods=["GET"])
@require_admin
def admin_system_health():
    """Return a full system health snapshot for admin dashboard."""
    from app.services.docker_service import _probe_docker
    from app.models.challenge_instance import ChallengeInstance
    from app.models.submission import Submission
    from app.models.user import User
    from app.models.competition import Competition
    from datetime import datetime
    from app.extensions import db
    import os

    # DB check
    db_ok = True
    db_err = None
    db_size_bytes = 0
    try:
        db.session.execute(db.select(1)).first()
        db_uri = current_app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if db_uri.startswith("sqlite:///"):
            db_file = db_uri.replace("sqlite:///", "")
            if not os.path.isabs(db_file):
                db_file = os.path.abspath(os.path.join(current_app.root_path, "..", db_file))
            if os.path.exists(db_file):
                db_size_bytes = os.path.getsize(db_file)
    except Exception as e:
        db_ok = False
        db_err = str(e)

    # Docker check
    docker_mode = DockerService.mode()
    docker_ok = docker_mode == "simulated" or _probe_docker()
    active_containers = ChallengeInstance.query.filter(
        ChallengeInstance.status.in_(["creating", "running"])
    ).count()

    # Competition check
    active_comp = Competition.query.filter(Competition.is_active == True).first()
    comp_state = None
    if active_comp:
        from app.services.competition_service import CompetitionService
        comp_state = CompetitionService.get_competition_state(active_comp)

    # Submissions & Users
    total_subs = Submission.query.count()
    correct_subs = Submission.query.filter_by(correct=True).count()
    total_users = User.query.filter_by(is_deleted=False).count()

    # Uploads
    uploads_dir = os.path.abspath(os.path.join(current_app.root_path, "..", "uploads"))
    uploads_ok = os.path.exists(uploads_dir) and os.access(uploads_dir, os.W_OK)
    uploads_size = 0
    if os.path.exists(uploads_dir):
        for dp, _, files_list in os.walk(uploads_dir):
            for f in files_list:
                try:
                    uploads_size += os.path.getsize(os.path.join(dp, f))
                except Exception:
                    pass

    return jsonify({
        "database": {"ok": db_ok, "error": db_err, "size_bytes": db_size_bytes},
        "docker": {"ok": docker_ok, "mode": docker_mode, "active_containers": active_containers},
        "uploads": {"ok": uploads_ok, "size_bytes": uploads_size},
        "competition": {
            "active": active_comp is not None,
            "name": active_comp.name if active_comp else None,
            "state": comp_state
        },
        "submissions": {"total": total_subs, "correct": correct_subs},
        "users": {"total": total_users}
    }), 200


@admin_bp.route("/admin/system/metrics", methods=["GET"])
@require_admin
def admin_system_metrics():
    """Return current in-memory HTTP request metrics."""
    from app.services.metrics_service import _request_counts, _response_status_counts, _api_requests
    return jsonify({
        "request_counts": _request_counts,
        "response_status_counts": _response_status_counts,
        "api_requests": _api_requests
    }), 200


# --- Plugin Marketplace Admin Endpoints ---

@admin_bp.route("/admin/plugins", methods=["GET"])
@require_admin
def admin_plugins():
    from app.services.plugin_service import PluginService
    plugins = PluginService.discover_plugins()
    return render_template("admin_plugins.html", plugins=plugins)


@admin_bp.route("/admin/plugins/upload", methods=["POST"])
@require_admin
def admin_plugins_upload():
    from flask import flash
    from app.services.plugin_service import PluginService
    from werkzeug.utils import secure_filename

    if 'zip_file' not in request.files:
        flash("No file part uploaded", "error")
        return redirect(url_for("admin.admin_plugins"))

    file = request.files['zip_file']
    if file.filename == '':
        flash("No file selected", "error")
        return redirect(url_for("admin.admin_plugins"))

    if file and file.filename.endswith(".zip"):
        plugins_dir = PluginService.get_plugins_dir()
        temp_zip = os.path.join(plugins_dir, secure_filename(file.filename))
        try:
            file.save(temp_zip)
            manifest = PluginService.install_plugin_zip(temp_zip)
            flash(f"Plugin '{manifest.get('name')}' successfully uploaded and installed!", "success")
        except Exception as e:
            flash(f"Installation failed: {str(e)}", "error")
        finally:
            if os.path.exists(temp_zip):
                os.remove(temp_zip)
    else:
        flash("Only ZIP files are supported", "error")

    return redirect(url_for("admin.admin_plugins"))


@admin_bp.route("/admin/plugins/<plugin_name>/enable", methods=["POST"])
@require_admin
def admin_plugins_enable(plugin_name):
    from flask import flash
    from app.services.plugin_service import PluginService
    ok = PluginService.enable_plugin(plugin_name)
    if ok:
        flash(f"Plugin '{plugin_name}' has been enabled.", "success")
    else:
        flash(f"Failed enabling plugin '{plugin_name}'. Check logs for safety warnings.", "error")
    return redirect(url_for("admin.admin_plugins"))


@admin_bp.route("/admin/plugins/<plugin_name>/disable", methods=["POST"])
@require_admin
def admin_plugins_disable(plugin_name):
    from flask import flash
    from app.services.plugin_service import PluginService
    ok = PluginService.disable_plugin(plugin_name)
    if ok:
        flash(f"Plugin '{plugin_name}' has been disabled.", "success")
    else:
        flash(f"Failed disabling plugin '{plugin_name}'.", "error")
    return redirect(url_for("admin.admin_plugins"))


@admin_bp.route("/admin/plugins/<plugin_name>/uninstall", methods=["POST"])
@require_admin
def admin_plugins_uninstall(plugin_name):
    from flask import flash
    from app.services.plugin_service import PluginService
    PluginService.uninstall_plugin(plugin_name)
    flash(f"Plugin '{plugin_name}' uninstalled completely.", "success")
    return redirect(url_for("admin.admin_plugins"))


@admin_bp.route("/admin/plugins/<plugin_name>", methods=["GET"])
@require_admin
def admin_plugin_detail(plugin_name):
    from app.services.plugin_service import PluginService
    from app.services.plugin_security import PluginSecurity
    from app.models.plugin_installation import PluginInstallation
    
    plugins = PluginService.discover_plugins()
    plugin = next((p for p in plugins if p["name"] == plugin_name), None)
    if not plugin:
        return redirect(url_for("admin.admin_plugins"))

    plugins_dir = PluginService.get_plugins_dir()
    plugin_folder = os.path.join(plugins_dir, plugin["folder_name"])
    security_status, reasons = PluginSecurity.scan_plugin(plugin_folder)
    
    db_inst = PluginInstallation.query.filter_by(plugin_name=plugin_name).first()
    
    return render_template(
        "admin_plugin_detail.html",
        plugin=plugin,
        security_status=security_status,
        security_reasons=reasons,
        db_inst=db_inst
    )


# =============================================================================
# PHASE 14 — AI ADMIN DASHBOARD
# =============================================================================

@admin_bp.route("/admin/ai", methods=["GET"])
@require_admin
def ai_dashboard():
    """AI control panel: provider config, stats overview."""
    from app.models.setting import Setting
    from app.services.ai_service import AIService
    from app.services.writeup_service import WriteupService

    ai_provider = (Setting.query.filter_by(key="AI_PROVIDER").first() or type('', (), {'value': 'stub'})()).value
    ai_model = (Setting.query.filter_by(key="AI_MODEL").first() or type('', (), {'value': 'stub-v1'})()).value
    max_tokens = (Setting.query.filter_by(key="MAX_AI_TOKENS").first() or type('', (), {'value': '512'})()).value
    ai_hint_cost = (Setting.query.filter_by(key="AI_HINT_COST").first() or type('', (), {'value': '0'})()).value
    ai_max_hints = (Setting.query.filter_by(key="AI_MAX_HINTS").first() or type('', (), {'value': '3'})()).value

    token_stats = AIService.get_token_usage_stats()
    draft_writeups = WriteupService.list_all(status='draft')
    approved_writeups = WriteupService.list_all(status='approved')

    return render_template(
        "admin_ai.html",
        ai_provider=ai_provider,
        ai_model=ai_model,
        max_tokens=max_tokens,
        ai_hint_cost=ai_hint_cost,
        ai_max_hints=ai_max_hints,
        token_stats=token_stats,
        draft_writeups=draft_writeups,
        approved_writeups=approved_writeups,
    )


@admin_bp.route("/admin/ai/config", methods=["POST"])
@require_admin
def ai_config_save():
    """Save AI provider configuration to settings."""
    from app.models.setting import Setting
    from app.extensions import db

    fields = {
        'AI_PROVIDER': request.form.get('ai_provider', 'stub'),
        'AI_MODEL': request.form.get('ai_model', 'stub-v1'),
        'MAX_AI_TOKENS': request.form.get('max_tokens', '512'),
        'AI_HINT_COST': request.form.get('ai_hint_cost', '0'),
        'AI_MAX_HINTS': request.form.get('ai_max_hints', '3'),
        'OLLAMA_URL': request.form.get('ollama_url', 'http://localhost:11434'),
        'OPENAI_API_KEY': request.form.get('openai_api_key', ''),
        'ANTHROPIC_API_KEY': request.form.get('anthropic_api_key', ''),
        'GEMINI_API_KEY': request.form.get('gemini_api_key', ''),
    }

    for key, value in fields.items():
        rec = Setting.query.filter_by(key=key).first()
        if rec:
            rec.value = value
        else:
            db.session.add(Setting(key=key, value=value))
    db.session.commit()

    flash("AI configuration saved.", "success")
    return redirect(url_for("admin.ai_dashboard"))


@admin_bp.route("/admin/ai/stats", methods=["GET"])
@require_admin
def ai_stats():
    """Token usage statistics page."""
    from app.services.ai_service import AIService
    from app.models.ai_hint_request import AIHintRequest
    from app.models.ai_difficulty_prediction import AIDifficultyPrediction

    token_stats = AIService.get_token_usage_stats()
    recent_hints = AIHintRequest.query.order_by(AIHintRequest.id.desc()).limit(20).all()
    recent_predictions = AIDifficultyPrediction.query.order_by(AIDifficultyPrediction.id.desc()).limit(10).all()

    return render_template(
        "admin_ai_stats.html",
        token_stats=token_stats,
        recent_hints=recent_hints,
        recent_predictions=recent_predictions,
    )


@admin_bp.route("/admin/ai/predict/<int:challenge_id>", methods=["POST"])
@require_admin
def ai_predict_difficulty(challenge_id):
    """Run AI difficulty prediction for a specific challenge."""
    from app.models.challenge import Challenge
    from app.services.difficulty_service import DifficultyService

    challenge = Challenge.query.get_or_404(challenge_id)
    result = DifficultyService.predict(challenge)

    if result.get('error'):
        flash(f"Prediction failed: {result['error']}", "danger")
    else:
        flash(
            f"Predicted: {result['predicted_difficulty']} "
            f"(confidence {result['confidence']:.0%})",
            "success"
        )
    return redirect(url_for("admin.ai_dashboard"))


@admin_bp.route("/admin/ai/writeup/<int:writeup_id>/approve", methods=["POST"])
@require_admin
def ai_writeup_approve(writeup_id):
    """Admin approves a draft AI writeup."""
    from app.services.writeup_service import WriteupService
    result = WriteupService.approve(writeup_id)
    if result.get('error'):
        flash(result['error'], "danger")
    else:
        flash("Writeup approved.", "success")
    return redirect(url_for("admin.ai_dashboard"))


@admin_bp.route("/admin/ai/writeup/<int:writeup_id>/publish", methods=["POST"])
@require_admin
def ai_writeup_publish(writeup_id):
    """Admin publishes an approved AI writeup."""
    from app.services.writeup_service import WriteupService
    result = WriteupService.publish(writeup_id)
    if result.get('error'):
        flash(result['error'], "danger")
    else:
        flash("Writeup published successfully.", "success")
    return redirect(url_for("admin.ai_dashboard"))


# =============================================================================
# PHASE 15 — SAAS ADMIN DASHBOARD
# =============================================================================

@admin_bp.route("/admin/organization", methods=["GET"])
@require_admin
def admin_organization():
    """Organization overview page."""
    from app.models.organization import Organization
    from app.services.quota_service import QuotaService
    from app.services.organization_service import OrganizationService

    all_orgs = []
    members = []
    quotas = {}

    if g.current_org:
        members = OrganizationService.get_members(g.current_org)
        # Compute quotas usage
        for res in ('users', 'competitions', 'challenges', 'containers', 'ai_tokens', 'storage_mb'):
            allowed, limit, used = QuotaService.check(g.current_org, res)
            quotas[res] = {
                'limit': limit,
                'used': used,
                'percent': min(100, int((used / limit) * 100)) if limit > 0 else (0 if limit == 0 else -1)
            }
    else:
        # Default view: list all organizations
        all_orgs = Organization.query.filter_by(is_deleted=False).all()

    return render_template(
        "admin_organization.html",
        all_orgs=all_orgs,
        members=members,
        quotas=quotas,
    )


@admin_bp.route("/admin/organization/billing", methods=["GET"])
@require_admin
def admin_organization_billing():
    """Billing overview page."""
    from app.services.billing_service import BillingService

    if not g.current_org:
        flash("Please access this page via a tenant subdomain (e.g. acme.ctfarena.local).", "warning")
        return redirect(url_for("admin.admin_organization"))

    billing = BillingService.get_billing(g.current_org)
    return render_template(
        "admin_organization_billing.html",
        billing=billing,
    )


@admin_bp.route("/admin/organization/plan", methods=["POST"])
@require_admin
def admin_organization_plan():
    """Change organization plan type."""
    from app.services.billing_service import BillingService

    if not g.current_org:
        flash("No resolved organization.", "danger")
        return redirect(url_for("admin.admin_organization"))

    plan = request.form.get("plan_type")
    success, msg = BillingService.upgrade(g.current_org, plan, actor_id=current_user.id)
    if success:
        flash(f"Plan switched to {plan.capitalize()} successfully.", "success")
    else:
        flash(msg, "danger")

    return redirect(url_for("admin.admin_organization_billing"))


# =============================================================================
# PHASE 16 — AI CYBER RANGE ROUTES
# =============================================================================

@admin_bp.route("/admin/cyberrange", methods=["GET"])
@require_admin
def admin_cyberrange():
    """Cyber Range main control panel."""
    from app.models.attack_simulation import AttackSimulation
    from app.models.attack_event import AttackEvent
    from app.models.incident import Incident

    # Fetch simulations (scoped by tenant if resolved)
    org_id = g.current_org.id if g.current_org else None
    query = AttackSimulation.query
    if org_id:
        query = query.filter_by(organization_id=org_id)
    
    simulations = query.order_by(AttackSimulation.created_at.desc()).all()
    
    # Calculate some summary stats
    running_sims = [s for s in simulations if s.status == 'running']
    total_attacks = AttackEvent.query.count()
    total_incidents = Incident.query.count()

    return render_template(
        "admin_cyberrange.html",
        simulations=simulations,
        running_sims=running_sims,
        total_attacks=total_attacks,
        total_incidents=total_incidents
    )


@admin_bp.route("/admin/cyberrange/simulation/<int:sim_id>", methods=["GET"])
@require_admin
def admin_simulation_detail(sim_id):
    """View details of a specific cyber range session, including MITRE heatmap and scores."""
    from app.models.attack_simulation import AttackSimulation
    from app.services.mitre_service import MitreService

    sim = AttackSimulation.query.get(sim_id)
    if not sim:
        flash("Simulation not found.", "danger")
        return redirect(url_for("admin.admin_cyberrange"))

    MitreService.seed_techniques()
    kill_chain = MitreService.get_kill_chain(sim_id)

    return render_template(
        "admin_cyberrange_detail.html",
        sim=sim,
        kill_chain=kill_chain
    )


@admin_bp.route("/admin/cyberrange/incidents", methods=["GET"])
@require_admin
def admin_cyberrange_incidents():
    """Incident Response queue view."""
    from app.models.incident import Incident

    incidents = Incident.query.order_by(Incident.created_at.desc()).all()
    return render_template(
        "admin_incidents.html",
        incidents=incidents
    )


@admin_bp.route("/admin/cyberrange/timeline/<int:sim_id>", methods=["GET"])
@require_admin
def admin_cyberrange_timeline(sim_id):
    """Timeline event stream visualization for a simulation session."""
    from app.models.attack_simulation import AttackSimulation
    from app.services.timeline_service import TimelineService

    sim = AttackSimulation.query.get(sim_id)
    if not sim:
        flash("Simulation not found.", "danger")
        return redirect(url_for("admin.admin_cyberrange"))

    timeline = TimelineService.get_timeline(sim_id)
    return render_template(
        "admin_timeline.html",
        sim=sim,
        timeline=timeline
    )


# ─────────────────────────────────────────────────────────────────────────────
# Phase 18 — Enterprise SOC & Threat Intelligence Admin Routes
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route("/admin/soc", methods=["GET"])
@require_admin
def admin_soc():
    """SOC Operations Center dashboard."""
    from app.models.alert import Alert
    from app.models.case import Case
    from app.models.ioc import IOC
    from app.models.hunt import Hunt

    # Seed mock data if empty
    from app.services.siem_service import SIEMService
    from app.services.threat_intelligence_service import ThreatIntelligenceService
    from app.services.hunt_service import HuntService
    
    if not Alert.query.first():
        # Create some demo alerts
        SIEMService.generate_alert("Brute force attack on admin portal", "high", {"source_ip": "198.51.100.42", "event_type": "authentication"})
        SIEMService.generate_alert("SQL injection attempt in query string", "critical", {"source_ip": "203.0.113.15", "event_type": "web"})
        SIEMService.generate_alert("Anomalous high outbound data transfer", "medium", {"source_ip": "192.168.1.50", "event_type": "network"})
    if not IOC.query.first():
        ThreatIntelligenceService.create_ioc("ip", "198.51.100.42", "high", 90, "OSINT", tags="c2,bruteforce")
        ThreatIntelligenceService.create_ioc("domain", "evil-c2-malware.com", "critical", 95, "ISAC", tags="c2")
    if not db.session.query(Hunt).first():
        HuntService.create_hunt("C2 Server Indicator Hunt", "ioc", "Look for compromised outbound traffic patterns")

    alerts = Alert.query.all()
    alert_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
    for a in alerts:
        if a.severity in alert_counts:
            alert_counts[a.severity] += 1

    open_cases = Case.query.filter(Case.status.in_(['open', 'investigating', 'contained'])).count()
    active_iocs = IOC.query.filter_by(is_active=True).count()
    active_hunts = db.session.query(Hunt).filter(Hunt.status.in_(['planned', 'active'])).count()
    recent_alerts = Alert.query.order_by(Alert.created_at.desc()).limit(5).all()

    return render_template(
        "admin_soc.html",
        alert_counts=alert_counts,
        open_cases=open_cases,
        active_iocs=active_iocs,
        active_hunts=active_hunts,
        recent_alerts=recent_alerts
    )


@admin_bp.route("/admin/alerts", methods=["GET"])
@require_admin
def admin_alerts():
    """Alert Queue overview."""
    from app.models.alert import Alert
    alerts = Alert.query.order_by(Alert.created_at.desc()).all()
    
    summary = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
    for a in alerts:
        if a.severity in summary:
            summary[a.severity] += 1

    return render_template(
        "admin_alerts.html",
        alerts=alerts,
        severity_summary=summary
    )


@admin_bp.route("/admin/cases", methods=["GET"])
@require_admin
def admin_cases():
    """Incident Case Queue board."""
    from app.models.case import Case
    from app.models.alert import Alert
    from app.services.case_service import CaseService

    # Create dummy case if none
    if not Case.query.first():
        alert = Alert.query.first()
        CaseService.create_case(
            "Investigate Brute Force Attempt",
            "Continuous SSH authentication failure events detected from unknown external IP address.",
            "high",
            alert_id=alert.id if alert else None
        )

    cases = Case.query.order_by(Case.created_at.desc()).all()
    by_status = {'open': [], 'investigating': [], 'contained': [], 'resolved': [], 'closed': []}
    for c in cases:
        if c.status in by_status:
            by_status[c.status].append(c)

    return render_template(
        "admin_cases.html",
        cases_by_status=by_status
    )


@admin_bp.route("/admin/cases/<int:case_id>", methods=["GET"])
@require_admin
def admin_case_detail(case_id):
    """Detailed case investigation page."""
    from app.models.case import Case, CASE_TRANSITIONS
    from app.services.case_service import CaseService
    
    case = Case.query.get_or_404(case_id)
    allowed = CASE_TRANSITIONS.get(case.status, [])
    timeline = CaseService.get_timeline(case_id)

    return render_template(
        "admin_case_detail.html",
        case=case,
        allowed_transitions=allowed,
        timeline=timeline
    )


@admin_bp.route("/admin/hunts", methods=["GET"])
@require_admin
def admin_hunts():
    """Threat Hunting Console."""
    from app.models.hunt import Hunt
    hunts = db.session.query(Hunt).order_by(Hunt.created_at.desc()).all()
    return render_template("admin_hunts.html", hunts=hunts)


@admin_bp.route("/admin/threat-intel", methods=["GET"])
@require_admin
def admin_threat_intel():
    """Threat Intelligence & IOCs."""
    from app.models.ioc import IOC
    from app.models.threat_feed import ThreatFeed
    from app.services.threat_intelligence_service import ThreatIntelligenceService

    # Seed feeds if empty
    if not ThreatFeed.query.first():
        ThreatIntelligenceService.create_feed("AlienVault OTX", feed_type="open_source")
        ThreatIntelligenceService.create_feed("Abuse.ch URLHaus", feed_type="open_source")

    iocs = IOC.query.order_by(IOC.created_at.desc()).all()
    feeds = ThreatFeed.query.all()

    counts = {'ip': 0, 'domain': 0, 'url': 0, 'hash': 0, 'email': 0}
    blocked_count = 0
    for i in iocs:
        if i.type in counts:
            counts[i.type] += 1
        if i.is_blocked:
            blocked_count += 1

    return render_template(
        "admin_threat_intel.html",
        iocs=iocs,
        feeds=feeds,
        ioc_counts=counts,
        blocked_count=blocked_count
    )


# ─────────────────────────────────────────────────────────────────────────────
# Phase 19 — Security Research & CTI Platform Admin Routes
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route("/admin/research", methods=["GET"])
@require_admin
def admin_research():
    """Security Research & CTI dashboard."""
    from app.services.navigator_service import NavigatorService
    # Generate coverage matrix on the fly
    coverage = NavigatorService.compute_coverage()
    return render_template("admin_research.html", coverage=coverage)


@admin_bp.route("/admin/research/threat-actors", methods=["GET"])
@require_admin
def admin_threat_actors():
    """Threat Actors profile intelligence curation view."""
    return render_template("admin_threat_actors.html")


@admin_bp.route("/admin/research/campaigns", methods=["GET"])
@require_admin
def admin_campaigns():
    """Campaign timeline view."""
    return render_template("admin_campaigns.html")


@admin_bp.route("/admin/research/malware", methods=["GET"])
@require_admin
def admin_malware():
    """Malware static analysis workspace uploader."""
    return render_template("admin_malware.html")


@admin_bp.route("/admin/research/reports", methods=["GET"])
@require_admin
def admin_reports():
    """Research Reports creator and workspace."""
    return render_template("admin_reports.html")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 20 — Global Cybersecurity Ecosystem Admin Routes
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route("/admin/bounties", methods=["GET"])
@require_admin
def admin_bounties():
    """Bug Bounty program and submissions queue panel."""
    return render_template("admin_bounties.html")


@admin_bp.route("/admin/researchers", methods=["GET"])
@require_admin
def admin_researchers():
    """Researcher profiles catalog and rankings page."""
    return render_template("admin_researchers.html")


@admin_bp.route("/admin/marketplace", methods=["GET"])
@require_admin
def admin_marketplace():
    """Digital cybersecurity marketplace assets catalog."""
    return render_template("admin_marketplace.html")


@admin_bp.route("/admin/reputation", methods=["GET"])
@require_admin
def admin_reputation():
    """Cyber reputation and tiers consolidation workspace."""
    return render_template("admin_reputation.html")


@admin_bp.route("/admin/federation", methods=["GET"])
@require_admin
def admin_federation():
    """Tenant federation and trust bridges bridge panel."""
    return render_template("admin_federation.html")


# ─────────────────────────────────────────────────────────────────────────────
# Phase 21 — Autonomous Security Operations Platform Admin Routes
# ─────────────────────────────────────────────────────────────────────────────

@admin_bp.route("/admin/agents", methods=["GET"])
@require_admin
def admin_agents():
    """AI SOC analyst controls page."""
    return render_template("admin_agents.html")


@admin_bp.route("/admin/playbooks", methods=["GET"])
@require_admin
def admin_playbooks():
    """Automated SOAR playbooks orchestration console."""
    return render_template("admin_playbooks.html")


@admin_bp.route("/admin/predictions", methods=["GET"])
@require_admin
def admin_predictions():
    """Threat Prediction forecasting logs page."""
    return render_template("admin_predictions.html")


@admin_bp.route("/admin/knowledge", methods=["GET"])
@require_admin
def admin_knowledge():
    """Security Knowledge Graph visualization workspace."""
    return render_template("admin_knowledge.html")


@admin_bp.route("/admin/command-center", methods=["GET"])
@require_admin
def admin_command_center():
    """Unified Command Center Executive Dashboard."""
    return render_template("admin_command_center.html")


@admin_bp.route("/admin/compliance", methods=["GET"])
@require_admin
def admin_compliance():
    """GRC Compliance scoring status overview."""
    return render_template("admin_compliance.html")


@admin_bp.route("/admin/governance", methods=["GET"])
@require_admin
def admin_governance():
    """Corporate policies and Governance dashboard."""
    return render_template("admin_governance.html")


@admin_bp.route("/admin/exchange", methods=["GET"])
@require_admin
def admin_exchange():
    """Threat indicator feed exchange workspace."""
    return render_template("admin_exchange.html")


@admin_bp.route("/admin/audits", methods=["GET"])
@require_admin
def admin_audits():
    """Compliance Gaps Audits list panel."""
    return render_template("admin_audits.html")


@admin_bp.route("/admin/digital-twin", methods=["GET"])
@require_admin
def admin_digital_twin():
    """Security Digital Twin simulation platform."""
    return render_template("admin_digital_twin.html")








