"""
Resilience Blueprint - Phase 25 Cyber Resilience & Digital Enterprise.
Defines endpoints for processes, crisis operations, vendor risks, and insurance.
"""
from flask import Blueprint

resilience_bp = Blueprint('resilience', __name__)

from app.resilience import routes
