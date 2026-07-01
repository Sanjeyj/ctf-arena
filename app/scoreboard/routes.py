from flask import render_template, request, jsonify
from flask_login import current_user
from app.scoreboard import scoreboard_bp
from app.services.scoreboard_service import ScoreboardService
from app.services.live_scoreboard_service import LiveScoreboardService
from app.services.announcement_service import AnnouncementService

@scoreboard_bp.route("/scoreboard")
def scoreboard():
    username = current_user.username if current_user.is_authenticated else None
    leaderboard, stats, solved, challenges = ScoreboardService.get_scoreboard_data(username)
    announcements = AnnouncementService.get_active_announcements()
    return render_template(
        "scoreboard.html",
        challenges=challenges,
        leaderboard=leaderboard,
        stats=stats,
        username=username,
        solved=solved,
        announcements=announcements
    )

@scoreboard_bp.route("/api/scoreboard")
def api_scoreboard():
    is_admin = current_user.is_authenticated and getattr(current_user, 'is_admin', False)
    live = LiveScoreboardService.get_live_rankings(is_admin_preview=is_admin)
    _, stats, _, challenges = ScoreboardService.get_scoreboard_data()
    return jsonify({
        "leaderboard": live["leaderboard"],
        "stats": stats,
        "challenges": {k: {"title": v["title"], "points": v["points"], "icon": v.get("icon","")}
                       for k, v in challenges.items()},
        "freeze_active": live["freeze_active"],
        "timer": live["timer"]
    })

@scoreboard_bp.route("/api/live/timeline")
def api_live_timeline():
    """Returns a time-ordered list of solve events for a live activity feed."""
    from app.repositories.submission_repository import SubmissionRepository
    from app.repositories.challenge_repository import ChallengeRepository
    limit = request.args.get("limit", 30, type=int)
    subs = SubmissionRepository.get_recent(limit=limit, correct_only=True)
    challenges = {c.id: c for c in ChallengeRepository.get_all(include_hidden=True)}
    events = []
    for sub in subs:
        ch = challenges.get(sub.challenge_id)
        events.append({
            "user_id": sub.user_id,
            "challenge_id": sub.challenge_id,
            "challenge_title": ch.title if ch else "Unknown",
            "points": sub.points,
            "time": sub.time.isoformat() if sub.time else None,
        })
    return jsonify({"events": events})
