"""
Strategic Resilience Blueprint Routes - Phase 37 Cyber Resilience Strategic Planning.
"""
import base64
import hmac
import hashlib
import json
import datetime
from functools import wraps
from flask import request, jsonify, render_template, current_app

from app.strategic_resilience import strategic_resilience_bp
from app.extensions import db
from app.utils.decorators import require_admin

# Models
from app.models.stress_test_scenario import StressTestScenario
from app.models.stress_test_run import StressTestRun
from app.models.resilience_investment_plan import ResilienceInvestmentPlan
from app.models.investment_plan_item import InvestmentPlanItem
from app.models.control_investment_option import ControlInvestmentOption
from app.models.business_dependency_risk import BusinessDependencyRisk
from app.models.strategic_decision_record import StrategicDecisionRecord
from app.models.resilience_portfolio_metric import ResiliencePortfolioMetric

# Services
from app.services.stress_testing_service import StressTestingService
from app.services.resilience_planning_service import ResiliencePlanningService
from app.services.portfolio_optimization_service import PortfolioOptimizationService
from app.services.dependency_risk_service import DependencyRiskService
from app.services.control_investment_service import ControlInvestmentService
from app.services.strategic_decision_service import StrategicDecisionService
from app.services.resilience_portfolio_service import ResiliencePortfolioService
from app.services.executive_strategy_ai import ExecutiveStrategyAI


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

@strategic_resilience_bp.route('/api/v1/strategic-resilience/stress-scenarios', methods=['GET'])
@jwt_required
def api_get_scenarios():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    scenarios = StressTestScenario.query.filter_by(organization_id=org_id).all()
    return jsonify([s.to_dict() for s in scenarios]), 200


