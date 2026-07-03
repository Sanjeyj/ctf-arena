from flask import Blueprint

secos_bp = Blueprint('secos', __name__)

from app.secos import routes  # noqa: F401, E402
