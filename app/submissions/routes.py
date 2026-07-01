from flask import jsonify
from app.submissions import submissions_bp

@submissions_bp.route("/api/v2/submissions/placeholder")
def placeholder():
    return jsonify({"blueprint": "submissions"})
