from flask import Blueprint

strategic_resilience_bp = Blueprint('strategic_resilience', __name__)

from app.strategic_resilience import routes
