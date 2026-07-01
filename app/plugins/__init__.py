from flask import Blueprint

plugins_bp = Blueprint("plugins", __name__)

from app.plugins import routes, errors
