"""
Control Plane REST API and Admin Routes - Phase 31 Cyber Platform Control Plane.
Enforces multi-tenant isolation, JWT authentication, and policy enforcement.
"""
import base64
import hmac
import hashlib
import json
from functools import wraps
from flask import request, jsonify, render_template, current_app

from app.control_plane import control_plane_bp
from app.extensions import db
from app.utils.decorators import require_admin

# Models
from app.models.platform_service import PlatformService
from app.models.service_dependency import ServiceDependency
from app.models.reliability_objective import ReliabilityObjective
from app.models.platform_feature_flag import PlatformFeatureFlag
from app.models.control_policy import ControlPolicy
from app.models.model_governance_record import ModelGovernanceRecord
from app.models.evidence_record import EvidenceRecord
from app.models.change_record import ChangeRecord

# Services
from app.services.platform_registry_service import PlatformRegistryService
from app.services.reliability_service import ReliabilityService
from app.services.feature_flag_service import FeatureFlagService
from app.services.control_policy_service import ControlPolicyService
from app.services.model_governance_service import ModelGovernanceService
from app.services.evidence_service import EvidenceService
from app.services.change_management_service import ChangeManagementService
from app.services.executive_control_ai import ExecutiveControlAI


# ─────────────────────────────────────────────────────────────────────────────
# JWT Crypto Helpers
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
    """Enforce JWT Bearer authentication."""
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
# REST Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@control_plane_bp.route('/api/v1/control-plane/services', methods=['GET'])
@jwt_required
def api_get_services():
    """GET /api/v1/control-plane/services — list registered services."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    services = PlatformRegistryService.list_services(org_id)
    return jsonify([s.to_dict() for s in services]), 200


@control_plane_bp.route('/api/v1/control-plane/services', methods=['POST'])
@jwt_required
def api_register_service():
    """POST /api/v1/control-plane/services — register logical service."""
    data = request.get_json() or {}
    name = data.get('service_name')
    stype = data.get('service_type')
    org_id = data.get('org_id') or request.args.get('org_id', type=int)
    if not name or not stype or not org_id:
        return jsonify({'error': 'service_name, service_type, and org_id are required'}), 400

    srv = PlatformRegistryService.register_service(
        service_name=name,
        service_type=stype,
        org_id=org_id,
        version=data.get('version', '1.0.0'),
        criticality=data.get('criticality', 'medium'),
        owner=data.get('owner')
    )
    return jsonify(srv.to_dict()), 201


@control_plane_bp.route('/api/v1/control-plane/dependencies', methods=['GET'])
@jwt_required
def api_get_dependencies():
    """GET /api/v1/control-plane/dependencies — get downstream dependencies health status map."""
    org_id = request.args.get('org_id', type=int)
    service_id = request.args.get('service_id', type=int)
    if not org_id or not service_id:
        return jsonify({'error': 'org_id and service_id required'}), 400
    status_map = PlatformRegistryService.dependency_status(service_id, org_id)
    return jsonify(status_map), 200


@control_plane_bp.route('/api/v1/control-plane/reliability', methods=['GET'])
@jwt_required
def api_get_reliability():
    """GET /api/v1/control-plane/reliability — list SLIs/SLOs objectives."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    objs = ReliabilityObjective.query.filter_by(organization_id=org_id).all()
    return jsonify([o.to_dict() for o in objs]), 200


@control_plane_bp.route('/api/v1/control-plane/reliability', methods=['POST'])
@jwt_required
def api_create_reliability():
    """POST /api/v1/control-plane/reliability — register SLI/SLO objective."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    data = request.get_json() or {}
    service_id = data.get('service_id')
    metric_name = data.get('metric_name')
    target_value = data.get('target_value')
    if not service_id or not metric_name or target_value is None:
        return jsonify({'error': 'service_id, metric_name, and target_value are required'}), 400

    obj = ReliabilityService.create_objective(
        service_id=service_id,
        metric_name=metric_name,
        target_value=target_value,
        org_id=org_id,
        measurement_window=data.get('measurement_window', '30d')
    )
    if not obj:
        return jsonify({'error': 'Service not found'}), 400
    return jsonify(obj.to_dict()), 201


@control_plane_bp.route('/api/v1/control-plane/flags', methods=['GET'])
@jwt_required
def api_get_flags():
    """GET /api/v1/control-plane/flags — list feature flags."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    flags = PlatformFeatureFlag.query.filter_by(organization_id=org_id).all()
    return jsonify([f.to_dict() for f in flags]), 200


