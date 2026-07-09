from flask import Blueprint

governance_intelligence_bp = Blueprint('governance_intelligence', __name__)

from app.governance_intelligence import routes
