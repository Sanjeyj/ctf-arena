from flask import jsonify
from app.flags import flags_bp

@flags_bp.route("/api/v2/flags/placeholder")
def placeholder():
    return jsonify({"blueprint": "flags"})
