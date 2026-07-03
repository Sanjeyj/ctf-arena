"""
Intelligence Blueprint - Phase 27 Global Security Intelligence Network.
Defines endpoints for threat intelligence, forecasting, trust, observatory, and federation.
"""
from flask import Blueprint

intelligence_bp = Blueprint('intelligence', __name__)

from app.intelligence import routes
