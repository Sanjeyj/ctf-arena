from flask import jsonify
from app.certificates import certificates_bp

@certificates_bp.route("/api/v2/certificates/placeholder")
def placeholder():
    return jsonify({"blueprint": "certificates"})
