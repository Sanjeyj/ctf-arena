from flask import jsonify
from app.teams import teams_bp

@teams_bp.route("/api/v2/teams/placeholder")
def placeholder():
    return jsonify({"blueprint": "teams"})
