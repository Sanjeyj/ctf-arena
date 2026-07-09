from flask import Blueprint

systemic_resilience_bp = Blueprint('systemic_resilience', __name__)

from app.systemic_resilience import routes
