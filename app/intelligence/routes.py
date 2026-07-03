"""
Intelligence REST API and Admin Routes - Phase 27 Global Security Intelligence Network.
Endpoints for intelligence reports, forecasting, trust networks, observatory, and federation.
"""
import base64
import hmac
import hashlib
import json
from functools import wraps
from flask import request, jsonify, render_template, current_app

from app.intelligence import intelligence_bp
from app.extensions import db
from app.utils.decorators import require_admin

from app.services.intelligence_service import IntelligenceService
from app.services.forecast_service import ForecastService
from app.services.trust_service import TrustService
from app.services.observatory_service import ObservatoryService
from app.services.intelligence_ai_service import IntelligenceAIService
from app.services.federation_service import FederationService

from app.models.intelligence_report import IntelligenceReport
from app.models.forecast_event import ForecastEvent
from app.models.trust_network import TrustNetwork
from app.models.observatory_node import ObservatoryNode
from app.models.global_threat_feed import GlobalThreatFeed
from app.models.intelligence_source import IntelligenceSource


# ─────────────────────────────────────────────────────────────────────────────
# Lightweight JWT helpers (stdlib only)
# ─────────────────────────────────────────────────────────────────────────────

def _decode_jwt(token: str, secret: str) -> dict:
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
# Admin HTML Routes
# ─────────────────────────────────────────────────────────────────────────────

@intelligence_bp.route('/admin/intelligence/reports', methods=['GET'])
@require_admin
def admin_intelligence():
    """Render intelligence reports admin dashboard."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int)
    reports = IntelligenceService.list_reports(org_id)
    feeds_q = GlobalThreatFeed.query
    if org_id:
        feeds_q = GlobalThreatFeed.tenant_filter(feeds_q, org_id)
    feeds = feeds_q.all()
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_intelligence.html',
        reports=reports, feeds=feeds,
        current_org_id=org_id, stats=stats, challenges=challenges, leaderboard=[]
    )


@intelligence_bp.route('/admin/intelligence/forecast', methods=['GET'])
@require_admin
def admin_forecast():
    """Render threat forecast admin dashboard."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int)
    q = ForecastEvent.query
    if org_id:
        q = ForecastEvent.tenant_filter(q, org_id)
    events = q.order_by(ForecastEvent.created_at.desc()).all()
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_forecast.html',
        events=events, current_org_id=org_id,
        stats=stats, challenges=challenges, leaderboard=[]
    )


@intelligence_bp.route('/admin/intelligence/observatory', methods=['GET'])
@require_admin
def admin_observatory():
    """Render global observatory node health admin dashboard."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int)
    nodes = ObservatoryService.monitor(org_id)
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_observatory.html',
        nodes=nodes, current_org_id=org_id,
        stats=stats, challenges=challenges, leaderboard=[]
    )


@intelligence_bp.route('/admin/intelligence/trust', methods=['GET'])
@require_admin
def admin_trust_network():
    """Render trust network relationship admin dashboard."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int)
    q = TrustNetwork.query
    if org_id:
        q = TrustNetwork.tenant_filter(q, org_id)
    relationships = q.all()
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_trust_network.html',
        relationships=relationships, current_org_id=org_id,
        stats=stats, challenges=challenges, leaderboard=[]
    )


@intelligence_bp.route('/admin/intelligence/global', methods=['GET'])
@require_admin
def admin_global_security():
    """Render unified global security command center."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int)
    report_count = IntelligenceReport.query.count()
    forecast_count = ForecastEvent.query.count()
    node_count = ObservatoryNode.query.count()
    trust_count = TrustNetwork.query.count()
    recommendations = IntelligenceAIService.recommend(org_id)
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_global_security.html',
        report_count=report_count, forecast_count=forecast_count,
        node_count=node_count, trust_count=trust_count,
        recommendations=recommendations, current_org_id=org_id,
        stats=stats, challenges=challenges, leaderboard=[]
    )


# ─────────────────────────────────────────────────────────────────────────────
# REST API Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@intelligence_bp.route('/api/v1/intelligence', methods=['GET'])
@jwt_required
def api_get_intelligence():
    """List intelligence reports."""
    org_id = request.args.get('org_id', type=int)
    reports = IntelligenceService.list_reports(org_id)
    return jsonify([r.to_dict() for r in reports]), 200


@intelligence_bp.route('/api/v1/intelligence', methods=['POST'])
@jwt_required
def api_post_intelligence():
    """Ingest a new intelligence report."""
    data = request.get_json() or {}
    if not data.get('title') or not data.get('source'):
        return jsonify({'error': 'title and source are required'}), 400
    org_id = data.get('organization_id')
    report = IntelligenceService.ingest(data, organization_id=org_id)
    return jsonify(report.to_dict()), 201


@intelligence_bp.route('/api/v1/forecast', methods=['GET'])
@jwt_required
def api_get_forecast():
    """List threat forecast events."""
    org_id = request.args.get('org_id', type=int)
    q = ForecastEvent.query
    if org_id:
        q = ForecastEvent.tenant_filter(q, org_id)
    events = q.order_by(ForecastEvent.created_at.desc()).all()
    return jsonify([e.to_dict() for e in events]), 200


@intelligence_bp.route('/api/v1/trust', methods=['GET'])
@jwt_required
def api_get_trust():
    """Query trust network relationships."""
    org_id = request.args.get('org_id', type=int)
    q = TrustNetwork.query
    if org_id:
        q = TrustNetwork.tenant_filter(q, org_id)
    relationships = q.all()
    return jsonify([r.to_dict() for r in relationships]), 200


@intelligence_bp.route('/api/v1/observatory', methods=['GET'])
@jwt_required
def api_get_observatory():
    """List observatory node statuses."""
    org_id = request.args.get('org_id', type=int)
    nodes = ObservatoryService.monitor(org_id)
    return jsonify(nodes), 200


@intelligence_bp.route('/api/v1/federation', methods=['GET'])
@jwt_required
def api_get_federation():
    """List federation subscriptions for an org."""
    org_id = request.args.get('org_id', type=int)
    q = IntelligenceSource.query.filter_by(source_type='federated')
    if org_id:
        q = IntelligenceSource.tenant_filter(q, org_id)
    sources = q.all()
    return jsonify([s.to_dict() for s in sources]), 200
