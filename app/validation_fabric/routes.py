"""
Validation Fabric REST API and Admin Routes - Phase 35 Continuous Security Validation & Defense Effectiveness Fabric.
"""
import base64
import hmac
import hashlib
import json
import datetime
from functools import wraps
from flask import request, jsonify, render_template, current_app

from app.validation_fabric import validation_fabric_bp
from app.extensions import db
from app.utils.decorators import require_admin

# Models
from app.models.validation_campaign import ValidationCampaign
from app.models.validation_scenario import ValidationScenario
from app.models.validation_execution import ValidationExecution
from app.models.validation_check import ValidationCheck
from app.models.detection_validation import DetectionValidation
from app.models.playbook_readiness import PlaybookReadiness
from app.models.defense_effectiveness_metric import DefenseEffectivenessMetric
from app.models.validation_regression import ValidationRegression
from app.models.remediation_plan import RemediationPlan

# Services
from app.services.validation_campaign_service import ValidationCampaignService
from app.services.validation_engine_service import ValidationEngineService
from app.services.detection_validation_service import DetectionValidationService
from app.services.playbook_validation_service import PlaybookValidationService
from app.services.defense_effectiveness_service import DefenseEffectivenessService
from app.services.validation_regression_service import ValidationRegressionService
from app.services.remediation_verification_service import RemediationVerificationService
from app.services.executive_validation_ai import ExecutiveValidationAI


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
# REST Endpoints - Validation Campaigns
# ─────────────────────────────────────────────────────────────────────────────

@validation_fabric_bp.route('/api/v1/validation-fabric/campaigns', methods=['GET'])
@jwt_required
def api_get_campaigns():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    campaigns = ValidationCampaign.query.filter_by(organization_id=org_id).all()
    return jsonify([c.to_dict() for c in campaigns]), 200


