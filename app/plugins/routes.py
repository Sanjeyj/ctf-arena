from flask import jsonify
from app.plugins import plugins_bp

@plugins_bp.route("/api/v2/plugins/placeholder")
def placeholder():
    return jsonify({"blueprint": "plugins"})
