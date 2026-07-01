from flask import Blueprint

competitions_bp = Blueprint("competitions", __name__)

from app.competitions import routes, errors
