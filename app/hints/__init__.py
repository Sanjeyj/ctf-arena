from flask import Blueprint

hints_bp = Blueprint("hints", __name__)

from app.hints import routes, errors
