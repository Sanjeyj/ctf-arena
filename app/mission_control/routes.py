import base64
import hmac
import hashlib
import json
import datetime
from functools import wraps
from flask import request, jsonify, render_template, current_app

from app.mission_control import mission_control_bp
from app.extensions import db
from app.utils.decorators import require_admin

# Models
from app.models.platform_capability import PlatformCapability
from app.models.capability_dependency import CapabilityDependency
from app.models.platform_certification_run import PlatformCertificationRun
from app.models.certification_check import CertificationCheck
from app.models.release_baseline import ReleaseBaseline
from app.models.release_gate_decision import ReleaseGateDecision
from app.models.architecture_decision_record import ArchitectureDecisionRecord
from app.models.platform_readiness_metric import PlatformReadinessMetric

# Services
from app.services.capability_registry_service import CapabilityRegistryService
from app.services.platform_certification_service import PlatformCertificationService
from app.services.architecture_convergence_service import ArchitectureConvergenceService
from app.services.release_baseline_service import ReleaseBaselineService
from app.services.platform_readiness_service import PlatformReadinessService
from app.services.release_gate_service import ReleaseGateService
from app.services.architecture_decision_service import ArchitectureDecisionService
from app.services.executive_platform_ai import ExecutivePlatformAI
from app.services.hook_service import HookService


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

@mission_control_bp.route('/api/v1/mission-control/overview', methods=['GET'])
@jwt_required
def api_overview():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    summary = CapabilityRegistryService.capability_summary(org_id)
    return jsonify(summary), 200


@mission_control_bp.route('/api/v1/mission-control/capabilities', methods=['GET'])
@jwt_required
def api_get_capabilities():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    caps = CapabilityRegistryService.discover_capabilities(org_id)
    return jsonify(caps), 200


@mission_control_bp.route('/api/v1/mission-control/capabilities', methods=['POST'])
@jwt_required
def api_register_capability():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    key = data.get('capability_key')
    name = data.get('name')
    phase = data.get('phase_introduced')
    if not org_id or not key or not name or phase is None:
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        cap = CapabilityRegistryService.register_capability(
            org_id=org_id,
            capability_key=key,
            name=name,
            phase_introduced=phase,
            category=data.get('category', 'platform'),
            description=data.get('description', ''),
            owner_module=data.get('owner_module', ''),
            service_reference=data.get('service_reference', ''),
            route_prefix=data.get('route_prefix', ''),
            maturity_score=data.get('maturity_score', 50.0)
        )
        return jsonify(cap), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@mission_control_bp.route('/api/v1/mission-control/capabilities/<int:cap_id>', methods=['GET'])
@jwt_required
def api_get_capability_details(cap_id):
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    cap = PlatformCapability.query.filter_by(id=cap_id, organization_id=org_id).first()
    if not cap:
        return jsonify({'error': 'Capability not found'}), 404
    return jsonify(cap.to_dict()), 200


@mission_control_bp.route('/api/v1/mission-control/dependencies', methods=['GET'])
@jwt_required
def api_get_dependencies():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    graph = CapabilityRegistryService.build_dependency_map(org_id)
    return jsonify(graph), 200


