"""
Assurance blueprint - Phase 32 Cyber Trust, Assurance & Verification Fabric.
"""
from flask import Blueprint

assurance_bp = Blueprint('assurance', __name__)

from app.assurance import routes  # noqa: F401, E402
