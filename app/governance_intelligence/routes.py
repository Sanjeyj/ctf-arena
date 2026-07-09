import base64
import hmac
import hashlib
import json
import datetime
from functools import wraps
from flask import request, jsonify, render_template, current_app

from app.governance_intelligence import governance_intelligence_bp
from app.extensions import db
from app.utils.decorators import require_admin

# Models
from app.models.decision_context import DecisionContext
from app.models.decision_recommendation import DecisionRecommendation
from app.models.policy_optimization_run import PolicyOptimizationRun
from app.models.policy_conflict import PolicyConflict
from app.models.governance_objective import GovernanceObjective
from app.models.governance_scorecard import GovernanceScorecard
from app.models.decision_outcome import DecisionOutcome
from app.models.governance_drift_record import GovernanceDriftRecord
from app.models.control_policy import ControlPolicy

# Services
from app.services.decision_intelligence_service import DecisionIntelligenceService
from app.services.policy_optimization_service import PolicyOptimizationService
from app.services.policy_conflict_service import PolicyConflictService
from app.services.governance_objective_service import GovernanceObjectiveService
from app.services.governance_scorecard_service import GovernanceScorecardService
from app.services.decision_outcome_service import DecisionOutcomeService
from app.services.governance_drift_service import GovernanceDriftService
from app.services.executive_governance_ai import ExecutiveGovernanceAI
from app.services.hook_service import HookService


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

@governance_intelligence_bp.route('/api/v1/governance-intelligence/contexts', methods=['GET'])
@jwt_required
def api_get_contexts():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    contexts = DecisionContext.query.filter_by(organization_id=org_id).all()
    return jsonify([c.to_dict() for c in contexts]), 200


