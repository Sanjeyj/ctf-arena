"""
Assurance REST API and Admin Routes - Phase 32 Cyber Trust, Assurance & Verification Fabric.
Enforces multi-tenant isolation, JWT authentication, and policy enforcement.
"""
import base64
import hmac
import hashlib
import json
from functools import wraps
from flask import request, jsonify, render_template, current_app

from app.assurance import assurance_bp
from app.extensions import db
from app.utils.decorators import require_admin

# Models
from app.models.trust_identity import TrustIdentity
from app.models.device_posture import DevicePosture
from app.models.trust_decision import TrustDecision
from app.models.assurance_case import AssuranceCase
from app.models.assurance_evidence_link import AssuranceEvidenceLink
from app.models.software_attestation import SoftwareAttestation
from app.models.sbom_record import SBOMRecord
from app.models.control_validation import ControlValidation

# Services
from app.services.identity_trust_service import IdentityTrustService
from app.services.device_posture_service import DevicePostureService
from app.services.zero_trust_decision_service import ZeroTrustDecisionService
from app.services.assurance_service import AssuranceService
from app.services.attestation_service import AttestationService
from app.services.sbom_service import SBOMService
from app.services.control_validation_service import ControlValidationService
from app.services.executive_assurance_ai import ExecutiveAssuranceAI


# ─────────────────────────────────────────────────────────────────────────────
# JWT Crypto Helpers (Same as Control Plane)
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

@assurance_bp.route('/api/v1/assurance/identities', methods=['GET'])
@jwt_required
def api_get_identities():
    """GET /api/v1/assurance/identities — list registered identities."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    identities = TrustIdentity.query.filter_by(organization_id=org_id).all()
    return jsonify([i.to_dict() for i in identities]), 200


@assurance_bp.route('/api/v1/assurance/identities', methods=['POST'])
@jwt_required
def api_register_identity():
    """POST /api/v1/assurance/identities — register identity."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    data = request.get_json() or {}
    user_id = data.get('user_id')
    itype = data.get('identity_type')
    if not user_id or not itype:
        return jsonify({'error': 'user_id and identity_type are required'}), 400

    ident = IdentityTrustService.register_identity(
        user_id=user_id,
        identity_type=itype,
        org_id=org_id,
        authentication_strength=data.get('authentication_strength', 1.0),
        risk_score=data.get('risk_score', 0.0)
    )
    return jsonify(ident.to_dict()), 201


@assurance_bp.route('/api/v1/assurance/identities/<int:identity_id>/verify', methods=['POST'])
@jwt_required
def api_verify_identity(identity_id):
    """POST /api/v1/assurance/identities/<id>/verify — verify identity."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    ident = IdentityTrustService.verify(identity_id, org_id)
    if not ident:
        return jsonify({'error': 'Identity not found'}), 404
    return jsonify(ident.to_dict()), 200


@assurance_bp.route('/api/v1/assurance/devices', methods=['GET'])
@jwt_required
def api_get_devices():
    """GET /api/v1/assurance/devices — list registered devices."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    devices = DevicePosture.query.filter_by(organization_id=org_id).all()
    return jsonify([d.to_dict() for d in devices]), 200


@assurance_bp.route('/api/v1/assurance/devices', methods=['POST'])
@jwt_required
def api_register_device():
    """POST /api/v1/assurance/devices — register device posture."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    data = request.get_json() or {}
    name = data.get('device_name')
    dtype = data.get('device_type')
    os_fam = data.get('os_family')
    if not name or not dtype or not os_fam:
        return jsonify({'error': 'device_name, device_type, and os_family are required'}), 400

    device = DevicePostureService.register_device(
        device_name=name,
        device_type=dtype,
        os_family=os_fam,
        org_id=org_id,
        patch_score=data.get('patch_score', 1.0),
        encryption_enabled=data.get('encryption_enabled', True),
        endpoint_protection_status=data.get('endpoint_protection_status', 'active')
    )
    return jsonify(device.to_dict()), 201


@assurance_bp.route('/api/v1/assurance/trust/evaluate', methods=['POST'])
@jwt_required
def api_evaluate_trust():
    """POST /api/v1/assurance/trust/evaluate — evaluate Zero Trust authorization decision."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    data = request.get_json() or {}
    identity_id = data.get('identity_id')
    device_id = data.get('device_id')
    res_type = data.get('resource_type')
    res_id = data.get('resource_id')
    action = data.get('requested_action')
    if not identity_id or not device_id or not res_type or not res_id or not action:
        return jsonify({'error': 'identity_id, device_id, resource_type, resource_id, and requested_action are required'}), 400

    decision = ZeroTrustDecisionService.evaluate(
        identity_id=identity_id,
        device_id=device_id,
        resource_type=res_type,
        resource_id=res_id,
        requested_action=action,
        org_id=org_id,
        context=data.get('context')
    )
    if not decision:
        return jsonify({'error': 'Identity or device not found'}), 404
    return jsonify(decision.to_dict()), 200


