from flask import Blueprint

mission_control_bp = Blueprint('mission_control', __name__)

from app.mission_control import routes
