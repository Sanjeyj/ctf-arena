from flask import jsonify
from app.api import api_bp

@api_bp.route("/api/v1/health")
def health():
    return jsonify({"status": "ok", "api": "v2"})
