from flask import jsonify
from app.competitions import competitions_bp

@competitions_bp.route("/api/v2/competitions/placeholder")
def placeholder():
    return jsonify({"blueprint": "competitions"})
