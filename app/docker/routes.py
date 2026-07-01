from flask import jsonify
from app.docker import docker_bp

@docker_bp.route("/api/v2/docker/placeholder")
def placeholder():
    return jsonify({"blueprint": "docker"})
