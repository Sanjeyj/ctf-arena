from flask import Blueprint

ecosystem_bp = Blueprint('ecosystem', __name__)

from app.ecosystem import routes  # noqa: F401, E402
