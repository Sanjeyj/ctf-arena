from flask import jsonify
from app.themes import themes_bp

@themes_bp.route("/api/v2/themes/placeholder")
def placeholder():
    return jsonify({"blueprint": "themes"})