@strategic_resilience_bp.route('/api/v1/strategic-resilience/stress-scenarios', methods=['POST'])
@jwt_required
def api_create_scenario():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    name = data.get('name')
    description = data.get('description')
    category = data.get('scenario_category')
    severity = data.get('severity', 'medium')
    duration = data.get('duration_hours', 24.0)
    domains = data.get('affected_domains', [])
    prob = data.get('probability', 0.1)
    mult = data.get('impact_multiplier', 1.0)

    if not org_id or not name or not category:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        scenario = StressTestingService.create_scenario(
            name=name,
            description=description,
            scenario_category=category,
            severity=severity,
            duration_hours=duration,
            affected_domains=domains,
            probability=prob,
            impact_multiplier=mult,
            org_id=org_id
        )
        return jsonify(scenario.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@strategic_resilience_bp.route('/api/v1/strategic-resilience/stress-scenarios/<int:scenario_id>', methods=['GET'])
@jwt_required
def api_get_scenario(scenario_id):
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    scenario = StressTestScenario.query.filter_by(id=scenario_id, organization_id=org_id).first()
    if not scenario:
        return jsonify({'error': 'Scenario not found'}), 404
    return jsonify(scenario.to_dict()), 200


@strategic_resilience_bp.route('/api/v1/strategic-resilience/stress-scenarios/<int:scenario_id>/simulate', methods=['POST'])
@jwt_required
def api_simulate_stress(scenario_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    scenario = StressTestScenario.query.filter_by(id=scenario_id, organization_id=org_id).first()
    if not scenario:
        return jsonify({'error': 'Scenario not found'}), 404

    iterations = data.get('iteration_count', 100)
    seed = data.get('random_seed', 42)

    try:
        run = StressTestingService.create_run(scenario.id, iterations, seed, org_id)
        run = StressTestingService.simulate_stress(run.id, org_id)
        return jsonify(run.to_dict()), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@strategic_resilience_bp.route('/api/v1/strategic-resilience/stress-runs/<int:run_id>', methods=['GET'])
@jwt_required
def api_get_run(run_id):
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    run = StressTestRun.query.filter_by(id=run_id, organization_id=org_id).first()
    if not run:
        return jsonify({'error': 'Run not found'}), 404
    return jsonify(run.to_dict()), 200


@strategic_resilience_bp.route('/api/v1/strategic-resilience/plans', methods=['GET'])
@jwt_required
def api_get_plans():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    plans = ResilienceInvestmentPlan.query.filter_by(organization_id=org_id).all()
    return jsonify([p.to_dict() for p in plans]), 200


@strategic_resilience_bp.route('/api/v1/strategic-resilience/plans', methods=['POST'])
@jwt_required
def api_create_plan():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    name = data.get('name')
    description = data.get('description')
    budget = data.get('budget_limit', 100000.0)
    horizon = data.get('planning_horizon_months', 12)
    target_reduction = data.get('target_risk_reduction', 0.0)
    target_resilience = data.get('target_resilience_score', 80.0)

    if not org_id or not name:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        plan = ResiliencePlanningService.create_plan(
            name=name,
            description=description,
            budget_limit=budget,
            horizon_months=horizon,
            target_reduction=target_reduction,
            target_resilience=target_resilience,
            org_id=org_id
        )
        return jsonify(plan.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@strategic_resilience_bp.route('/api/v1/strategic-resilience/plans/<int:plan_id>', methods=['GET'])
@jwt_required
def api_get_plan_details(plan_id):
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    plan = ResilienceInvestmentPlan.query.filter_by(id=plan_id, organization_id=org_id).first()
    if not plan:
        return jsonify({'error': 'Plan not found'}), 404
    return jsonify(plan.to_dict()), 200


@strategic_resilience_bp.route('/api/v1/strategic-resilience/plans/<int:plan_id>/optimize', methods=['POST'])
@jwt_required
def api_optimize_plan(plan_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    plan = ResilienceInvestmentPlan.query.filter_by(id=plan_id, organization_id=org_id).first()
    if not plan:
        return jsonify({'error': 'Plan not found'}), 404

    try:
        PortfolioOptimizationService.optimize_budget(plan.id, org_id)
        # Update metrics history
        ResiliencePortfolioService.save_metric(plan.id, org_id)
        return jsonify(plan.to_dict()), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@strategic_resilience_bp.route('/api/v1/strategic-resilience/plans/<int:plan_id>/approve', methods=['POST'])
@jwt_required
def api_approve_plan(plan_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    approved_by = data.get('approved_by', 'system_admin')
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    plan = ResiliencePlanningService.approve_plan(plan_id, approved_by, org_id)
    if not plan:
        return jsonify({'error': 'Plan not found'}), 404
    return jsonify(plan.to_dict()), 200


@strategic_resilience_bp.route('/api/v1/strategic-resilience/dependencies', methods=['GET'])
@jwt_required
def api_get_dependencies():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    deps = BusinessDependencyRisk.query.filter_by(organization_id=org_id).all()
    return jsonify([d.to_dict() for d in deps]), 200


@strategic_resilience_bp.route('/api/v1/strategic-resilience/control-options', methods=['GET'])
@jwt_required
def api_get_control_options():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    opts = ControlInvestmentOption.query.filter_by(organization_id=org_id).all()
    return jsonify([o.to_dict() for o in opts]), 200


@strategic_resilience_bp.route('/api/v1/strategic-resilience/decisions', methods=['GET'])
@jwt_required
def api_get_decisions():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    decisions = StrategicDecisionRecord.query.filter_by(organization_id=org_id).all()
    return jsonify([d.to_dict() for d in decisions]), 200


@strategic_resilience_bp.route('/api/v1/strategic-resilience/portfolio', methods=['GET'])
@jwt_required
def api_get_portfolio():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    summary = ResiliencePortfolioService.portfolio_summary(org_id)
    return jsonify(summary), 200


@strategic_resilience_bp.route('/api/v1/strategic-resilience/brief', methods=['GET'])
@jwt_required
def api_get_brief():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    brief = ExecutiveStrategyAI.generate_strategic_resilience_brief(org_id)
    return jsonify({'brief': brief}), 200


# ─────────────────────────────────────────────────────────────────────────────
# Admin Views
# ─────────────────────────────────────────────────────────────────────────────

@strategic_resilience_bp.route('/admin/strategic-resilience', methods=['GET'])
@require_admin
def admin_dashboard():
    org_id = request.args.get('org_id', type=int)
    from app.services.admin_service import AdminService
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_strategic_resilience.html',
        stats=stats,
        challenges=challenges,
        current_org_id=org_id
    )


@strategic_resilience_bp.route('/admin/strategic-resilience/stress-tests', methods=['GET'])
@require_admin
def admin_stress_tests():
    org_id = request.args.get('org_id', type=int)
    from app.services.admin_service import AdminService
    scenarios = StressTestScenario.query.all() if not org_id else StressTestScenario.query.filter_by(organization_id=org_id).all()
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_stress_tests.html',
        scenarios=scenarios,
        stats=stats,
        challenges=challenges,
        current_org_id=org_id
    )


@strategic_resilience_bp.route('/admin/strategic-resilience/investment-plans', methods=['GET'])
@require_admin
def admin_investment_plans():
    org_id = request.args.get('org_id', type=int)
    from app.services.admin_service import AdminService
    plans = ResilienceInvestmentPlan.query.all() if not org_id else ResilienceInvestmentPlan.query.filter_by(organization_id=org_id).all()
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_investment_plans.html',
        plans=plans,
        stats=stats,
        challenges=challenges,
        current_org_id=org_id
    )


@strategic_resilience_bp.route('/admin/strategic-resilience/optimization', methods=['GET'])
@require_admin
def admin_portfolio_optimization():
    org_id = request.args.get('org_id', type=int)
    from app.services.admin_service import AdminService
    plans = ResilienceInvestmentPlan.query.all() if not org_id else ResilienceInvestmentPlan.query.filter_by(organization_id=org_id).all()
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_portfolio_optimization.html',
        plans=plans,
        stats=stats,
        challenges=challenges,
        current_org_id=org_id
    )


@strategic_resilience_bp.route('/admin/strategic-resilience/dependencies', methods=['GET'])
@require_admin
def admin_dependency_risk():
    org_id = request.args.get('org_id', type=int)
    from app.services.admin_service import AdminService
    dependencies = BusinessDependencyRisk.query.all() if not org_id else BusinessDependencyRisk.query.filter_by(organization_id=org_id).all()
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_dependency_risk.html',
        dependencies=dependencies,
        stats=stats,
        challenges=challenges,
        current_org_id=org_id
    )


@strategic_resilience_bp.route('/admin/strategic-resilience/decisions', methods=['GET'])
@require_admin
def admin_strategic_decisions():
    org_id = request.args.get('org_id', type=int)
    from app.services.admin_service import AdminService
    decisions = StrategicDecisionRecord.query.all() if not org_id else StrategicDecisionRecord.query.filter_by(organization_id=org_id).all()
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_strategic_decisions.html',
        decisions=decisions,
        stats=stats,
        challenges=challenges,
        current_org_id=org_id
    )


@strategic_resilience_bp.route('/admin/strategic-resilience/portfolio', methods=['GET'])
@require_admin
def admin_resilience_portfolio():
    org_id = request.args.get('org_id', type=int)
    from app.services.admin_service import AdminService
    metrics = ResiliencePortfolioMetric.query.all() if not org_id else ResiliencePortfolioMetric.query.filter_by(organization_id=org_id).all()
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_resilience_portfolio.html',
        metrics=metrics,
        stats=stats,
        challenges=challenges,
        current_org_id=org_id
    )
