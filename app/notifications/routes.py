from flask import jsonify
from app.notifications import notifications_bp

@notifications_bp.route("/api/v2/notifications/placeholder")
def placeholder():
    return jsonify({"blueprint": "notifications"})
