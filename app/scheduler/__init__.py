from flask import Blueprint

scheduler_bp = Blueprint("scheduler", __name__)

from app.scheduler import routes, errors