@assurance_bp.route('/api/v1/assurance/trust/decisions', methods=['GET'])
@jwt_required
def api_get_decisions():
    """GET /api/v1/assurance/trust/decisions — list ZT decisions ledger."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    decisions = ZeroTrustDecisionService.decision_history(org_id)
    return jsonify([d.to_dict() for d in decisions]), 200


@assurance_bp.route('/api/v1/assurance/cases', methods=['GET'])
@jwt_required
def api_get_cases():
    """GET /api/v1/assurance/cases — list assurance cases claims."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    cases = AssuranceCase.query.filter_by(organization_id=org_id).all()
    return jsonify([c.to_dict() for c in cases]), 200


@assurance_bp.route('/api/v1/assurance/cases', methods=['POST'])
@jwt_required
def api_create_case():
    """POST /api/v1/assurance/cases — create assurance case claim."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    data = request.get_json() or {}
    title = data.get('title')
    claim = data.get('claim')
    if not title or not claim:
        return jsonify({'error': 'title and claim are required'}), 400

    case = AssuranceService.create_case(
        title=title,
        claim=claim,
        org_id=org_id,
        scope=data.get('scope'),
        owner=data.get('owner')
    )
    return jsonify(case.to_dict()), 201


@assurance_bp.route('/api/v1/assurance/cases/<int:case_id>/evidence', methods=['POST'])
@jwt_required
def api_attach_evidence(case_id):
    """POST /api/v1/assurance/cases/<id>/evidence — attach evidence record."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    data = request.get_json() or {}
    evidence_id = data.get('evidence_record_id')
    rel_type = data.get('relationship_type', 'supports')
    weight = data.get('weight', 1.0)
    if not evidence_id:
        return jsonify({'error': 'evidence_record_id required'}), 400

    link = AssuranceService.attach_evidence(case_id, evidence_id, rel_type, weight, org_id)
    if not link:
        return jsonify({'error': 'Assurance case or Evidence record not found'}), 404
    return jsonify(link.to_dict()), 201


@assurance_bp.route('/api/v1/assurance/cases/<int:case_id>/evaluate', methods=['POST'])
@jwt_required
def api_evaluate_case(case_id):
    """POST /api/v1/assurance/cases/<id>/evaluate — evaluate case confidence score."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    case = db.session.get(AssuranceCase, case_id)
    if not case or case.organization_id != org_id:
        return jsonify({'error': 'Assurance case not found'}), 404

    confidence = AssuranceService.evaluate_case(case_id, org_id)
    return jsonify({'confidence_score': confidence, 'status': case.status}), 200


@assurance_bp.route('/api/v1/assurance/attestations', methods=['GET'])
@jwt_required
def api_get_attestations():
    """GET /api/v1/assurance/attestations — list attestations."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    atts = SoftwareAttestation.query.filter_by(organization_id=org_id).all()
    return jsonify([a.to_dict() for a in atts]), 200


@assurance_bp.route('/api/v1/assurance/attestations', methods=['POST'])
@jwt_required
def api_register_attestation():
    """POST /api/v1/assurance/attestations — register attestation."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    data = request.get_json() or {}
    name = data.get('artifact_name')
    ver = data.get('artifact_version')
    digest = data.get('artifact_digest')
    if not name or not ver or not digest:
        return jsonify({'error': 'artifact_name, artifact_version, and artifact_digest are required'}), 400

    att = AttestationService.register_attestation(
        artifact_name=name,
        artifact_version=ver,
        artifact_digest=digest,
        org_id=org_id,
        builder_identity=data.get('builder_identity'),
        build_environment=data.get('build_environment'),
        metadata=data.get('metadata')
    )
    return jsonify(att.to_dict()), 201


@assurance_bp.route('/api/v1/assurance/sbom', methods=['GET'])
@jwt_required
def api_get_sbom():
    """GET /api/v1/assurance/sbom — list sboms."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    records = SBOMRecord.query.filter_by(organization_id=org_id).all()
    return jsonify([r.to_dict() for r in records]), 200


