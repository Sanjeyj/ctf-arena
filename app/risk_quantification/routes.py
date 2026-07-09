"""
Risk Quantification Blueprint Routes - Phase 36 Cyber Risk Quantification.
"""
import base64
import hmac
import hashlib
import json
import datetime
from functools import wraps
from flask import request, jsonify, render_template, current_app

from app.risk_quantification import risk_quantification_bp
from app.extensions import db
from app.utils.decorators import require_admin

# Models
from app.models.quantitative_risk_scenario import QuantitativeRiskScenario
from app.models.risk_frequency_estimate import RiskFrequencyEstimate
from app.models.loss_magnitude_estimate import LossMagnitudeEstimate
from app.models.risk_simulation_run import RiskSimulationRun
from app.models.risk_treatment_option import RiskTreatmentOption
from app.models.security_investment import SecurityInvestment
from app.models.risk_appetite_profile import RiskAppetiteProfile
from app.models.risk_portfolio_metric import RiskPortfolioMetric

# Services
from app.services.risk_scenario_service import RiskScenarioService
from app.services.frequency_model_service import FrequencyModelService
from app.services.loss_model_service import LossModelService
from app.services.risk_simulation_service import RiskSimulationService
from app.services.risk_treatment_service import RiskTreatmentService
from app.services.security_investment_service import SecurityInvestmentService
from app.services.risk_portfolio_service import RiskPortfolioService
from app.services.executive_risk_ai import ExecutiveRiskAI


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

@risk_quantification_bp.route('/api/v1/risk-quantification/scenarios', methods=['GET'])
@jwt_required
def api_get_scenarios():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    scenarios = QuantitativeRiskScenario.query.filter_by(organization_id=org_id).all()
    return jsonify([s.to_dict() for s in scenarios]), 200


