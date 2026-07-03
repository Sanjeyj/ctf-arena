from flask import Blueprint

defense_bp = Blueprint('defense', __name__)

from app.defense import routes  # noqa: F401, E402
