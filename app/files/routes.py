from flask import jsonify
from app.files import files_bp

@files_bp.route("/api/v2/files/placeholder")
def placeholder():
    return jsonify({"blueprint": "files"})