@risk_quantification_bp.route('/api/v1/risk-quantification/scenarios', methods=['POST'])
@jwt_required
def api_create_scenario():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    name = data.get('name')
    description = data.get('description')
    scenario_type = data.get('scenario_type')
    asset_ref_type = data.get('asset_reference_type')
    asset_ref_id = data.get('asset_reference_id')
    business_process_id = data.get('business_process_id')
    threat_category = data.get('threat_category')

    if not org_id or not name or not scenario_type:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        scenario = RiskScenarioService.create_scenario(
            name=name,
            description=description,
            scenario_type=scenario_type,
            asset_ref_type=asset_ref_type,
            asset_ref_id=asset_ref_id,
            business_process_id=business_process_id,
            threat_category=threat_category,
            org_id=org_id
        )
        return jsonify(scenario.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@risk_quantification_bp.route('/api/v1/risk-quantification/scenarios/<int:scenario_id>', methods=['GET'])
@jwt_required
def api_get_scenario_details(scenario_id):
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    scenario = QuantitativeRiskScenario.query.filter_by(id=scenario_id, organization_id=org_id).first()
    if not scenario:
        return jsonify({'error': 'Scenario not found'}), 404
    return jsonify(scenario.to_dict()), 200


@risk_quantification_bp.route('/api/v1/risk-quantification/scenarios/<int:scenario_id>/simulate', methods=['POST'])
@jwt_required
def api_simulate_scenario(scenario_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    scenario = QuantitativeRiskScenario.query.filter_by(id=scenario_id, organization_id=org_id).first()
    if not scenario:
        return jsonify({'error': 'Scenario not found'}), 404

    sim_type = data.get('simulation_type', 'monte_carlo_simulation')
    iterations = data.get('iteration_count', 1000)
    seed = data.get('random_seed', 42)

    try:
        run = RiskSimulationService.create_run(
            scenario_id=scenario.id,
            simulation_type=sim_type,
            iteration_count=iterations,
            random_seed=seed,
            org_id=org_id
        )
        if sim_type == 'monte_carlo_simulation':
            run = RiskSimulationService.simulate_monte_carlo(run.id, org_id)
        else:
            run = RiskSimulationService.simulate_deterministic(run.id, org_id)

        # Trigger scenario score updates
        RiskScenarioService.calculate_inherent_risk(scenario.id, org_id)

        return jsonify(run.to_dict()), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@risk_quantification_bp.route('/api/v1/risk-quantification/simulations/<int:run_id>', methods=['GET'])
@jwt_required
def api_get_simulation(run_id):
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    run = RiskSimulationRun.query.filter_by(id=run_id, organization_id=org_id).first()
    if not run:
        return jsonify({'error': 'Simulation run not found'}), 404
    return jsonify(run.to_dict()), 200


@risk_quantification_bp.route('/api/v1/risk-quantification/treatments', methods=['GET'])
@jwt_required
def api_get_treatments():
    org_id = request.args.get('org_id', type=int)
    scenario_id = request.args.get('scenario_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    query = RiskTreatmentOption.query.filter_by(organization_id=org_id)
    if scenario_id:
        query = query.filter_by(scenario_id=scenario_id)

    options = query.all()
    return jsonify([o.to_dict() for o in options]), 200


@risk_quantification_bp.route('/api/v1/risk-quantification/treatments', methods=['POST'])
@jwt_required
def api_create_treatment():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    scenario_id = data.get('scenario_id')
    treatment_type = data.get('treatment_type')
    title = data.get('title')
    description = data.get('description')
    cost = data.get('estimated_cost', 0.0)
    reduction = data.get('expected_risk_reduction', 0.0)
    complexity = data.get('implementation_complexity', 'medium')

    if not org_id or not scenario_id or not treatment_type or not title:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        option = RiskTreatmentService.create_option(
            scenario_id=scenario_id,
            treatment_type=treatment_type,
            title=title,
            description=description,
            estimated_cost=cost,
            expected_risk_reduction=reduction,
            implementation_complexity=complexity,
            org_id=org_id
        )
        return jsonify(option.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@risk_quantification_bp.route('/api/v1/risk-quantification/treatments/<int:option_id>/approve', methods=['POST'])
@jwt_required
def api_approve_treatment(option_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    option = RiskTreatmentService.approve_treatment(option_id, org_id)
    if not option:
        return jsonify({'error': 'Treatment option not found'}), 404
    return jsonify(option.to_dict()), 200


@risk_quantification_bp.route('/api/v1/risk-quantification/investments', methods=['GET'])
@jwt_required
def api_get_investments():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    investments = SecurityInvestment.query.filter_by(organization_id=org_id).all()
    return jsonify([i.to_dict() for i in investments]), 200


@risk_quantification_bp.route('/api/v1/risk-quantification/investments', methods=['POST'])
@jwt_required
def api_create_investment():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    title = data.get('title')
    category = data.get('investment_category')
    cost = data.get('cost', 0.0)
    operating_cost = data.get('annual_operating_cost', 0.0)
    loss_reduction = data.get('expected_loss_reduction', 0.0)
    risk_reduction = data.get('expected_risk_reduction', 0.0)

    if not org_id or not title or not category:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        investment = SecurityInvestmentService.create_investment(
            title=title,
            investment_category=category,
            cost=cost,
            operating_cost=operating_cost,
            loss_reduction=loss_reduction,
            risk_reduction=risk_reduction,
            org_id=org_id
        )
        return jsonify(investment.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@risk_quantification_bp.route('/api/v1/risk-quantification/portfolio', methods=['GET'])
@jwt_required
def api_get_portfolio():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    summary = RiskPortfolioService.portfolio_summary(org_id)
    return jsonify(summary), 200


@risk_quantification_bp.route('/api/v1/risk-quantification/brief', methods=['GET'])
@jwt_required
def api_get_brief():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    brief = ExecutiveRiskAI.generate_quantitative_risk_brief(org_id)
    return jsonify({'brief': brief}), 200


# ─────────────────────────────────────────────────────────────────────────────
# Admin Views
# ─────────────────────────────────────────────────────────────────────────────

@risk_quantification_bp.route('/admin/risk-quantification', methods=['GET'])
@require_admin
def admin_dashboard():
    org_id = request.args.get('org_id', type=int)
    from app.services.admin_service import AdminService
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_risk_quantification.html',
        stats=stats,
        challenges=challenges,
        current_org_id=org_id
    )


@risk_quantification_bp.route('/admin/risk-quantification/scenarios', methods=['GET'])
@require_admin
def admin_scenarios():
    org_id = request.args.get('org_id', type=int)
    from app.services.admin_service import AdminService
    scenarios = QuantitativeRiskScenario.query.all() if not org_id else QuantitativeRiskScenario.query.filter_by(organization_id=org_id).all()
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_risk_scenarios.html',
        scenarios=scenarios,
        stats=stats,
        challenges=challenges,
        current_org_id=org_id
    )


@risk_quantification_bp.route('/admin/risk-quantification/simulations', methods=['GET'])
@require_admin
def admin_simulations():
    org_id = request.args.get('org_id', type=int)
    from app.services.admin_service import AdminService
    runs = RiskSimulationRun.query.all() if not org_id else RiskSimulationRun.query.filter_by(organization_id=org_id).all()
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_risk_simulations.html',
        runs=runs,
        stats=stats,
        challenges=challenges,
        current_org_id=org_id
    )


@risk_quantification_bp.route('/admin/risk-quantification/treatments', methods=['GET'])
@require_admin
def admin_treatments():
    org_id = request.args.get('org_id', type=int)
    from app.services.admin_service import AdminService
    options = RiskTreatmentOption.query.all() if not org_id else RiskTreatmentOption.query.filter_by(organization_id=org_id).all()
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_risk_treatments.html',
        options=options,
        stats=stats,
        challenges=challenges,
        current_org_id=org_id
    )


@risk_quantification_bp.route('/admin/risk-quantification/investments', methods=['GET'])
@require_admin
def admin_investments():
    org_id = request.args.get('org_id', type=int)
    from app.services.admin_service import AdminService
    investments = SecurityInvestment.query.all() if not org_id else SecurityInvestment.query.filter_by(organization_id=org_id).all()
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_security_investments.html',
        investments=investments,
        stats=stats,
        challenges=challenges,
        current_org_id=org_id
    )


@risk_quantification_bp.route('/admin/risk-quantification/portfolio', methods=['GET'])
@require_admin
def admin_portfolio():
    org_id = request.args.get('org_id', type=int)
    from app.services.admin_service import AdminService
    metrics = RiskPortfolioMetric.query.all() if not org_id else RiskPortfolioMetric.query.filter_by(organization_id=org_id).all()
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_risk_portfolio.html',
        metrics=metrics,
        stats=stats,
        challenges=challenges,
        current_org_id=org_id
    )


@risk_quantification_bp.route('/admin/risk-quantification/brief', methods=['GET'])
@require_admin
def admin_brief():
    org_id = request.args.get('org_id', type=int)
    from app.services.admin_service import AdminService
    brief_text = ExecutiveRiskAI.generate_quantitative_risk_brief(org_id or 1)
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_executive_brief.html',
        brief=brief_text,
        stats=stats,
        challenges=challenges,
        current_org_id=org_id
    )
