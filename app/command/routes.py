"""
Command REST API and Admin Routes - Phase 29 Global Cyber Command Center.
Endpoints for command centers, global operations, CERT teams, war games, strategic objectives, and crisis rooms.
"""
import base64
import hmac
import hashlib
import json
from functools import wraps
from flask import request, jsonify, render_template, current_app

from app.command import command_bp
from app.extensions import db
from app.utils.decorators import require_admin

# Services
from app.services.command_service import CommandService
from app.services.operations_service import OperationsService
from app.services.cert_service import CertService
from app.services.wargame_service import WargameService
from app.services.strategic_service import StrategicService
from app.services.executive_command_ai import ExecutiveCommandAI

# Models
from app.models.command_center import CommandCenter
from app.models.global_operation import GlobalOperation
from app.models.cert_team import CertTeam
from app.models.war_game import WarGame
from app.models.strategic_objective import StrategicObjective
from app.models.crisis_room import CrisisRoom
from app.models.threat_campaign_global import ThreatCampaignGlobal
from app.models.command_metric import CommandMetric


# ─────────────────────────────────────────────────────────────────────────────
# Lightweight JWT Crypto Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _decode_jwt(token: str, secret: str) -> dict:
    """Decode and verify HS256 JWT signature."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        sig_input = f"{header_b64}.{payload_b64}"
        sig = hmac.new(secret.encode(), sig_input.encode(), hashlib.sha256).digest()
        expected = base64.urlsafe_b64encode(sig).decode().rstrip('=')
        if not hmac.compare_digest(sig_b64, expected):
            return None
        pad = payload_b64 + '=' * (4 - len(payload_b64) % 4)
        return json.loads(base64.urlsafe_b64decode(pad).decode())
    except Exception:
        return None


def jwt_required(f):
    """Decorator to enforce JWT Bearer token authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid token'}), 401
        token = auth_header[7:]
        secret = current_app.config.get('SECRET_KEY', 'default_secret')
        payload = _decode_jwt(token, secret)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────────────────────────────────────
# REST API Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@command_bp.route('/api/v1/command', methods=['GET'])
@jwt_required
def api_get_command():
    """GET /api/v1/command — list all command centers for an org."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    centers = CommandCenter.query.filter_by(organization_id=org_id).all()
    return jsonify([c.to_dict() for c in centers]), 200


@command_bp.route('/api/v1/operations', methods=['GET'])
@jwt_required
def api_get_operations():
    """GET /api/v1/operations — list all global operations for an org."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    ops = GlobalOperation.query.filter_by(organization_id=org_id).all()
    return jsonify([o.to_dict() for o in ops]), 200


@command_bp.route('/api/v1/cert', methods=['GET'])
@jwt_required
def api_get_cert():
    """GET /api/v1/cert — list all CERT teams for an org."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    certs = CertTeam.query.filter_by(organization_id=org_id).all()
    return jsonify([c.to_dict() for c in certs]), 200


@command_bp.route('/api/v1/wargames', methods=['GET'])
@jwt_required
def api_get_wargames():
    """GET /api/v1/wargames — list all war games for an org."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    games = WarGame.query.filter_by(organization_id=org_id).all()
    return jsonify([g.to_dict() for g in games]), 200


@command_bp.route('/api/v1/strategy', methods=['GET'])
@jwt_required
def api_get_strategy():
    """GET /api/v1/strategy — list all strategic objectives for an org."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    objectives = StrategicObjective.query.filter_by(organization_id=org_id).all()
    return jsonify([o.to_dict() for o in objectives]), 200


@command_bp.route('/api/v1/crisis', methods=['GET'])
@jwt_required
def api_get_crisis():
    """GET /api/v1/crisis — list all crisis rooms for an org."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    rooms = CrisisRoom.query.filter_by(organization_id=org_id).all()
    return jsonify([r.to_dict() for r in rooms]), 200


# ─────────────────────────────────────────────────────────────────────────────
# Admin Routes
# ─────────────────────────────────────────────────────────────────────────────

@command_bp.route('/admin/command', methods=['GET'])
@require_admin
def admin_command():
    """Admin: Command center overview dashboard."""
    centers = CommandCenter.query.all()
    return render_template('admin_command.html', centers=centers)


@command_bp.route('/admin/command/operations', methods=['GET'])
@require_admin
def admin_command_operations():
    """Admin: Global operations dashboard."""
    operations = GlobalOperation.query.order_by(GlobalOperation.created_at.desc()).all()
    return render_template('admin_operations.html', operations=operations)


@command_bp.route('/admin/command/cert', methods=['GET'])
@require_admin
def admin_command_cert():
    """Admin: CERT teams dashboard."""
    certs = CertTeam.query.order_by(CertTeam.trust_score.desc()).all()
    return render_template('admin_cert.html', certs=certs)


@command_bp.route('/admin/command/wargames', methods=['GET'])
@require_admin
def admin_command_wargames():
    """Admin: War games dashboard."""
    games = WarGame.query.order_by(WarGame.created_at.desc()).all()
    return render_template('admin_wargames.html', games=games)


@command_bp.route('/admin/command/crisis', methods=['GET'])
@require_admin
def admin_command_crisis():
    """Admin: Crisis room dashboard."""
    rooms = CrisisRoom.query.filter_by(active=True).all()
    return render_template('admin_crisis_room.html', rooms=rooms)
