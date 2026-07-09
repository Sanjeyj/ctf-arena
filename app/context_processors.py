from flask_login import current_user
from app.repositories.challenge_repository import ChallengeRepository
from app.repositories.submission_repository import SubmissionRepository


def _default_stats():
    """Return an empty stats dict that satisfies admin.html without any DB calls."""
    return {
        "total_participants": 0,
        "total_solves": 0,
        "most_popular_ch": "—",
        "max_possible": 0,
        "ch_solve_counts": {},
    }


def utility_processors():
    solved = {}
    challenges = {}
    username = None

    if current_user.is_authenticated:
        username = current_user.username

        # Load active visible challenges only
        challenges_list = ChallengeRepository.get_all(include_hidden=False)
        for ch in challenges_list:
            challenges[ch.legacy_id] = {
                "id": ch.legacy_id,
                "title": ch.title,
                "category": ch.category.name if ch.category else "General",
                "points": ch.current_points,
                "icon": ch.icon,
                "difficulty": ch.difficulty,
                "description": ch.description,
            }

        # Load user solves
        solved_list = SubmissionRepository.get_solved_by_user(username)
        for sub in solved_list:
            sch = next((c for c in challenges_list if c.id == sub.challenge_id), None)
            if sch:
                solved[sch.legacy_id] = {
                    "points": sub.points,
                    "time": sub.time.isoformat(),
                    "elapsed": sub.elapsed,
                }

    # ── Admin context ──────────────────────────────────────────────────────────
    # Inject stats/leaderboard/challenges so that templates extending admin.html
    # work correctly even when individual routes forget to pass these variables.
    stats = _default_stats()
    leaderboard = []

    from flask_login import current_user as _cu
    try:
        from app.services.permission_service import PermissionService
        if _cu.is_authenticated and PermissionService.has_permission(_cu, "manage_settings"):
            from app.services.admin_service import AdminService
            _lb, _stats, _challenges = AdminService.get_dashboard_stats()
            leaderboard = _lb
            stats = _stats
            # Merge admin challenge dict into the context challenges dict so
            # templates see the richer admin version (includes solve_count, etc.)
            challenges = _challenges
    except Exception:
        # Never crash a page render because of missing stats
        pass

    return {
        "platform_name": "CTF Arena",
        "competition_name": "Easy CTF Challenge",
        "logo_emoji": "🚩",
        "active_theme": "default",
        "current_user_name": username,
        "username": username,
        "solved": solved,
        "challenges": challenges,
        "platform_version": "v2",
        "notifications_count": 0,
        # Admin dashboard context — safe for all templates
        "stats": stats,
        "leaderboard": leaderboard,
    }
