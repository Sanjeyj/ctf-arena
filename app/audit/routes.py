from flask import jsonify
from app.audit import audit_bp

@audit_bp.route("/api/v2/audit/placeholder")
def placeholder():
    return jsonify({"blueprint": "audit"})