@mission_control_bp.route('/api/v1/mission-control/dependencies', methods=['POST'])
@jwt_required
def api_add_dependency():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    src = data.get('source_capability_id')
    tgt = data.get('target_capability_id')
    if not org_id or not src or not tgt:
        return jsonify({'error': 'Missing required fields'}), 400
    val = CapabilityRegistryService.validate_dependency(org_id, src, tgt)
    if not val['valid']:
        return jsonify({'error': val['errors'][0]}), 400
    try:
        dep = CapabilityDependency(
            source_capability_id=src,
            target_capability_id=tgt,
            dependency_type=data.get('dependency_type', 'service_call'),
            criticality=data.get('criticality', 'medium'),
            coupling_score=data.get('coupling_score', 0.5),
            health_impact_score=data.get('health_impact_score', 0.5),
            status='active',
            organization_id=org_id,
        )
        db.session.add(dep)
        db.session.commit()
        return jsonify(dep.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@mission_control_bp.route('/api/v1/mission-control/architecture', methods=['GET'])
@jwt_required
def api_get_architecture():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    summary = ArchitectureConvergenceService.convergence_summary(org_id)
    return jsonify(summary), 200


@mission_control_bp.route('/api/v1/mission-control/certifications', methods=['GET'])
@jwt_required
def api_get_certifications():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    runs = PlatformCertificationRun.query.filter_by(organization_id=org_id).all()
    return jsonify([r.to_dict() for r in runs]), 200


@mission_control_bp.route('/api/v1/mission-control/certifications', methods=['POST'])
@jwt_required
def api_create_certification():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    name = data.get('name')
    cert_type = data.get('certification_type', 'full_platform')
    if not org_id or not name:
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        HookService.trigger_hook('before_platform_certification', org_id, None)
        run = PlatformCertificationService.create_run(org_id, name, cert_type)
        HookService.trigger_hook('after_platform_certification', org_id, run['id'], run['overall_score'])
        return jsonify(run), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@mission_control_bp.route('/api/v1/mission-control/certifications/<int:run_id>', methods=['GET'])
@jwt_required
def api_get_certification_details(run_id):
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    run = PlatformCertificationRun.query.filter_by(id=run_id, organization_id=org_id).first()
    if not run:
        return jsonify({'error': 'Certification run not found'}), 404
    return jsonify(run.to_dict()), 200


@mission_control_bp.route('/api/v1/mission-control/certifications/<int:run_id>/checks', methods=['GET'])
@jwt_required
def api_get_certification_checks(run_id):
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    checks = CertificationCheck.query.filter_by(certification_run_id=run_id, organization_id=org_id).all()
    return jsonify([c.to_dict() for c in checks]), 200


@mission_control_bp.route('/api/v1/mission-control/readiness', methods=['GET'])
@jwt_required
def api_get_readiness():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    metrics = PlatformReadinessMetric.query.filter_by(organization_id=org_id).order_by(
        PlatformReadinessMetric.measured_at.desc()
    ).all()
    return jsonify([m.to_dict() for m in metrics]), 200


@mission_control_bp.route('/api/v1/mission-control/readiness', methods=['POST'])
@jwt_required
def api_evaluate_readiness():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    metric_type = data.get('metric_type', 'on_demand')
    notes = data.get('notes', '')
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    try:
        HookService.trigger_hook('before_readiness_evaluation', org_id, metric_type)
        metric = PlatformReadinessService.save_metric(org_id, metric_type, notes)
        HookService.trigger_hook('after_readiness_evaluation', org_id, metric['id'], metric['overall_readiness_score'])
        return jsonify(metric), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@mission_control_bp.route('/api/v1/mission-control/baselines', methods=['GET'])
@jwt_required
def api_get_baselines():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    baselines = ReleaseBaseline.query.filter_by(organization_id=org_id).all()
    return jsonify([b.to_dict() for b in baselines]), 200


@mission_control_bp.route('/api/v1/mission-control/baselines', methods=['POST'])
@jwt_required
def api_create_baseline():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    version = data.get('version')
    metrics = data.get('metrics')
    if not org_id or not version or not metrics:
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        HookService.trigger_hook('before_release_baseline', org_id, version, metrics)
        bl = ReleaseBaselineService.create_baseline(org_id, version, metrics, data.get('codename', ''), data.get('notes', ''))
        HookService.trigger_hook('after_release_baseline', org_id, version, bl['id'])
        return jsonify(bl), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@mission_control_bp.route('/api/v1/mission-control/baselines/<int:baseline_id>', methods=['GET'])
@jwt_required
def api_get_baseline_details(baseline_id):
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    bl = ReleaseBaseline.query.filter_by(id=baseline_id, organization_id=org_id).first()
    if not bl:
        return jsonify({'error': 'Baseline not found'}), 404
    return jsonify(bl.to_dict()), 200


@mission_control_bp.route('/api/v1/mission-control/baselines/<int:baseline_id>/approve', methods=['POST'])
@jwt_required
def api_approve_baseline(baseline_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    approved_by = data.get('approved_by')
    if not org_id or not approved_by:
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        bl = ReleaseBaselineService.approve_baseline(org_id, baseline_id, approved_by)
        return jsonify(bl), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@mission_control_bp.route('/api/v1/mission-control/release-gates', methods=['GET'])
@jwt_required
def api_get_release_gates():
    org_id = request.args.get('org_id', type=int)
    baseline_id = request.args.get('baseline_id', type=int)
    if not org_id or not baseline_id:
        return jsonify({'error': 'org_id and baseline_id required'}), 400
    gates = ReleaseGateDecision.query.filter_by(
        release_baseline_id=baseline_id, organization_id=org_id
    ).all()
    return jsonify([g.to_dict() for g in gates]), 200


@mission_control_bp.route('/api/v1/mission-control/release-gates/evaluate', methods=['POST'])
@jwt_required
def api_evaluate_release_gates():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    baseline_id = data.get('release_baseline_id')
    gate_type = data.get('gate_type')
    if not org_id or not baseline_id or not gate_type:
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        HookService.trigger_hook('before_release_gate_decision', org_id, baseline_id, gate_type)
        if gate_type == 'test_gate':
            gate = ReleaseGateService.evaluate_test_gate(org_id, baseline_id)
        elif gate_type == 'security_gate':
            gate = ReleaseGateService.evaluate_security_gate(org_id, baseline_id)
        elif gate_type == 'tenant_isolation_gate':
            gate = ReleaseGateService.evaluate_tenant_gate(org_id, baseline_id)
        elif gate_type == 'ai_safety_gate':
            gate = ReleaseGateService.evaluate_ai_safety_gate(org_id, baseline_id)
        elif gate_type == 'migration_gate':
            gate = ReleaseGateService.evaluate_migration_gate(org_id, baseline_id)
        elif gate_type == 'documentation_gate':
            gate = ReleaseGateService.evaluate_documentation_gate(org_id, baseline_id)
        else:
            return jsonify({'error': f"Unknown gate_type: {gate_type}"}), 400
        HookService.trigger_hook('after_release_gate_decision', org_id, baseline_id, gate['id'], gate['decision'])
        return jsonify(gate), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@mission_control_bp.route('/api/v1/mission-control/release-gates/<int:gate_id>/approve', methods=['POST'])
@jwt_required
def api_approve_release_gate(gate_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    approved_by = data.get('approved_by')
    if not org_id or not approved_by:
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        gate = ReleaseGateService.approve_release(org_id, gate_id, approved_by)
        return jsonify(gate), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@mission_control_bp.route('/api/v1/mission-control/decisions', methods=['GET'])
@jwt_required
def api_get_decisions():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    recs = ArchitectureDecisionRecord.query.filter_by(organization_id=org_id).all()
    return jsonify([r.to_dict() for r in recs]), 200


@mission_control_bp.route('/api/v1/mission-control/decisions', methods=['POST'])
@jwt_required
def api_create_decision():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    key = data.get('adr_key')
    title = data.get('title')
    decision = data.get('decision')
    if not org_id or not key or not title or not decision:
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        rec = ArchitectureDecisionService.create_decision(
            org_id=org_id,
            adr_key=key,
            title=title,
            decision=decision,
            context=data.get('context', ''),
            consequences=data.get('consequences', ''),
            alternatives=data.get('alternatives', []),
            affected_modules=data.get('affected_modules', []),
        )
        return jsonify(rec), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@mission_control_bp.route('/api/v1/mission-control/brief', methods=['GET'])
@jwt_required
def api_get_brief():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    try:
        brief = ExecutivePlatformAI.generate_final_platform_brief(org_id)
        return jsonify({'brief': brief}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN routes (Require @require_admin)
# ─────────────────────────────────────────────────────────────────────────────

@mission_control_bp.route('/admin/mission-control', methods=['GET'])
@require_admin
def admin_overview():
    return render_template('admin_mission_control.html')


@mission_control_bp.route('/admin/mission-control/capabilities', methods=['GET'])
@require_admin
def admin_capability_registry():
    return render_template('admin_capability_registry.html')


@mission_control_bp.route('/admin/mission-control/architecture', methods=['GET'])
@require_admin
def admin_architecture_convergence():
    return render_template('admin_architecture_convergence.html')


@mission_control_bp.route('/admin/mission-control/certification', methods=['GET'])
@require_admin
def admin_platform_certification():
    return render_template('admin_platform_certification.html')


@mission_control_bp.route('/admin/mission-control/readiness', methods=['GET'])
@require_admin
def admin_platform_readiness():
    return render_template('admin_platform_readiness.html')


@mission_control_bp.route('/admin/mission-control/releases', methods=['GET'])
@require_admin
def admin_release_baselines():
    return render_template('admin_release_baselines.html')


@mission_control_bp.route('/admin/mission-control/decisions', methods=['GET'])
@require_admin
def admin_architecture_decisions():
    return render_template('admin_architecture_decisions.html')
