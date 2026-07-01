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
from app.utils.decorators import require_admin

@admin_bp.route("/admin/login", methods=["GET", "POST"])
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
