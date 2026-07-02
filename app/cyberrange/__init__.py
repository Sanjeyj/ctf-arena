from flask import Blueprint

cyberrange_bp = Blueprint('cyberrange', __name__)

from app.cyberrange import routes  # noqa: F401, E402
