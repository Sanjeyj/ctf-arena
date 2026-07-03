from flask import Blueprint

cloud_bp = Blueprint('cloud', __name__)

from app.cloud import routes  # noqa: F401, E402