@validation_fabric_bp.route('/api/v1/validation-fabric/campaigns', methods=['POST'])
@jwt_required
def api_create_campaign():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    name = data.get('name')
    description = data.get('description')
    campaign_type = data.get('campaign_type')
    scope = data.get('scope')
    priority = data.get('priority', 'medium')
    scheduled_at_str = data.get('scheduled_at')

    if not org_id or not name or not campaign_type:
        return jsonify({'error': 'org_id, name, and campaign_type are required'}), 400

    scheduled_at = None
    if scheduled_at_str:
        try:
            scheduled_at = datetime.datetime.fromisoformat(scheduled_at_str.replace('Z', '+00:00'))
        except Exception:
            return jsonify({'error': 'Invalid scheduled_at date format. Use ISO format.'}), 400

    try:
        campaign = ValidationCampaignService.create_campaign(
            name, description, campaign_type, scope, priority, scheduled_at, org_id
        )
        return jsonify(campaign.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@validation_fabric_bp.route('/api/v1/validation-fabric/campaigns/<int:campaign_id>/scenarios', methods=['POST'])
@jwt_required
def api_add_scenario(campaign_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    name = data.get('name')
    scenario_type = data.get('scenario_type')
    description = data.get('description')
    severity = data.get('severity', 'medium')
    expected_outcome = data.get('expected_outcome')
    configuration_json = data.get('configuration_json', '{}')

    if not org_id or not name or not scenario_type or not expected_outcome:
        return jsonify({'error': 'org_id, name, scenario_type, and expected_outcome are required'}), 400

    scenario = ValidationCampaignService.add_scenario(
        campaign_id, name, scenario_type, description, severity, expected_outcome, configuration_json, org_id
    )
    if not scenario:
        return jsonify({'error': 'Campaign not found or access denied'}), 404

    return jsonify(scenario.to_dict()), 201


@validation_fabric_bp.route('/api/v1/validation-fabric/campaigns/<int:campaign_id>/schedule', methods=['POST'])
@jwt_required
def api_schedule_campaign(campaign_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    try:
        campaign = ValidationCampaignService.schedule_campaign(campaign_id, org_id)
        if not campaign:
            return jsonify({'error': 'Campaign not found or access denied'}), 404
        return jsonify(campaign.to_dict()), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@validation_fabric_bp.route('/api/v1/validation-fabric/campaigns/<int:campaign_id>/start', methods=['POST'])
@jwt_required
def api_start_campaign(campaign_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    try:
        campaign = ValidationCampaignService.start_campaign(campaign_id, org_id)
        if not campaign:
            return jsonify({'error': 'Campaign not found or access denied'}), 404
        return jsonify(campaign.to_dict()), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@validation_fabric_bp.route('/api/v1/validation-fabric/campaigns/<int:campaign_id>/complete', methods=['POST'])
@jwt_required
def api_complete_campaign(campaign_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    try:
        campaign = ValidationCampaignService.complete_campaign(campaign_id, org_id)
        if not campaign:
            return jsonify({'error': 'Campaign not found or access denied'}), 404
        return jsonify(campaign.to_dict()), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@validation_fabric_bp.route('/api/v1/validation-fabric/campaigns/<int:campaign_id>/cancel', methods=['POST'])
@jwt_required
def api_cancel_campaign(campaign_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    try:
        campaign = ValidationCampaignService.cancel_campaign(campaign_id, org_id)
        if not campaign:
            return jsonify({'error': 'Campaign not found or access denied'}), 404
        return jsonify(campaign.to_dict()), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@validation_fabric_bp.route('/api/v1/validation-fabric/campaigns/<int:campaign_id>/summary', methods=['GET'])
@jwt_required
def api_get_campaign_summary(campaign_id):
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    summary = ValidationCampaignService.campaign_summary(campaign_id, org_id)
    if not summary:
        return jsonify({'error': 'Campaign not found or access denied'}), 404
    return jsonify(summary), 200


# ─────────────────────────────────────────────────────────────────────────────
# REST Endpoints - Validation Engine / Execution
# ─────────────────────────────────────────────────────────────────────────────

@validation_fabric_bp.route('/api/v1/validation-fabric/scenarios/<int:scenario_id>/execute', methods=['POST'])
@jwt_required
def api_execute_scenario(scenario_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    exec_record = ValidationEngineService.execute_scenario(scenario_id, org_id)
    if not exec_record:
        return jsonify({'error': 'Scenario not found or access denied'}), 404
    return jsonify({
        'id': exec_record.id,
        'status': exec_record.status,
        'result_score': exec_record.result_score,
        'effectiveness_score': exec_record.effectiveness_score,
        'result_summary': exec_record.result_summary
    }), 201


@validation_fabric_bp.route('/api/v1/validation-fabric/executions/<int:execution_id>/summary', methods=['GET'])
@jwt_required
def api_get_execution_summary(execution_id):
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    summary = ValidationEngineService.execution_summary(execution_id, org_id)
    if not summary:
        return jsonify({'error': 'Execution not found or access denied'}), 404
    return jsonify(summary), 200


# ─────────────────────────────────────────────────────────────────────────────
# REST Endpoints - Detection Validation
# ─────────────────────────────────────────────────────────────────────────────

@validation_fabric_bp.route('/api/v1/validation-fabric/detection/signal', methods=['POST'])
@jwt_required
def api_create_synthetic_signal():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    execution_id = data.get('execution_id')
    detection_type = data.get('detection_type')
    detection_reference = data.get('detection_reference')
    synthetic_signal_type = data.get('synthetic_signal_type')
    expected_detection = data.get('expected_detection', True)

    if not org_id or not execution_id or not detection_type or not detection_reference:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        val = DetectionValidationService.create_synthetic_signal(
            execution_id, detection_type, detection_reference, synthetic_signal_type, expected_detection, org_id
        )
        return jsonify({
            'id': val.id,
            'detection_type': val.detection_type,
            'detection_reference': val.detection_reference,
            'synthetic_signal_type': val.synthetic_signal_type,
            'expected_detection': val.expected_detection,
            'detected': val.detected
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@validation_fabric_bp.route('/api/v1/validation-fabric/detection/evaluate', methods=['POST'])
@jwt_required
def api_evaluate_detection():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    validation_id = data.get('validation_id')
    detected = data.get('detected', True)
    latency_score = data.get('latency_score', 1.0)

    if not org_id or not validation_id:
        return jsonify({'error': 'org_id and validation_id are required'}), 400

    val = DetectionValidationService.evaluate_detection(validation_id, detected, latency_score, org_id)
    if not val:
        return jsonify({'error': 'Detection validation record not found'}), 404

    return jsonify({
        'id': val.id,
        'detected': val.detected,
        'latency_score': val.latency_score,
        'coverage_score': val.coverage_score
    }), 200


@validation_fabric_bp.route('/api/v1/validation-fabric/detection/gaps', methods=['GET'])
@jwt_required
def api_get_detection_gaps():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    gaps = DetectionValidationService.find_detection_gaps(org_id)
    return jsonify(gaps), 200


@validation_fabric_bp.route('/api/v1/validation-fabric/detection/summary', methods=['GET'])
@jwt_required
def api_get_detection_summary():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    summary = DetectionValidationService.detection_summary(org_id)
    return jsonify(summary), 200


# ─────────────────────────────────────────────────────────────────────────────
# REST Endpoints - Playbook Readiness
# ─────────────────────────────────────────────────────────────────────────────

@validation_fabric_bp.route('/api/v1/validation-fabric/playbooks/<int:playbook_id>/evaluate', methods=['POST'])
@jwt_required
def api_evaluate_playbook(playbook_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    execution_id = data.get('execution_id')

    if not org_id or not execution_id:
        return jsonify({'error': 'org_id and execution_id are required'}), 400

    record = PlaybookValidationService.calculate_readiness(playbook_id, execution_id, org_id)
    return jsonify({
        'id': record.id,
        'playbook_id': record.playbook_id,
        'readiness_score': record.readiness_score,
        'status': record.status
    }), 201


@validation_fabric_bp.route('/api/v1/validation-fabric/playbooks/summary', methods=['GET'])
@jwt_required
def api_get_playbook_summary():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    summary = PlaybookValidationService.playbook_summary(org_id)
    return jsonify(summary), 200


# ─────────────────────────────────────────────────────────────────────────────
# REST Endpoints - Defense Effectiveness
# ─────────────────────────────────────────────────────────────────────────────

@validation_fabric_bp.route('/api/v1/validation-fabric/effectiveness', methods=['GET'])
@jwt_required
def api_get_effectiveness():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    summary = DefenseEffectivenessService.effectiveness_summary(org_id)
    trend = DefenseEffectivenessService.effectiveness_trend(org_id)
    return jsonify({
        'summary': summary,
        'trend': trend
    }), 200


@validation_fabric_bp.route('/api/v1/validation-fabric/effectiveness', methods=['POST'])
@jwt_required
def api_calculate_effectiveness():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    metric = DefenseEffectivenessService.calculate_composite_score(org_id)
    return jsonify({
        'id': metric.id,
        'score': metric.score,
        'previous_score': metric.previous_score,
        'delta': metric.delta,
        'trend': metric.trend
    }), 201


# ─────────────────────────────────────────────────────────────────────────────
# REST Endpoints - Regressions
# ─────────────────────────────────────────────────────────────────────────────

@validation_fabric_bp.route('/api/v1/validation-fabric/regressions', methods=['GET'])
@jwt_required
def api_get_regressions():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    regs = ValidationRegression.query.filter_by(organization_id=org_id).all()
    return jsonify([
        {
            'id': r.id,
            'resource_type': r.resource_type,
            'resource_id': r.resource_id,
            'metric_type': r.metric_type,
            'previous_score': r.previous_score,
            'current_score': r.current_score,
            'regression_delta': r.regression_delta,
            'severity': r.severity,
            'status': r.status,
            'detected_at': r.detected_at.isoformat() if r.detected_at else None
        } for r in regs
    ]), 200


@validation_fabric_bp.route('/api/v1/validation-fabric/regressions/<int:regression_id>/resolve', methods=['POST'])
@jwt_required
def api_resolve_regression(regression_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    reg = ValidationRegressionService.resolve_regression(regression_id, org_id)
    if not reg:
        return jsonify({'error': 'Regression not found or access denied'}), 404
    return jsonify({
        'id': reg.id,
        'status': reg.status
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# REST Endpoints - Remediation Verification
# ─────────────────────────────────────────────────────────────────────────────

@validation_fabric_bp.route('/api/v1/validation-fabric/remediation/verify', methods=['POST'])
@jwt_required
def api_verify_remediation():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    plan_id = data.get('plan_id')
    if not org_id or not plan_id:
        return jsonify({'error': 'org_id and plan_id are required'}), 400

    plan = RemediationVerificationService.select_plan(plan_id, org_id)
    if not plan:
        return jsonify({'error': 'Remediation plan not found'}), 404

    scenario = RemediationVerificationService.create_verification_scenario(plan_id, org_id)
    exec_record = ValidationEngineService.execute_scenario(scenario.id, org_id)
    improvement = RemediationVerificationService.evaluate_remediation(exec_record.id, org_id)

    return jsonify({
        'scenario_id': scenario.id,
        'execution_id': exec_record.id,
        'remediation_plan_id': plan_id,
        'improvement_score': improvement,
        'status': 'verified'
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# REST Endpoints - AI Brief
# ─────────────────────────────────────────────────────────────────────────────

@validation_fabric_bp.route('/api/v1/validation-fabric/brief', methods=['GET'])
@jwt_required
def api_get_brief():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    brief = ExecutiveValidationAI.generate_defense_effectiveness_brief(org_id)
    posture = ExecutiveValidationAI.summarize_validation_posture(org_id)
    priorities = ExecutiveValidationAI.recommend_validation_priorities(org_id)
    gaps = ExecutiveValidationAI.summarize_detection_gaps(org_id)
    regressions = ExecutiveValidationAI.explain_regressions(org_id)

    return jsonify({
        'brief': brief,
        'posture': posture,
        'priorities': priorities,
        'gaps': gaps,
        'regressions': regressions
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# Admin Dashboard Routes
# ─────────────────────────────────────────────────────────────────────────────

@validation_fabric_bp.route('/admin/validation-fabric', methods=['GET'])
@require_admin
def admin_validation():
    campaigns = ValidationCampaign.query.all()
    scenarios = ValidationScenario.query.all()
    executions = ValidationExecution.query.all()
    metrics = DefenseEffectivenessMetric.query.order_by(DefenseEffectivenessMetric.id.desc()).limit(10).all()
    regressions = ValidationRegression.query.all()
    return render_template(
        'admin_validation_fabric.html',
        campaigns=campaigns,
        scenarios=scenarios,
        executions=executions,
        metrics=metrics,
        regressions=regressions
    )


@validation_fabric_bp.route('/admin/validation-fabric/campaigns', methods=['GET'])
@require_admin
def admin_campaigns():
    campaigns = ValidationCampaign.query.all()
    return render_template('admin_validation_campaigns.html', campaigns=campaigns)


@validation_fabric_bp.route('/admin/validation-fabric/scenarios', methods=['GET'])
@require_admin
def admin_scenarios():
    scenarios = ValidationScenario.query.all()
    return render_template('admin_validation_scenarios.html', scenarios=scenarios)


@validation_fabric_bp.route('/admin/validation-fabric/executions', methods=['GET'])
@require_admin
def admin_executions():
    executions = ValidationExecution.query.all()
    return render_template('admin_validation_executions.html', executions=executions)


@validation_fabric_bp.route('/admin/validation-fabric/detections', methods=['GET'])
@require_admin
def admin_detections():
    validations = DetectionValidation.query.all()
    return render_template('admin_validation_detections.html', validations=validations)


@validation_fabric_bp.route('/admin/validation-fabric/readiness', methods=['GET'])
@require_admin
def admin_readiness():
    records = PlaybookReadiness.query.all()
    return render_template('admin_validation_readiness.html', records=records)


@validation_fabric_bp.route('/admin/validation-fabric/effectiveness', methods=['GET'])
@require_admin
def admin_effectiveness():
    metrics = DefenseEffectivenessMetric.query.order_by(DefenseEffectivenessMetric.id.desc()).all()
    return render_template('admin_validation_effectiveness.html', metrics=metrics)
