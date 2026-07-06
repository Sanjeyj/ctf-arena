"""
Control Plane blueprint - Phase 31 Cyber Platform Control Plane.
"""
from flask import Blueprint

control_plane_bp = Blueprint('control_plane', __name__)

from app.control_plane import routes  # noqa: F401, E402
