"""
Enterprise Blueprint - Phase 26 Autonomous Cyber Enterprise.
Defines endpoints for agents, tasks, decisions, workflows, and self-healing.
"""
from flask import Blueprint

enterprise_bp = Blueprint('enterprise', __name__)

from app.enterprise import routes
