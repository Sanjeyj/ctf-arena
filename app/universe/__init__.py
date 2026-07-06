"""
Universe blueprint - Phase 30 Unified Cyber Defense Universe.
"""
from flask import Blueprint

universe_bp = Blueprint('universe', __name__)

from app.universe import routes  # noqa: F401, E402
