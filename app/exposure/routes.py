"""
Exposure REST API and Admin Routes - Phase 34 Security Architecture, Exposure & Attack Surface Management Fabric.
"""
import base64
import hmac
import hashlib
import json
from functools import wraps
from flask import request, jsonify, render_template, current_app

from app.exposure import exposure_bp
from app.extensions import db
from app.utils.decorators import require_admin

# Models
from app.models.architecture_zone import ArchitectureZone
from app.models.trust_boundary import TrustBoundary
from app.models.exposure_asset import ExposureAsset
from app.models.exposure_finding import ExposureFinding
from app.models.attack_path import AttackPath
from app.models.control_coverage_map import ControlCoverageMap
from app.models.remediation_plan import RemediationPlan
from app.models.architecture_review import ArchitectureReview

# Services
from app.services.architecture_service import ArchitectureService
from app.services.exposure_inventory_service import ExposureInventoryService
from app.services.finding_service import FindingService
from app.services.attack_path_service import AttackPathService
from app.services.control_coverage_service import ControlCoverageService
from app.services.remediation_prioritization_service import RemediationPrioritizationService
from app.services.architecture_review_service import ArchitectureReviewService
from app.services.executive_exposure_ai import ExecutiveExposureAI


# ─────────────────────────────────────────────────────────────────────────────
# JWT Crypto Helpers
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

@exposure_bp.route('/api/v1/exposure-fabric/zones', methods=['GET'])
@jwt_required
def api_get_zones():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    zones = ArchitectureZone.query.filter_by(organization_id=org_id).all()
    return jsonify([
        {
            "id": z.id,
            "name": z.name,
            "zone_type": z.zone_type,
            "description": z.description,
            "trust_level": z.trust_level,
            "criticality": z.criticality,
            "status": z.status
        } for z in zones
    ]), 200


@exposure_bp.route('/api/v1/exposure-fabric/zones', methods=['POST'])
@jwt_required
def api_create_zone():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    name = data.get('name')
    zone_type = data.get('zone_type', 'application')
    description = data.get('description')
    trust_level = data.get('trust_level', 1.0)
    criticality = data.get('criticality', 'medium')

    if not org_id or not name:
        return jsonify({'error': 'org_id and name required'}), 400

    z = ArchitectureService.create_zone(name, zone_type, description, trust_level, criticality, org_id)
    return jsonify({
        "id": z.id,
        "name": z.name,
        "zone_type": z.zone_type
    }), 201


@exposure_bp.route('/api/v1/exposure-fabric/boundaries', methods=['GET'])
@jwt_required
def api_get_boundaries():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    boundaries = TrustBoundary.query.filter_by(organization_id=org_id).all()
    return jsonify([
        {
            "id": b.id,
            "name": b.name,
            "source_zone_id": b.source_zone_id,
            "target_zone_id": b.target_zone_id,
            "boundary_type": b.boundary_type,
            "required_trust_score": b.required_trust_score,
            "control_requirements_json": b.control_requirements_json,
            "status": b.status
        } for b in boundaries
    ]), 200


@exposure_bp.route('/api/v1/exposure-fabric/boundaries', methods=['POST'])
@jwt_required
def api_create_boundary():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    name = data.get('name')
    source_zone_id = data.get('source_zone_id')
    target_zone_id = data.get('target_zone_id')
    boundary_type = data.get('boundary_type', 'network')
    required_trust_score = data.get('required_trust_score', 0.5)
    control_requirements_json = data.get('control_requirements_json', '[]')

    if not org_id or not name or not source_zone_id or not target_zone_id:
        return jsonify({'error': 'Missing required fields'}), 400

    # IDOR check
    z1 = ArchitectureZone.query.filter_by(id=source_zone_id, organization_id=org_id).first()
    z2 = ArchitectureZone.query.filter_by(id=target_zone_id, organization_id=org_id).first()
    if not z1 or not z2:
        return jsonify({'error': 'Source/Target zone not found or access denied'}), 404

    b = ArchitectureService.create_boundary(name, source_zone_id, target_zone_id, boundary_type, required_trust_score, control_requirements_json, org_id)
    return jsonify({
        "id": b.id,
        "name": b.name,
        "status": b.status
    }), 201


