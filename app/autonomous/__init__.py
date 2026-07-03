from flask import Blueprint

autonomous_bp = Blueprint('autonomous', __name__)

from app.autonomous import routes  # noqa: F401, E402
