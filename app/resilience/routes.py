"""
Resilience REST API and Admin Routes - Phase 25 Cyber Resilience & Digital Enterprise.
Defines endpoints for business processes, disaster recovery, vendor risk, and insurance.
"""
import base64
import hmac
import hashlib
import json
from functools import wraps
from flask import request, jsonify, current_app, render_template
from flask_login import current_user

from app.resilience import resilience_bp
from app.extensions import db
from app.utils.decorators import require_admin

# Import services
from app.services.resilience_engine_service import ResilienceEngineService
from app.services.bcm_service import BCMService
from app.services.crisis_service import CrisisService
from app.services.vendor_risk_service import VendorRiskService
from app.services.insurance_service import InsuranceService
from app.services.executive_resilience_ai import ExecutiveResilienceAI

# Import models
from app.models.business_process import BusinessProcess
from app.models.business_impact_analysis import BusinessImpactAnalysis
from app.models.crisis_event import CrisisEvent
from app.models.third_party_vendor import ThirdPartyVendor
from app.models.insurance_policy import InsurancePolicy
from app.models.resilience_exercise import ResilienceExercise
from app.models.disaster_recovery_plan import DisasterRecoveryPlan

# ─────────────────────────────────────────────────────────────────────────────
# Lightweight JWT Crypto Helpers (Standard Library only)
# ─────────────────────────────────────────────────────────────────────────────

def decode_jwt(token: str, secret: str) -> dict:
    """Decode and verify signature of an HS256 JWT token."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        
        # Verify signature
        signature_input = f"{header_b64}.{payload_b64}"
        sig = hmac.new(secret.encode(), signature_input.encode(), hashlib.sha256).digest()
        
        def add_padding(val):
            return val + "=" * (4 - len(val) % 4)
            
        expected_sig_b64 = base64.urlsafe_b64encode(sig).decode().rstrip("=")
        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            return None
            
        payload_json = base64.urlsafe_b64decode(add_padding(payload_b64)).decode()
        return json.loads(payload_json)
    except Exception:
        return None


def jwt_required(f):
    """Decorator to enforce JWT Bearer token authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid authorization header"}), 401
        
        token = auth_header.split(' ')[1]
        secret = current_app.config.get('SECRET_KEY', 'default_secret')
        payload = decode_jwt(token, secret)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
            
        request.jwt_payload = payload
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────────────────────────────────────
# Admin Dashboard HTML Pages
# ─────────────────────────────────────────────────────────────────────────────

@resilience_bp.route('/admin/resilience', methods=['GET'])
@require_admin
def admin_resilience_center():
    """Render executive resilience center control panel."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int)
    
    score_info = ResilienceEngineService.calculate_resilience_score(org_id)
    forecast_info = ResilienceEngineService.forecast_failure(org_id)
    
    _, stats, challenges = AdminService.get_dashboard_stats()
    
    return render_template(
        'admin_resilience_center.html',
        score=score_info['resilience_score'],
        score_components=score_info['components'],
        forecast=forecast_info,
        current_org_id=org_id,
        stats=stats,
        challenges=challenges,
        leaderboard=[]
    )


@resilience_bp.route('/admin/resilience/crisis', methods=['GET'])
@require_admin
def admin_crisis():
    """Render crisis response coordination room."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int)
    
    crisis_query = CrisisEvent.query
    if org_id:
        crisis_query = CrisisEvent.tenant_filter(crisis_query, org_id)
    active_crises = crisis_query.filter_by(status='active').all()
    
    _, stats, challenges = AdminService.get_dashboard_stats()
    
    return render_template(
        'admin_crisis.html',
        active_crises=active_crises,
        current_org_id=org_id,
        stats=stats,
        challenges=challenges,
        leaderboard=[]
    )


@resilience_bp.route('/admin/resilience/bcp', methods=['GET'])
@require_admin
def admin_bcp():
    """Render Business Continuity (BCP) objective checklists."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int)
    
    rto_evaluation = BCMService.evaluate_rto(org_id)
    rpo_evaluation = BCMService.evaluate_rpo(org_id)
    
    plans_query = DisasterRecoveryPlan.query
    if org_id:
        plans_query = DisasterRecoveryPlan.tenant_filter(plans_query, org_id)
    plans = plans_query.all()
    
    _, stats, challenges = AdminService.get_dashboard_stats()
    
    return render_template(
        'admin_bcp.html',
        rto_eval=rto_evaluation,
        rpo_eval=rpo_evaluation,
        plans=plans,
        current_org_id=org_id,
        stats=stats,
        challenges=challenges,
        leaderboard=[]
    )


@resilience_bp.route('/admin/resilience/vendors', methods=['GET'])
@require_admin
def admin_vendor_risk():
    """Render third party vendor assessments dashboard."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int)
    
    vendor_query = ThirdPartyVendor.query
    if org_id:
        vendor_query = ThirdPartyVendor.tenant_filter(vendor_query, org_id)
    vendors = vendor_query.all()
    
    _, stats, challenges = AdminService.get_dashboard_stats()
    
    return render_template(
        'admin_vendor_risk.html',
        vendors=vendors,
        current_org_id=org_id,
        stats=stats,
        challenges=challenges,
        leaderboard=[]
    )


