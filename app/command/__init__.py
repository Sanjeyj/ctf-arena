"""
Command Center blueprint - Phase 29 Global Cyber Command Center.
"""
from flask import Blueprint

command_bp = Blueprint('command', __name__)

from app.command import routes  # noqa: F401, E402
