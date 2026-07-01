from flask import jsonify
from app.scheduler import scheduler_bp

@scheduler_bp.route("/api/v2/scheduler/placeholder")
def placeholder():
    return jsonify({"blueprint": "scheduler"})