@control_plane_bp.route('/api/v1/control-plane/flags', methods=['POST'])
@jwt_required
def api_create_flag():
    """POST /api/v1/control-plane/flags — create feature flag."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    data = request.get_json() or {}
    key = data.get('flag_key')
    if not key:
        return jsonify({'error': 'flag_key required'}), 400

    flag = FeatureFlagService.create_flag(
        flag_key=key,
        org_id=org_id,
        description=data.get('description'),
        enabled=data.get('enabled', False),
        rollout_percentage=data.get('rollout_percentage', 100),
        conditions=data.get('conditions')
    )
    return jsonify(flag.to_dict()), 201


@control_plane_bp.route('/api/v1/control-plane/flags/<int:flag_id>/evaluate', methods=['POST'])
@jwt_required
def api_evaluate_flag(flag_id):
    """POST /api/v1/control-plane/flags/<id>/evaluate — evaluate feature flag deterministically."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400

    flag = db.session.get(PlatformFeatureFlag, flag_id)
    if not flag or flag.organization_id != org_id:
        return jsonify({'error': 'Flag not found'}), 404

    val = FeatureFlagService.evaluate(flag.flag_key, str(user_id), org_id)
    return jsonify({'enabled': val}), 200


@control_plane_bp.route('/api/v1/control-plane/policies', methods=['GET'])
@jwt_required
def api_get_policies():
    """GET /api/v1/control-plane/policies — list policies."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    pols = ControlPolicy.query.filter_by(organization_id=org_id).all()
    return jsonify([p.to_dict() for p in pols]), 200


@control_plane_bp.route('/api/v1/control-plane/policies', methods=['POST'])
@jwt_required
def api_create_policy():
    """POST /api/v1/control-plane/policies — create control policy rule."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    data = request.get_json() or {}
    name = data.get('policy_name')
    ptype = data.get('policy_type')
    if not name or not ptype:
        return jsonify({'error': 'policy_name and policy_type are required'}), 400

    pol = ControlPolicyService.create_policy(
        policy_name=name,
        policy_type=ptype,
        org_id=org_id,
        rule=data.get('rule'),
        enforcement_mode=data.get('enforcement_mode', 'observe')
    )
    return jsonify(pol.to_dict()), 201


@control_plane_bp.route('/api/v1/control-plane/policies/<int:policy_id>/evaluate', methods=['POST'])
@jwt_required
def api_evaluate_policy(policy_id):
    """POST /api/v1/control-plane/policies/<id>/evaluate — evaluate control policy against context."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    data = request.get_json() or {}
    context = data.get('context')
    if context is None:
        return jsonify({'error': 'context required'}), 400

    res = ControlPolicyService.evaluate(policy_id, context, org_id)
    return jsonify(res), 200


@control_plane_bp.route('/api/v1/control-plane/models', methods=['GET'])
@jwt_required
def api_get_models():
    """GET /api/v1/control-plane/models — list AI governance models."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    recs = ModelGovernanceRecord.query.filter_by(organization_id=org_id).all()
    return jsonify([r.to_dict() for r in recs]), 200


@control_plane_bp.route('/api/v1/control-plane/models', methods=['POST'])
@jwt_required
def api_register_model():
    """POST /api/v1/control-plane/models — register AI model."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    data = request.get_json() or {}
    name = data.get('model_name')
    prov = data.get('provider')
    if not name or not prov:
        return jsonify({'error': 'model_name and provider are required'}), 400

    rec = ModelGovernanceService.register_model(
        model_name=name,
        provider=prov,
        org_id=org_id,
        purpose=data.get('purpose'),
        risk_level=data.get('risk_level', 'medium')
    )
    return jsonify(rec.to_dict()), 201


@control_plane_bp.route('/api/v1/control-plane/evidence', methods=['GET'])
@jwt_required
def api_get_evidence():
    """GET /api/v1/control-plane/evidence — search evidence records."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    module = request.args.get('source_module')
    evidence = EvidenceService.search(org_id, module)
    return jsonify([e.to_dict() for e in evidence]), 200