@governance_intelligence_bp.route('/api/v1/governance-intelligence/contexts', methods=['POST'])
@jwt_required
def api_create_context():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    name = data.get('name')
    context_type = data.get('context_type')
    business_scope = data.get('business_scope')

    if not org_id or not name or not context_type:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        ctx = DecisionIntelligenceService.create_context(name, context_type, business_scope, org_id)
        return jsonify(ctx.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@governance_intelligence_bp.route('/api/v1/governance-intelligence/contexts/<int:context_id>', methods=['GET'])
@jwt_required
def api_get_context_details(context_id):
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    ctx = DecisionContext.query.filter_by(id=context_id, organization_id=org_id).first()
    if not ctx:
        return jsonify({'error': 'Context not found'}), 404
    return jsonify(ctx.to_dict()), 200


@governance_intelligence_bp.route('/api/v1/governance-intelligence/recommendations', methods=['GET'])
@jwt_required
def api_get_recommendations():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    recs = DecisionRecommendation.query.filter_by(organization_id=org_id).all()
    return jsonify([r.to_dict() for r in recs]), 200


@governance_intelligence_bp.route('/api/v1/governance-intelligence/contexts/<int:context_id>/recommend', methods=['POST'])
@jwt_required
def api_create_recommendation(context_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    rec_type = data.get('recommendation_type')
    title = data.get('title')
    description = data.get('description')
    risk_red = data.get('expected_risk_reduction', 0.0)
    res_gain = data.get('expected_resilience_gain', 0.0)
    ctrl_imp = data.get('expected_control_improvement', 0.0)
    cost = data.get('estimated_cost', 0.0)
    confidence = data.get('confidence_score', 0.0)

    if not org_id or not rec_type or not title:
        return jsonify({'error': 'Missing required fields'}), 400

    # Hook dispatch
    HookService.trigger_hook('before_decision_recommendation', context_id=context_id, org_id=org_id)

    try:
        rec = DecisionIntelligenceService.generate_recommendation(
            context_id, rec_type, title, description, risk_red, res_gain, ctrl_imp, cost, confidence, org_id
        )
        HookService.trigger_hook('after_decision_recommendation', recommendation_id=rec.id, org_id=org_id)
        return jsonify(rec.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@governance_intelligence_bp.route('/api/v1/governance-intelligence/policy-optimizations', methods=['GET'])
@jwt_required
def api_get_policy_optimizations():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    runs = PolicyOptimizationRun.query.filter_by(organization_id=org_id).all()
    return jsonify([r.to_dict() for r in runs]), 200


@governance_intelligence_bp.route('/api/v1/governance-intelligence/policies/<int:policy_id>/optimize', methods=['POST'])
@jwt_required
def api_optimize_policy(policy_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    opt_type = data.get('optimization_type', 'threshold_tuning')
    seed = data.get('random_seed', 42)

    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    try:
        run = PolicyOptimizationService.create_run(policy_id, opt_type, seed, org_id)
        HookService.trigger_hook('before_policy_optimization', run_id=run.id, org_id=org_id)

        PolicyOptimizationService.simulate_adjustment(run.id, org_id)

        HookService.trigger_hook('after_policy_optimization', run_id=run.id, org_id=org_id)
        return jsonify(run.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@governance_intelligence_bp.route('/api/v1/governance-intelligence/conflicts', methods=['GET'])
@jwt_required
def api_get_conflicts():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    # Auto-detect conflicts on retrieval for dynamic state
    PolicyConflictService.detect_conflicts(org_id)
    conflicts = PolicyConflict.query.filter_by(organization_id=org_id).all()
    return jsonify([c.to_dict() for c in conflicts]), 200


@governance_intelligence_bp.route('/api/v1/governance-intelligence/conflicts/<int:conflict_id>/resolve', methods=['POST'])
@jwt_required
def api_resolve_conflict(conflict_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    status = data.get('status', 'resolved')

    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    try:
        resolved = PolicyConflictService.resolve_conflict(conflict_id, status, org_id)
        if not resolved:
            return jsonify({'error': 'Conflict not found'}), 404
        return jsonify(resolved.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@governance_intelligence_bp.route('/api/v1/governance-intelligence/objectives', methods=['GET'])
@jwt_required
def api_get_objectives():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    objs = GovernanceObjective.query.filter_by(organization_id=org_id).all()
    return jsonify([o.to_dict() for o in objs]), 200


@governance_intelligence_bp.route('/api/v1/governance-intelligence/objectives', methods=['POST'])
@jwt_required
def api_create_objective():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    title = data.get('title')
    obj_type = data.get('objective_type')
    description = data.get('description')
    target_score = data.get('target_score', 80.0)
    weight = data.get('weight', 0.2)
    deadline = data.get('deadline')
    owner = data.get('owner')

    if not org_id or not title or not obj_type:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        obj = GovernanceObjectiveService.create_objective(
            title, obj_type, description, target_score, weight, deadline, owner, org_id
        )
        return jsonify(obj.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@governance_intelligence_bp.route('/api/v1/governance-intelligence/scorecards', methods=['GET'])
@jwt_required
def api_get_scorecards():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    scorecards = GovernanceScorecard.query.filter_by(organization_id=org_id).all()
    return jsonify([s.to_dict() for s in scorecards]), 200


@governance_intelligence_bp.route('/api/v1/governance-intelligence/scorecards/calculate', methods=['POST'])
@jwt_required
def api_calculate_scorecard():
    data = request.get_json() or {}
    org_id = data.get('org_id')

    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    HookService.trigger_hook('before_governance_scoring', org_id=org_id)
    try:
        sc = GovernanceScorecardService.save_scorecard(org_id)
        HookService.trigger_hook('after_governance_scoring', scorecard_id=sc.id, org_id=org_id)
        return jsonify(sc.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@governance_intelligence_bp.route('/api/v1/governance-intelligence/outcomes', methods=['GET'])
@jwt_required
def api_get_outcomes():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    outcomes = DecisionOutcome.query.filter_by(organization_id=org_id).all()
    return jsonify([o.to_dict() for o in outcomes]), 200


@governance_intelligence_bp.route('/api/v1/governance-intelligence/drift', methods=['GET'])
@jwt_required
def api_get_drift():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    HookService.trigger_hook('before_governance_drift_detection', org_id=org_id)
    # Detect drift dynamically
    GovernanceDriftService.detect_drift(org_id)
    records = GovernanceDriftRecord.query.filter_by(organization_id=org_id).all()
    HookService.trigger_hook('after_governance_drift_detection', org_id=org_id)
    return jsonify([r.to_dict() for r in records]), 200


@governance_intelligence_bp.route('/api/v1/governance-intelligence/brief', methods=['GET'])
@jwt_required
def api_get_brief():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    brief = ExecutiveGovernanceAI.generate_governance_brief(org_id)
    return jsonify({'brief': brief}), 200


# ─────────────────────────────────────────────────────────────────────────────
# Admin Dashboards (7 views)
# ─────────────────────────────────────────────────────────────────────────────

@governance_intelligence_bp.route('/admin/governance-intelligence', methods=['GET'])
@require_admin
def admin_governance():
    org_id = request.args.get('org_id', default=1, type=int)
    summary = GovernanceScorecardService.scorecard_summary(org_id)
    drift = GovernanceDriftService.drift_summary(org_id)
    return render_template(
        'admin_governance_intelligence.html',
        org_id=org_id,
        summary=summary,
        drift=drift
    )


@governance_intelligence_bp.route('/admin/governance-intelligence/decisions', methods=['GET'])
@require_admin
def admin_decisions():
    org_id = request.args.get('org_id', default=1, type=int)
    contexts = DecisionContext.query.filter_by(organization_id=org_id).all()
    return render_template(
        'admin_decision_intelligence.html',
        org_id=org_id,
        contexts=contexts
    )


@governance_intelligence_bp.route('/admin/governance-intelligence/policies', methods=['GET'])
@require_admin
def admin_policies():
    org_id = request.args.get('org_id', default=1, type=int)
    runs = PolicyOptimizationRun.query.filter_by(organization_id=org_id).all()
    return render_template(
        'admin_policy_optimization.html',
        org_id=org_id,
        runs=runs
    )


@governance_intelligence_bp.route('/admin/governance-intelligence/conflicts', methods=['GET'])
@require_admin
def admin_conflicts():
    org_id = request.args.get('org_id', default=1, type=int)
    conflicts = PolicyConflict.query.filter_by(organization_id=org_id).all()
    return render_template(
        'admin_policy_conflicts.html',
        org_id=org_id,
        conflicts=conflicts
    )


@governance_intelligence_bp.route('/admin/governance-intelligence/objectives', methods=['GET'])
@require_admin
def admin_objectives():
    org_id = request.args.get('org_id', default=1, type=int)
    objectives = GovernanceObjective.query.filter_by(organization_id=org_id).all()
    return render_template(
        'admin_governance_objectives.html',
        org_id=org_id,
        objectives=objectives
    )


@governance_intelligence_bp.route('/admin/governance-intelligence/outcomes', methods=['GET'])
@require_admin
def admin_outcomes():
    org_id = request.args.get('org_id', default=1, type=int)
    outcomes = DecisionOutcome.query.filter_by(organization_id=org_id).all()
    return render_template(
        'admin_decision_outcomes.html',
        org_id=org_id,
        outcomes=outcomes
    )


@governance_intelligence_bp.route('/admin/governance-intelligence/drift', methods=['GET'])
@require_admin
def admin_drift():
    org_id = request.args.get('org_id', default=1, type=int)
    records = GovernanceDriftRecord.query.filter_by(organization_id=org_id).all()
    return render_template(
        'admin_governance_drift.html',
        org_id=org_id,
        records=records
    )
