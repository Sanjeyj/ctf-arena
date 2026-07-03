"""
Civilization REST API and Admin Routes - Phase 28 Cyber Civilization Platform.
Endpoints for cyber nations, workforce profiles, innovation, and global defense grids.
"""
import base64
import hmac
import hashlib
import json
from functools import wraps
from flask import request, jsonify, render_template, current_app

from app.civilization import civilization_bp
from app.extensions import db
from app.utils.decorators import require_admin

# Import services
from app.services.civilization_service import CivilizationService
from app.services.economy_service import EconomyService
from app.services.alliance_service import AllianceService
from app.services.innovation_service import InnovationService
from app.services.prediction_grid_service import PredictionGridService
from app.services.executive_civilization_ai import ExecutiveCivilizationAI

# Import models
from app.models.cyber_nation import CyberNation
from app.models.defense_grid import DefenseGrid
from app.models.innovation_project import InnovationProject
from app.models.security_economy import SecurityEconomy
from app.models.workforce_profile import WorkforceProfile
from app.models.defense_alliance import DefenseAlliance
from app.models.prediction_scenario import PredictionScenario
from app.models.civilization_metric import CivilizationMetric


# ─────────────────────────────────────────────────────────────────────────────
# Lightweight JWT Crypto Helpers (Standard Library only)
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
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        token = auth.split(' ', 1)[1]
        secret = current_app.config.get('SECRET_KEY', 'default_secret')
        payload = _decode_jwt(token, secret)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        request.jwt_payload = payload
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────────────────────────────────────
# Admin HTML Dashboard Routes
# ─────────────────────────────────────────────────────────────────────────────

@civilization_bp.route('/admin/civilization', methods=['GET'])
@require_admin
def admin_civilization():
    """Render cyber nations and baseline maturity panel."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int)
    
    nation_query = CyberNation.query
    if org_id:
        nation_query = CyberNation.tenant_filter(nation_query, org_id)
    nations = nation_query.all()
    
    benchmark = CivilizationService.benchmark(org_id) if org_id else {}
    _, stats, challenges = AdminService.get_dashboard_stats()
    
    return render_template(
        'admin_civilization.html',
        nations=nations,
        benchmark=benchmark,
        current_org_id=org_id,
        stats=stats,
        challenges=challenges,
        leaderboard=[]
    )


@civilization_bp.route('/admin/civilization/economy', methods=['GET'])
@require_admin
def admin_economy():
    """Render security investments and workforce profiles tracker."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int)
    
    econ_query = SecurityEconomy.query
    workforce_query = WorkforceProfile.query
    if org_id:
        econ_query = SecurityEconomy.tenant_filter(econ_query, org_id)
        workforce_query = WorkforceProfile.tenant_filter(workforce_query, org_id)
    
    economies = econ_query.all()
    profiles = workforce_query.all()
    
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_economy.html',
        economies=economies,
        profiles=profiles,
        current_org_id=org_id,
        stats=stats,
        challenges=challenges,
        leaderboard=[]
    )


@civilization_bp.route('/admin/civilization/alliances', methods=['GET'])
@require_admin
def admin_alliances():
    """Render trans-national defense alliances registry."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int)
    
    alliance_query = DefenseAlliance.query
    if org_id:
        alliance_query = DefenseAlliance.tenant_filter(alliance_query, org_id)
    alliances = alliance_query.all()
    
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_alliances.html',
        alliances=alliances,
        current_org_id=org_id,
        stats=stats,
        challenges=challenges,
        leaderboard=[]
    )


@civilization_bp.route('/admin/civilization/innovation', methods=['GET'])
@require_admin
def admin_innovation():
    """Render innovation and development registry."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int)
    
    projects = InnovationService.prioritize(org_id) if org_id else InnovationProject.query.all()
    
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_innovation.html',
        projects=projects,
        current_org_id=org_id,
        stats=stats,
        challenges=challenges,
        leaderboard=[]
    )


@civilization_bp.route('/admin/civilization/grid', methods=['GET'])
@require_admin
def admin_global_grid():
    """Render autonomous defense grid command room."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int)
    
    grid_query = DefenseGrid.query
    if org_id:
        grid_query = DefenseGrid.tenant_filter(grid_query, org_id)
    grids = grid_query.all()
    
    sync_info = AllianceService.synchronize(org_id) if org_id else {}
    _, stats, challenges = AdminService.get_dashboard_stats()
    
    return render_template(
        'admin_global_grid.html',
        grids=grids,
        sync_info=sync_info,
        current_org_id=org_id,
        stats=stats,
        challenges=challenges,
        leaderboard=[]
    )


# ─────────────────────────────────────────────────────────────────────────────
# REST API Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@civilization_bp.route('/api/v1/civilization', methods=['GET'])
@jwt_required
def api_get_civilization():
    """Retrieve all cyber nations."""
    org_id = request.args.get('org_id', type=int)
    query = CyberNation.query
    if org_id:
        query = CyberNation.tenant_filter(query, org_id)
    nations = [n.to_dict() for n in query.all()]
    return jsonify(nations), 200


@civilization_bp.route('/api/v1/economy', methods=['GET'])
@jwt_required
def api_get_economy():
    """Retrieve security economies data."""
    org_id = request.args.get('org_id', type=int)
    query = SecurityEconomy.query
    if org_id:
        query = SecurityEconomy.tenant_filter(query, org_id)
    economies = [e.to_dict() for e in query.all()]
    return jsonify(economies), 200


@civilization_bp.route('/api/v1/alliances', methods=['GET'])
@jwt_required
def api_get_alliances():
    """Retrieve all defense alliances."""
    org_id = request.args.get('org_id', type=int)
    query = DefenseAlliance.query
    if org_id:
        query = DefenseAlliance.tenant_filter(query, org_id)
    alliances = [a.to_dict() for a in query.all()]
    return jsonify(alliances), 200


@civilization_bp.route('/api/v1/innovation', methods=['GET'])
@jwt_required
def api_get_innovation():
    """Retrieve R&D innovation projects."""
    org_id = request.args.get('org_id', type=int)
    query = InnovationProject.query
    if org_id:
        query = InnovationProject.tenant_filter(query, org_id)
    projects = [p.to_dict() for p in query.all()]
    return jsonify(projects), 200


@civilization_bp.route('/api/v1/predictions', methods=['GET'])
@jwt_required
def api_get_predictions():
    """Retrieve threat forecasting scenarios."""
    org_id = request.args.get('org_id', type=int)
    query = PredictionScenario.query
    if org_id:
        query = PredictionScenario.tenant_filter(query, org_id)
    scenarios = [s.to_dict() for s in query.all()]
    return jsonify(scenarios), 200


@civilization_bp.route('/api/v1/civilization/metrics', methods=['GET'])
@jwt_required
def api_get_civilization_metrics():
    """Retrieve civilization composite metrics."""
    org_id = request.args.get('org_id', type=int)
    query = CivilizationMetric.query
    if org_id:
        query = CivilizationMetric.tenant_filter(query, org_id)
    metrics = [m.to_dict() for m in query.all()]
    return jsonify(metrics), 200
