from flask import Blueprint

org_bp = Blueprint('organization', __name__)

from app.organization import routes  # noqa: F401, E402
