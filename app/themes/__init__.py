from flask import Blueprint

themes_bp = Blueprint("themes", __name__)

from app.themes import routes, errors