@control_plane_bp.route('/api/v1/control-plane/evidence', methods=['POST'])
@jwt_required
def api_collect_evidence():
    """POST /api/v1/control-plane/evidence — collect compliance metadata evidence."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    data = request.get_json() or {}
    etype = data.get('evidence_type')
    source = data.get('source_module')
    res_type = data.get('resource_type')
    res_id = data.get('resource_id')
    summary = data.get('summary')
    if not etype or not source or not res_type or not res_id or not summary:
        return jsonify({'error': 'evidence_type, source_module, resource_type, resource_id, and summary are required'}), 400

    rec = EvidenceService.collect(etype, source, res_type, res_id, summary, org_id)
    return jsonify(rec.to_dict()), 201


@control_plane_bp.route('/api/v1/control-plane/changes', methods=['GET'])
@jwt_required
def api_get_changes():
    """GET /api/v1/control-plane/changes — list changes requested."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    records = ChangeRecord.query.filter_by(organization_id=org_id).all()
    return jsonify([r.to_dict() for r in records]), 200


@control_plane_bp.route('/api/v1/control-plane/changes', methods=['POST'])
@jwt_required
def api_request_change():
    """POST /api/v1/control-plane/changes — request platform change."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    data = request.get_json() or {}
    ctype = data.get('change_type')
    res_type = data.get('resource_type')
    res_id = data.get('resource_id')
    by = data.get('requested_by')
    if not ctype or not res_type or not res_id or not by:
        return jsonify({'error': 'change_type, resource_type, resource_id, and requested_by are required'}), 400

    rec = ChangeManagementService.request_change(ctype, res_type, res_id, by, org_id, data.get('rollback_plan'))
    return jsonify(rec.to_dict()), 201


@control_plane_bp.route('/api/v1/control-plane/changes/<int:change_id>/simulate', methods=['POST'])
@jwt_required
def api_simulate_change(change_id):
    """POST /api/v1/control-plane/changes/<id>/simulate — simulate change rollout validation."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    rec = db.session.get(ChangeRecord, change_id)
    if not rec or rec.organization_id != org_id:
        return jsonify({'error': 'Change request not found'}), 404

    ChangeManagementService.assess_risk(change_id, org_id)
    simulated = ChangeManagementService.simulate(change_id, org_id)
    return jsonify(simulated.to_dict()), 200


@control_plane_bp.route('/api/v1/control-plane/brief', methods=['GET'])
@jwt_required
def api_get_brief():
    """GET /api/v1/control-plane/brief — retrieve AI governance briefing."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    brief = ExecutiveControlAI.generate_governance_brief(org_id)
    summary = ExecutiveControlAI.summarize_platform(org_id)
    rec = ExecutiveControlAI.recommend_priorities(org_id)
    return jsonify({
        'brief': brief,
        'summary': summary,
        'recommendations': rec
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# Admin Dashboard Routes
# ─────────────────────────────────────────────────────────────────────────────

@control_plane_bp.route('/admin/control-plane', methods=['GET'])
@require_admin
def admin_control_plane():
    """Admin: Overview command center dashboard."""
    services = PlatformService.query.all()
    return render_template('admin_control_plane.html', services=services)


@control_plane_bp.route('/admin/control-plane/services', methods=['GET'])
@require_admin
def admin_platform_services():
    """Admin: Service registry catalog and dependency trees."""
    services = PlatformService.query.all()
    dependencies = ServiceDependency.query.all()
    return render_template('admin_platform_services.html', services=services, dependencies=dependencies)


@control_plane_bp.route('/admin/control-plane/reliability', methods=['GET'])
@require_admin
def admin_reliability():
    """Admin: SLIs, SLOs, and error budgets indicators."""
    objectives = ReliabilityObjective.query.all()
    return render_template('admin_reliability.html', objectives=objectives)


@control_plane_bp.route('/admin/control-plane/policies', methods=['GET'])
@require_admin
def admin_control_policies():
    """Admin: Policy rules enforcement modes catalog."""
    policies = ControlPolicy.query.all()
    return render_template('admin_control_policies.html', policies=policies)


@control_plane_bp.route('/admin/control-plane/models', methods=['GET'])
@require_admin
def admin_model_governance():
    """Admin: Model safety risk review records."""
    records = ModelGovernanceRecord.query.all()
    return render_template('admin_model_governance.html', records=records)


@control_plane_bp.route('/admin/control-plane/evidence', methods=['GET'])
@require_admin
def admin_evidence():
    """Admin: Compliance evidence hashes registry."""
    evidence = EvidenceRecord.query.order_by(EvidenceRecord.collected_at.desc()).all()
    return render_template('admin_evidence.html', evidence=evidence)


@control_plane_bp.route('/admin/control-plane/changes', methods=['GET'])
@require_admin
def admin_changes():
    """Admin: Rollout workflow change logs."""
    changes = ChangeRecord.query.order_by(ChangeRecord.id.desc()).all()
    return render_template('admin_changes.html', changes=changes)
