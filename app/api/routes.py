from flask import jsonify, current_app
from app.api import api_bp
from app.extensions import limiter

def get_api_limit():
    return current_app.config.get("RATE_LIMIT_API", "60 per minute")

@api_bp.route("/api/v1/health")
@limiter.limit(get_api_limit)
def health():
    return jsonify({"status": "ok", "api": "v2"})