@exposure_bp.route('/api/v1/exposure-fabric/boundaries/<int:boundary_id>/validate', methods=['POST'])
@jwt_required
def api_validate_boundary(boundary_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    boundary = TrustBoundary.query.filter_by(id=boundary_id, organization_id=org_id).first()
    if not boundary:
        return jsonify({'error': 'Boundary not found or access denied'}), 404

    res = ArchitectureService.validate_boundary(boundary_id, org_id)
    return jsonify(res), 200


@exposure_bp.route('/api/v1/exposure-fabric/assets', methods=['GET'])
@jwt_required
def api_get_assets():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    assets = ExposureInventoryService.list_exposed_assets(org_id)
    return jsonify(assets), 200


@exposure_bp.route('/api/v1/exposure-fabric/assets', methods=['POST'])
@jwt_required
def api_create_asset():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    asset_reference_type = data.get('asset_reference_type')
    asset_reference_id = data.get('asset_reference_id')
    display_name = data.get('display_name')
    exposure_type = data.get('exposure_type', 'internal')
    internet_exposed = data.get('internet_exposed', False)
    criticality = data.get('criticality', 'medium')
    business_impact_score = data.get('business_impact_score', 5.0)
    architecture_zone_id = data.get('architecture_zone_id')

    if not org_id or not asset_reference_type or not asset_reference_id or not display_name:
        return jsonify({'error': 'Missing required fields'}), 400

    # IDOR check for zone
    if architecture_zone_id:
        zone = ArchitectureZone.query.filter_by(id=architecture_zone_id, organization_id=org_id).first()
        if not zone:
            return jsonify({'error': 'Architecture zone not found or access denied'}), 404

    asset = ExposureInventoryService.register_projection(
        asset_reference_type, asset_reference_id, display_name, exposure_type,
        internet_exposed, criticality, business_impact_score, architecture_zone_id, org_id
    )
    return jsonify({
        "id": asset.id,
        "display_name": asset.display_name,
        "status": asset.status
    }), 201


@exposure_bp.route('/api/v1/exposure-fabric/findings', methods=['GET'])
@jwt_required
def api_get_findings():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    findings = ExposureFinding.query.filter_by(organization_id=org_id).all()
    return jsonify([
        {
            "id": f.id,
            "exposure_asset_id": f.exposure_asset_id,
            "finding_type": f.finding_type,
            "title": f.title,
            "severity": f.severity,
            "likelihood": f.likelihood,
            "impact_score": f.impact_score,
            "confidence": f.confidence,
            "status": f.status,
            "source_type": f.source_type
        } for f in findings
    ]), 200


@exposure_bp.route('/api/v1/exposure-fabric/findings', methods=['POST'])
@jwt_required
def api_create_finding():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    exposure_asset_id = data.get('exposure_asset_id')
    finding_type = data.get('finding_type')
    title = data.get('title')
    severity = data.get('severity', 'medium')
    likelihood = data.get('likelihood', 0.5)
    impact_score = data.get('impact_score', 5.0)
    confidence = data.get('confidence', 1.0)
    status = data.get('status', 'open')
    source_type = data.get('source_type', 'simulation')
    metadata_json = data.get('metadata_json', '{}')

    if not org_id or not exposure_asset_id or not finding_type or not title:
        return jsonify({'error': 'Missing required fields'}), 400

    # IDOR check
    asset = ExposureAsset.query.filter_by(id=exposure_asset_id, organization_id=org_id).first()
    if not asset:
        return jsonify({'error': 'Exposure asset not found or access denied'}), 404

    try:
        f = FindingService.create_finding(
            exposure_asset_id, finding_type, title, severity, likelihood,
            impact_score, confidence, status, source_type, metadata_json, org_id
        )
    except ValueError as ex:
        return jsonify({'error': str(ex)}), 400

    return jsonify({
        "id": f.id,
        "title": f.title,
        "status": f.status
    }), 201


@exposure_bp.route('/api/v1/exposure-fabric/paths/critical', methods=['POST'])
@jwt_required
def api_find_critical_path():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    source_asset_id = data.get('source_asset_id')
    target_asset_id = data.get('target_asset_id')

    if not org_id or not source_asset_id or not target_asset_id:
        return jsonify({'error': 'Missing required fields'}), 400

    # IDOR check
    a1 = ExposureAsset.query.filter_by(id=source_asset_id, organization_id=org_id).first()
    a2 = ExposureAsset.query.filter_by(id=target_asset_id, organization_id=org_id).first()
    if not a1 or not a2:
        return jsonify({'error': 'Source/Target asset not found or access denied'}), 404

    ap = AttackPathService.find_critical_path(source_asset_id, target_asset_id, org_id)
    if not ap:
        return jsonify({'error': 'No path found'}), 404

    return jsonify({
        "id": ap.id,
        "name": ap.name,
        "path": json.loads(ap.path_json),
        "hop_count": ap.hop_count,
        "path_risk_score": ap.path_risk_score
    }), 200


@exposure_bp.route('/api/v1/exposure-fabric/coverage', methods=['GET'])
@jwt_required
def api_get_coverage_summary():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    summary = ControlCoverageService.coverage_summary(org_id)
    return jsonify(summary), 200


@exposure_bp.route('/api/v1/exposure-fabric/remediation', methods=['GET'])
@jwt_required
def api_get_remediation():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    plans = RemediationPlan.query.filter_by(organization_id=org_id).all()
    return jsonify([
        {
            "id": p.id,
            "title": p.title,
            "finding_id": p.finding_id,
            "priority_score": p.priority_score,
            "recommended_action": p.recommended_action,
            "approval_status": p.approval_status,
            "status": p.status
        } for p in plans
    ]), 200


@exposure_bp.route('/api/v1/exposure-fabric/remediation', methods=['POST'])
@jwt_required
def api_create_remediation():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    title = data.get('title')
    finding_id = data.get('finding_id')
    recommended_action = data.get('recommended_action')

    if not org_id or not title or not finding_id:
        return jsonify({'error': 'Missing required fields'}), 400

    # IDOR check
    finding = ExposureFinding.query.filter_by(id=finding_id, organization_id=org_id).first()
    if not finding:
        return jsonify({'error': 'Finding not found or access denied'}), 404

    p = RemediationPrioritizationService.create_plan(title, finding_id, recommended_action, None, org_id)
    return jsonify({
        "id": p.id,
        "title": p.title,
        "priority_score": p.priority_score,
        "status": p.status
    }), 201


@exposure_bp.route('/api/v1/exposure-fabric/remediation/<int:plan_id>/approve', methods=['POST'])
@jwt_required
def api_approve_remediation(plan_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    plan = RemediationPlan.query.filter_by(id=plan_id, organization_id=org_id).first()
    if not plan:
        return jsonify({'error': 'Remediation plan not found or access denied'}), 404

    p = RemediationPrioritizationService.approve_plan(plan_id, org_id)
    return jsonify({
        "id": p.id,
        "approval_status": p.approval_status
    }), 200


@exposure_bp.route('/api/v1/exposure-fabric/reviews', methods=['GET'])
@jwt_required
def api_get_reviews():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    reviews = ArchitectureReview.query.filter_by(organization_id=org_id).all()
    return jsonify([
        {
            "id": r.id,
            "title": r.title,
            "scope": r.scope,
            "review_type": r.review_type,
            "risk_score": r.risk_score,
            "findings_count": r.findings_count,
            "decision": r.decision,
            "reviewer": r.reviewer,
            "status": r.status
        } for r in reviews
    ]), 200


@exposure_bp.route('/api/v1/exposure-fabric/reviews', methods=['POST'])
@jwt_required
def api_create_review():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    title = data.get('title')
    scope = data.get('scope')
    review_type = data.get('review_type', 'annual')
    reviewer = data.get('reviewer')
    summary = data.get('summary')

    if not org_id or not title or not scope or not reviewer:
        return jsonify({'error': 'Missing required fields'}), 400

    r = ArchitectureReviewService.create_review(title, scope, review_type, reviewer, summary, org_id)
    return jsonify({
        "id": r.id,
        "title": r.title,
        "status": r.status
    }), 201


@exposure_bp.route('/api/v1/exposure-fabric/reviews/<int:review_id>/findings', methods=['POST'])
@jwt_required
def api_attach_review_findings(review_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    finding_ids = data.get('finding_ids', [])

    if not org_id or not finding_ids:
        return jsonify({'error': 'Missing required fields'}), 400

    # IDOR check
    review = ArchitectureReview.query.filter_by(id=review_id, organization_id=org_id).first()
    if not review:
        return jsonify({'error': 'Review not found or access denied'}), 404

    r = ArchitectureReviewService.attach_findings(review_id, finding_ids, org_id)
    return jsonify({
        "id": r.id,
        "findings_count": r.findings_count,
        "risk_score": r.risk_score
    }), 200


@exposure_bp.route('/api/v1/exposure-fabric/brief', methods=['GET'])
@jwt_required
def api_get_brief():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    brief = ExecutiveExposureAI.generate_exposure_brief(org_id)
    summary = ExecutiveExposureAI.summarize_attack_surface(org_id)
    rec = ExecutiveExposureAI.recommend_remediation_priorities(org_id)

    return jsonify({
        'brief': brief,
        'summary': summary,
        'recommendations': rec
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# Admin Dashboard Routes
# ─────────────────────────────────────────────────────────────────────────────

@exposure_bp.route('/admin/exposure-fabric', methods=['GET'])
@require_admin
def admin_exposure():
    zones = ArchitectureZone.query.all()
    boundaries = TrustBoundary.query.all()
    assets = ExposureAsset.query.all()
    findings = ExposureFinding.query.all()
    return render_template('admin_exposure_fabric.html', zones=zones, boundaries=boundaries, assets=assets, findings=findings)


@exposure_bp.route('/admin/exposure-fabric/zones', methods=['GET'])
@require_admin
def admin_zones():
    zones = ArchitectureZone.query.all()
    return render_template('admin_exposure_zones.html', zones=zones)


@exposure_bp.route('/admin/exposure-fabric/boundaries', methods=['GET'])
@require_admin
def admin_boundaries():
    boundaries = TrustBoundary.query.all()
    return render_template('admin_exposure_boundaries.html', boundaries=boundaries)


@exposure_bp.route('/admin/exposure-fabric/inventory', methods=['GET'])
@require_admin
def admin_inventory():
    assets = ExposureAsset.query.all()
    return render_template('admin_exposure_inventory.html', assets=assets)


@exposure_bp.route('/admin/exposure-fabric/findings', methods=['GET'])
@require_admin
def admin_findings():
    findings = ExposureFinding.query.all()
    return render_template('admin_exposure_findings.html', findings=findings)


@exposure_bp.route('/admin/exposure-fabric/paths', methods=['GET'])
@require_admin
def admin_paths():
    paths = AttackPath.query.all()
    return render_template('admin_exposure_paths.html', paths=paths)


@exposure_bp.route('/admin/exposure-fabric/remediation', methods=['GET'])
@require_admin
def admin_remediation():
    plans = RemediationPlan.query.all()
    return render_template('admin_exposure_remediation.html', plans=plans)
