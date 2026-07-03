"""
Civilization Blueprint - Phase 28 Cyber Civilization Platform.
Defines endpoints for cyber nations, economies, alliances, innovation, and global grids.
"""
from flask import Blueprint

civilization_bp = Blueprint('civilization', __name__)

from app.civilization import routes
