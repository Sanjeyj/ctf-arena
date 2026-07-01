from flask import Blueprint

challenges_bp = Blueprint("challenges", __name__)

from app.challenges import routes, errors
