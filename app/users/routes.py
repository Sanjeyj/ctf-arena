from flask import jsonify
from app.users import users_bp

@users_bp.route("/api/v2/users/placeholder")
def placeholder():
    return jsonify({"blueprint": "users"})
