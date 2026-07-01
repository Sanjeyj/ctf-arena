from flask import jsonify
from app.announcements import announcements_bp

@announcements_bp.route("/api/v2/announcements/placeholder")
def placeholder():
    return jsonify({"blueprint": "announcements"})