@assurance_bp.route('/api/v1/assurance/sbom', methods=['POST'])
@jwt_required
def api_register_sbom():
    """POST /api/v1/assurance/sbom — register sbom document."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    data = request.get_json() or {}
    name = data.get('artifact_name')
    ver = data.get('artifact_version')
    ftype = data.get('format_type', 'CycloneDX')
    doc_hash = data.get('document_hash')
    if not name or not ver or not doc_hash:
        return jsonify({'error': 'artifact_name, artifact_version, and document_hash are required'}), 400

    sbom = SBOMService.register(
        artifact_name=name,
        artifact_version=ver,
        format_type=ftype,
        document_hash=doc_hash,
        org_id=org_id,
        metadata=data.get('metadata')
    )
    return jsonify(sbom.to_dict()), 201


@assurance_bp.route('/api/v1/assurance/controls', methods=['GET'])
@jwt_required
def api_get_controls():
    """GET /api/v1/assurance/controls — list validation runs."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    validations = ControlValidation.query.filter_by(organization_id=org_id).all()
    return jsonify([v.to_dict() for v in validations]), 200


@assurance_bp.route('/api/v1/assurance/controls/validate', methods=['POST'])
@jwt_required
def api_validate_control():
    """POST /api/v1/assurance/controls/validate — run control validation check."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    data = request.get_json() or {}
    ref = data.get('control_reference')
    vtype = data.get('validation_type')
    expected = data.get('expected_result')
    actual = data.get('actual_result')
    score = data.get('effectiveness_score')
    if not ref or not vtype or not expected or not actual or score is None:
        return jsonify({'error': 'control_reference, validation_type, expected_result, actual_result, and effectiveness_score are required'}), 400

    val = ControlValidationService.validate_control(
        control_reference=ref,
        validation_type=vtype,
        expected_result=expected,
        actual_result=actual,
        effectiveness_score=score,
        org_id=org_id,
        evidence_id=data.get('evidence_record_id')
    )
    return jsonify(val.to_dict()), 201


@assurance_bp.route('/api/v1/assurance/brief', methods=['GET'])
@jwt_required
def api_get_brief():
    """GET /api/v1/assurance/brief — retrieve AI executive brief summaries."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    brief = ExecutiveAssuranceAI.generate_assurance_brief(org_id)
    summary = ExecutiveAssuranceAI.summarize_trust_posture(org_id)
    rec = ExecutiveAssuranceAI.recommend_evidence_priorities(org_id)
    return jsonify({
        'brief': brief,
        'summary': summary,
        'recommendations': rec
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# Admin Dashboard Routes
# ─────────────────────────────────────────────────────────────────────────────

@assurance_bp.route('/admin/assurance', methods=['GET'])
@require_admin
def admin_assurance():
    """Admin: Overview unified assurance posture dashboard."""
    identities = TrustIdentity.query.all()
    devices = DevicePosture.query.all()
    cases = AssuranceCase.query.all()
    return render_template('admin_assurance.html', identities=identities, devices=devices, cases=cases)


@assurance_bp.route('/admin/assurance/identities', methods=['GET'])
@require_admin
def admin_identity_trust():
    """Admin: Identity trust scores workspace."""
    identities = TrustIdentity.query.all()
    return render_template('admin_identity_trust.html', identities=identities)


@assurance_bp.route('/admin/assurance/devices', methods=['GET'])
@require_admin
def admin_device_posture():
    """Admin: Device compliance and simulated posture dashboard."""
    devices = DevicePosture.query.all()
    return render_template('admin_device_posture.html', devices=devices)


@assurance_bp.route('/admin/assurance/trust', methods=['GET'])
@require_admin
def admin_trust_decisions():
    """Admin: Zero Trust decision ledger workspace."""
    decisions = TrustDecision.query.all()
    return render_template('admin_trust_decisions.html', decisions=decisions)


@assurance_bp.route('/admin/assurance/cases', methods=['GET'])
@require_admin
def admin_assurance_cases():
    """Admin: Claims, linked evidence, and confidence metrics."""
    cases = AssuranceCase.query.all()
    return render_template('admin_assurance_cases.html', cases=cases)


@assurance_bp.route('/admin/assurance/supply-chain', methods=['GET'])
@require_admin
def admin_supply_chain_assurance():
    """Admin: Attestations and SBOM catalog metadata."""
    attestations = SoftwareAttestation.query.all()
    sboms = SBOMRecord.query.all()
    return render_template('admin_supply_chain_assurance.html', attestations=attestations, sboms=sboms)


@assurance_bp.route('/admin/assurance/controls', methods=['GET'])
@require_admin
def admin_control_validation():
    """Admin: Control effectiveness tracking dashboard."""
    validations = ControlValidation.query.all()
    return render_template('admin_control_validation.html', validations=validations)
