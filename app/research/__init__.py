from flask import Blueprint

research_bp = Blueprint('research', __name__)

from app.research import routes  # noqa: F401, E402
