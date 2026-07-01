from flask import Blueprint

flags_bp = Blueprint("flags", __name__)

from app.flags import routes, errors