@resilience_bp.route('/admin/resilience/insurance', methods=['GET'])
@require_admin
def admin_insurance():
    """Render cyber insurance financial coverages page."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int)
    
    recommendations = InsuranceService.recommend_policy(org_id)
    
    policies_query = InsurancePolicy.query
    if org_id:
        policies_query = InsurancePolicy.tenant_filter(policies_query, org_id)
    policies = policies_query.all()
    
    _, stats, challenges = AdminService.get_dashboard_stats()
    
    return render_template(
        'admin_insurance.html',
        policies=policies,
        rec=recommendations,
        current_org_id=org_id,
        stats=stats,
        challenges=challenges,
        leaderboard=[]
    )


# ─────────────────────────────────────────────────────────────────────────────
# REST API Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@resilience_bp.route('/api/v1/resilience/processes', methods=['GET'])
@jwt_required
def api_get_processes():
    """Retrieve all critical business processes."""
    org_id = request.args.get('org_id', type=int)
    query = BusinessProcess.query
    if org_id:
        query = BusinessProcess.tenant_filter(query, org_id)
    processes = [p.to_dict() for p in query.all()]
    return jsonify(processes), 200


@resilience_bp.route('/api/v1/resilience/processes', methods=['POST'])
@jwt_required
def api_create_process():
    """Register a new business process."""
    data = request.get_json() or {}
    if not data.get('name'):
        return jsonify({'error': 'name is required'}), 400
    
    bp = BusinessProcess(
        name=data['name'],
        owner=data.get('owner'),
        criticality=data.get('criticality', 'medium'),
        rto=float(data.get('rto', 4.0)),
        rpo=float(data.get('rpo', 4.0)),
        status=data.get('status', 'active'),
        organization_id=data.get('organization_id')
    )
    db.session.add(bp)
    db.session.commit()
    return jsonify(bp.to_dict()), 201


@resilience_bp.route('/api/v1/crisis', methods=['GET'])
@jwt_required
def api_get_crisis():
    """Retrieve active or resolved crisis events."""
    org_id = request.args.get('org_id', type=int)
    query = CrisisEvent.query
    if org_id:
        query = CrisisEvent.tenant_filter(query, org_id)
    events = [e.to_dict() for e in query.all()]
    return jsonify(events), 200


@resilience_bp.route('/api/v1/crisis', methods=['POST'])
@jwt_required
def api_post_crisis():
    """Declare a new crisis event."""
    data = request.get_json() or {}
    if not data.get('event_name') or not data.get('severity'):
        return jsonify({'error': 'event_name and severity are required'}), 400
    
    crisis = CrisisService.declare_crisis(
        event_name=data['event_name'],
        severity=data['severity'],
        organization_id=data.get('organization_id')
    )
    return jsonify(crisis.to_dict()), 201


@resilience_bp.route('/api/v1/vendors', methods=['GET'])
@jwt_required
def api_get_vendors():
    """Retrieve supply chain vendor profiles."""
    org_id = request.args.get('org_id', type=int)
    query = ThirdPartyVendor.query
    if org_id:
        query = ThirdPartyVendor.tenant_filter(query, org_id)
    vendors = [v.to_dict() for v in query.all()]
    return jsonify(vendors), 200


@resilience_bp.route('/api/v1/vendors', methods=['POST'])
@jwt_required
def api_post_vendors():
    """Add a third-party vendor."""
    data = request.get_json() or {}
    if not data.get('vendor_name'):
        return jsonify({'error': 'vendor_name is required'}), 400
    
    vendor = VendorRiskService.assess_vendor(
        vendor_name=data['vendor_name'],
        service_type=data.get('service_type'),
        initial_risk=float(data.get('risk_score', 30.0)),
        organization_id=data.get('organization_id')
    )
    return jsonify(vendor.to_dict()), 201


@resilience_bp.route('/api/v1/insurance', methods=['GET'])
@jwt_required
def api_get_insurance():
    """Get recommendations and estimates for cyber insurance."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id is required'}), 400
    
    info = InsuranceService.recommend_policy(org_id)
    return jsonify(info), 200


@resilience_bp.route('/api/v1/bia', methods=['GET'])
@jwt_required
def api_get_bia():
    """Retrieve Business Impact Analysis metrics."""
    org_id = request.args.get('org_id', type=int)
    query = BusinessImpactAnalysis.query
    if org_id:
        query = BusinessImpactAnalysis.tenant_filter(query, org_id)
    bias = [b.to_dict() for b in query.all()]
    return jsonify(bias), 200


# ─────────────────────────────────────────────────────────────────────────────
# Copilot API
# ─────────────────────────────────────────────────────────────────────────────

@resilience_bp.route('/api/v1/resilience/copilot', methods=['POST'])
@jwt_required
def api_copilot():
    """Ask executive copilot a resilience question."""
    data = request.get_json() or {}
    question = data.get('question')
    org_id = request.args.get('org_id', type=int) or data.get('organization_id')
    
    if not question:
        return jsonify({'error': 'question is required'}), 400
    if not org_id:
        return jsonify({'error': 'organization_id or org_id query param is required'}), 400
        
    answer = ExecutiveResilienceAI.answer(question, org_id)
    return jsonify({'question': question, 'answer': answer}), 200
