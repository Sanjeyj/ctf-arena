from flask import Blueprint

submissions_bp = Blueprint("submissions", __name__)

from app.submissions import routes, errors
