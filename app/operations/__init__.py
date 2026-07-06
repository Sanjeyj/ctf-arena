"""
Operations blueprint - Phase 33 Cyber Platform Observability, Reliability & Operations Fabric.
"""
from flask import Blueprint

operations_bp = Blueprint('operations_fabric', __name__)

from app.operations import routes  # noqa: F401, E402
