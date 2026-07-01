from flask import jsonify
from app.analytics import analytics_bp

@analytics_bp.route("/api/v2/analytics/placeholder")
def placeholder():
    return jsonify({"blueprint": "analytics"})
