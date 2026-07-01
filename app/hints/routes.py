from flask import jsonify
from app.hints import hints_bp

@hints_bp.route("/api/v2/hints/placeholder")
def placeholder():
    return jsonify({"blueprint": "hints"})
