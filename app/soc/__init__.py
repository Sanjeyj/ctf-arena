from flask import Blueprint

soc_bp = Blueprint('soc', __name__)

from app.soc import routes  # noqa: F401, E402
