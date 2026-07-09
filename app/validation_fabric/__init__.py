"""
validation_fabric Blueprint Initialization - Phase 35.
Defines the blueprint.
"""
from flask import Blueprint

validation_fabric_bp = Blueprint('validation_fabric', __name__)

from app.validation_fabric import routes
