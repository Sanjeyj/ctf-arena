"""
Exposure blueprint definition - Phase 34 Security Architecture, Exposure & Attack Surface Management Fabric.
"""
from flask import Blueprint

exposure_bp = Blueprint('exposure', __name__)

from app.exposure import routes
