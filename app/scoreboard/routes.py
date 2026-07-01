from flask import render_template, request, jsonify, session
from app.scoreboard import scoreboard_bp
from app.services.scoreboard_service import ScoreboardService

@scoreboard_bp.route("/scoreboard")
def scoreboard():
    username = session.get("user")
    leaderboard, stats, solved, challenges = ScoreboardService.get_scoreboard_data(username)
    return render_template(
        "scoreboard.html",
        challenges=challenges,
        leaderboard=leaderboard,
        stats=stats,
        username=username,
        solved=solved
    )

@scoreboard_bp.route("/api/scoreboard")
def api_scoreboard():
    leaderboard, stats, _, challenges = ScoreboardService.get_scoreboard_data()
    return jsonify({
        "leaderboard": leaderboard,
        "stats": stats,
        "challenges": {k: {"title": v["title"], "points": v["points"]} for k, v in challenges.items()},
    })
