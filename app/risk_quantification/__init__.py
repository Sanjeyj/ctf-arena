from flask import Blueprint

risk_quantification_bp = Blueprint('risk_quantification', __name__)

from app.risk_quantification import routes
