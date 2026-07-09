import base64
import hmac
import hashlib
import json
import datetime
from functools import wraps
from flask import request, jsonify, render_template, current_app

from app.systemic_resilience import systemic_resilience_bp
from app.extensions import db
from app.utils.decorators import require_admin

# Models
from app.models.systemic_risk_node import SystemicRiskNode
from app.models.systemic_dependency import SystemicDependency
from app.models.contagion_scenario import ContagionScenario
from app.models.contagion_simulation_run import ContagionSimulationRun
from app.models.contagion_event import ContagionEvent
from app.models.collective_resilience_plan import CollectiveResiliencePlan
from app.models.mutual_aid_simulation import MutualAidSimulation
from app.models.federation_governance_record import FederationGovernanceRecord

# Services
from app.services.systemic_risk_graph_service import SystemicRiskGraphService
from app.services.contagion_simulation_service import ContagionSimulationService
from app.services.systemic_stress_service import SystemicStressService
from app.services.collective_resilience_service import CollectiveResilienceService
from app.services.mutual_aid_simulation_service import MutualAidSimulationService
from app.services.federation_governance_service import FederationGovernanceService
from app.services.ecosystem_resilience_service import EcosystemResilienceService
from app.services.executive_systemic_risk_ai import ExecutiveSystemicRiskAI
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
# API Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@systemic_resilience_bp.route('/api/v1/systemic-resilience/nodes', methods=['GET'])
@jwt_required
def api_get_nodes():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    nodes = SystemicRiskNode.query.filter_by(organization_id=org_id).all()
    return jsonify([n.to_dict() for n in nodes]), 200


@systemic_resilience_bp.route('/api/v1/systemic-resilience/nodes', methods=['POST'])
@jwt_required
def api_create_node():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    name = data.get('name')
    node_type = data.get('node_type')
    if not org_id or not name or not node_type:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        node = SystemicRiskGraphService.register_projection(
            name=name,
            node_type=node_type,
            reference_type=data.get('reference_type'),
            reference_id=data.get('reference_id'),
            sector=data.get('sector'),
            region=data.get('region'),
            org_id=org_id,
            criticality_score=data.get('criticality_score', 50.0),
            dependency_score=data.get('dependency_score', 50.0),
            concentration_score=data.get('concentration_score', 50.0),
            resilience_score=data.get('resilience_score', 50.0)
        )
        return jsonify(node.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@systemic_resilience_bp.route('/api/v1/systemic-resilience/dependencies', methods=['GET'])
@jwt_required
def api_get_dependencies():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    deps = SystemicDependency.query.filter_by(organization_id=org_id).all()
    return jsonify([d.to_dict() for d in deps]), 200


@systemic_resilience_bp.route('/api/v1/systemic-resilience/dependencies', methods=['POST'])
@jwt_required
def api_create_dependency():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    source_id = data.get('source_node_id')
    target_id = data.get('target_node_id')
    dep_type = data.get('dependency_type')
    if not org_id or not source_id or not target_id or not dep_type:
        return jsonify({'error': 'Missing required fields'}), 400

    # IDOR / ownership verification
    valid, msg = SystemicRiskGraphService.validate_dependency(source_id, target_id, org_id)
    if not valid:
        return jsonify({'error': msg}), 400

    try:
        dep = SystemicRiskGraphService.add_dependency(
            source_node_id=source_id,
            target_node_id=target_id,
            dep_type=dep_type,
            strength=data.get('dependency_strength', 50.0),
            substitutability=data.get('substitutability_score', 50.0),
            recovery_dep=data.get('recovery_dependency_score', 50.0),
            propagation_prob=data.get('propagation_probability', 0.5),
            trust_dep=data.get('trust_dependency_score', 50.0),
            org_id=org_id
        )
        return jsonify(dep.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@systemic_resilience_bp.route('/api/v1/systemic-resilience/graph', methods=['GET'])
@jwt_required
def api_get_graph():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    # Dispatch hooks
    HookService.trigger_hook('before_systemic_risk_analysis', org_id=org_id)

    graph_data = SystemicRiskGraphService.build_graph(org_id)
    centrality = SystemicRiskGraphService.calculate_node_centrality(org_id)
    spofs = SystemicRiskGraphService.identify_single_points_of_failure(org_id)

    nodes_serialized = {}
    for node_id, data in graph_data.items():
        nodes_serialized[node_id] = {
            'node': data['node'].to_dict(),
            'centrality': centrality.get(node_id, 0.0),
            'outbound': [d.to_dict() for d in data['outbound']],
            'inbound': [d.to_dict() for d in data['inbound']],
        }

    summary = SystemicRiskGraphService.graph_summary(org_id)
    HookService.trigger_hook('after_systemic_risk_analysis', org_id=org_id, metrics=summary)

    return jsonify({
        'nodes': nodes_serialized,
        'single_points_of_failure': spofs,
        'summary': summary
    }), 200


@systemic_resilience_bp.route('/api/v1/systemic-resilience/scenarios', methods=['GET'])
@jwt_required
def api_get_scenarios():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    scenarios = ContagionScenario.query.filter_by(organization_id=org_id).all()
    return jsonify([s.to_dict() for s in scenarios]), 200


@systemic_resilience_bp.route('/api/v1/systemic-resilience/scenarios', methods=['POST'])
@jwt_required
def api_create_scenario():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    name = data.get('name')
    scenario_type = data.get('scenario_type')
    initial_node_id = data.get('initial_node_id')

    if not org_id or not name or not scenario_type:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        scenario = ContagionSimulationService.create_scenario(
            name=name,
            description=data.get('description'),
            scenario_type=scenario_type,
            initial_node_id=initial_node_id,
            severity=data.get('severity', 'high'),
            initial_impact_score=data.get('initial_impact_score', 50.0),
            propagation_depth=data.get('propagation_depth', 5),
            correlation_factor=data.get('correlation_factor', 0.5),
            random_seed=data.get('random_seed', 42),
            org_id=org_id
        )
        return jsonify(scenario.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@systemic_resilience_bp.route('/api/v1/systemic-resilience/scenarios/<int:scenario_id>/simulate', methods=['POST'])
@jwt_required
def api_simulate_scenario(scenario_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    # IDOR check
    scenario = ContagionScenario.query.filter_by(id=scenario_id, organization_id=org_id).first()
    if not scenario:
        return jsonify({'error': 'Scenario not found'}), 404

    HookService.trigger_hook('before_contagion_simulation', scenario_id=scenario_id, org_id=org_id)
    try:
        run = ContagionSimulationService.start_simulation(scenario_id, org_id)
        HookService.trigger_hook('after_contagion_simulation', run_id=run.id, org_id=org_id)
        return jsonify(run.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@systemic_resilience_bp.route('/api/v1/systemic-resilience/simulations', methods=['GET'])
@jwt_required
def api_get_simulations():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    runs = ContagionSimulationRun.query.filter_by(organization_id=org_id).all()
    return jsonify([r.to_dict() for r in runs]), 200


@systemic_resilience_bp.route('/api/v1/systemic-resilience/simulations/<int:run_id>', methods=['GET'])
@jwt_required
def api_get_simulation_details(run_id):
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    run = ContagionSimulationRun.query.filter_by(id=run_id, organization_id=org_id).first()
    if not run:
        return jsonify({'error': 'Simulation run not found'}), 404
    return jsonify(run.to_dict()), 200


@systemic_resilience_bp.route('/api/v1/systemic-resilience/simulations/<int:run_id>/timeline', methods=['GET'])
@jwt_required
def api_get_simulation_timeline(run_id):
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    try:
        events = ContagionSimulationService.replay_simulation(run_id, org_id)
        return jsonify([e.to_dict() for e in events]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@systemic_resilience_bp.route('/api/v1/systemic-resilience/concentration-risk', methods=['GET'])
@jwt_required
def api_get_concentration_risk():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    risks = SystemicStressService.identify_concentration_failures(org_id)
    return jsonify(risks), 200


@systemic_resilience_bp.route('/api/v1/systemic-resilience/plans', methods=['GET'])
@jwt_required
def api_get_plans():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    plans = CollectiveResiliencePlan.query.filter_by(organization_id=org_id).all()
    return jsonify([p.to_dict() for p in plans]), 200


@systemic_resilience_bp.route('/api/v1/systemic-resilience/plans', methods=['POST'])
@jwt_required
def api_create_plan():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    name = data.get('name')
    plan_type = data.get('plan_type')
    node_ids = data.get('participating_node_ids', [])

    if not org_id or not name or not plan_type:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        plan = CollectiveResilienceService.create_plan(
            name=name,
            scope=data.get('scope'),
            plan_type=plan_type,
            participating_node_ids=node_ids,
            estimated_cost=data.get('estimated_cost', 0.0),
            org_id=org_id
        )
        return jsonify(plan.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@systemic_resilience_bp.route('/api/v1/systemic-resilience/plans/<int:plan_id>/evaluate', methods=['POST'])
@jwt_required
def api_evaluate_plan(plan_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    factor = data.get('improvement_factor', 0.2)

    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    # IDOR check
    plan = CollectiveResiliencePlan.query.filter_by(id=plan_id, organization_id=org_id).first()
    if not plan:
        return jsonify({'error': 'Resilience plan not found'}), 404

    HookService.trigger_hook('before_collective_resilience_evaluation', plan_id=plan_id, org_id=org_id)
    try:
        res = CollectiveResilienceService.evaluate_plan(plan_id, factor, org_id)
        HookService.trigger_hook('after_collective_resilience_evaluation', plan_id=plan_id, org_id=org_id)
        return jsonify(res.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@systemic_resilience_bp.route('/api/v1/systemic-resilience/plans/<int:plan_id>/approve', methods=['POST'])
@jwt_required
def api_approve_plan(plan_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    approved_by = data.get('approved_by')

    if not org_id or not approved_by:
        return jsonify({'error': 'org_id and approved_by required'}), 400

    try:
        plan = CollectiveResilienceService.approve_plan(plan_id, approved_by, org_id)
        return jsonify(plan.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@systemic_resilience_bp.route('/api/v1/systemic-resilience/mutual-aid', methods=['GET'])
@jwt_required
def api_get_mutual_aid():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    aids = MutualAidSimulation.query.filter_by(organization_id=org_id).all()
    return jsonify([a.to_dict() for a in aids]), 200


@systemic_resilience_bp.route('/api/v1/systemic-resilience/mutual-aid/simulate', methods=['POST'])
@jwt_required
def api_simulate_mutual_aid():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    provider_id = data.get('provider_node_id')
    recipient_id = data.get('recipient_node_id')
    assistance_type = data.get('assistance_type')
    allocated = data.get('capacity_allocated', 0.0)
    run_id = data.get('simulation_run_id')

    if not org_id or not provider_id or not recipient_id or not assistance_type:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        aid = MutualAidSimulationService.allocate_simulated_capacity(
            provider_node_id=provider_id,
            recipient_node_id=recipient_id,
            assistance_type=assistance_type,
            capacity_requested=allocated,
            run_id=run_id,
            org_id=org_id
        )
        return jsonify(aid.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@systemic_resilience_bp.route('/api/v1/systemic-resilience/governance', methods=['GET'])
@jwt_required
def api_get_governance():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    records = FederationGovernanceRecord.query.filter_by(organization_id=org_id).all()
    return jsonify([r.to_dict() for r in records]), 200


@systemic_resilience_bp.route('/api/v1/systemic-resilience/governance', methods=['POST'])
@jwt_required
def api_create_governance():
    data = request.get_json() or {}
    org_id = data.get('org_id')
    title = data.get('title')
    decision_type = data.get('decision_type')

    if not org_id or not title or not decision_type:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        proposal = FederationGovernanceService.create_proposal(
            title=title,
            decision_type=decision_type,
            scope=data.get('scope'),
            proposal_summary=data.get('proposal_summary'),
            participating_entities=data.get('participating_entities', []),
            org_id=org_id
        )
        return jsonify(proposal.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@systemic_resilience_bp.route('/api/v1/systemic-resilience/governance/<int:record_id>/approve', methods=['POST'])
@jwt_required
def api_approve_governance(record_id):
    data = request.get_json() or {}
    org_id = data.get('org_id')
    approved_by = data.get('approved_by')

    if not org_id or not approved_by:
        return jsonify({'error': 'org_id and approved_by required'}), 400

    HookService.trigger_hook('before_federation_governance_decision', record_id=record_id, org_id=org_id)
    try:
        proposal = FederationGovernanceService.approve_decision(record_id, approved_by, org_id)
        HookService.trigger_hook('after_federation_governance_decision', record_id=record_id, org_id=org_id)
        return jsonify(proposal.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@systemic_resilience_bp.route('/api/v1/systemic-resilience/ecosystem', methods=['GET'])
@jwt_required
def api_get_ecosystem():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    summary = EcosystemResilienceService.ecosystem_summary(org_id)
    return jsonify(summary), 200


@systemic_resilience_bp.route('/api/v1/systemic-resilience/brief', methods=['GET'])
@jwt_required
def api_get_brief():
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    brief = ExecutiveSystemicRiskAI.generate_systemic_risk_brief(org_id)
    return jsonify({'brief': brief}), 200


# ─────────────────────────────────────────────────────────────────────────────
# Admin Dashboards (7 views)
# ─────────────────────────────────────────────────────────────────────────────

@systemic_resilience_bp.route('/admin/systemic-resilience', methods=['GET'])
@require_admin
def admin_dashboard():
    org_id = request.args.get('org_id', default=1, type=int)
    summary = EcosystemResilienceService.ecosystem_summary(org_id)
    return render_template(
        'admin_systemic_resilience.html',
        org_id=org_id,
        summary=summary
    )


@systemic_resilience_bp.route('/admin/systemic-resilience/graph', methods=['GET'])
@require_admin
def admin_graph():
    org_id = request.args.get('org_id', default=1, type=int)
    nodes = SystemicRiskNode.query.filter_by(organization_id=org_id).all()
    deps = SystemicDependency.query.filter_by(organization_id=org_id).all()
    return render_template(
        'admin_systemic_risk_graph.html',
        org_id=org_id,
        nodes=nodes,
        dependencies=deps
    )


@systemic_resilience_bp.route('/admin/systemic-resilience/contagion', methods=['GET'])
@require_admin
def admin_contagion():
    org_id = request.args.get('org_id', default=1, type=int)
    scenarios = ContagionScenario.query.filter_by(organization_id=org_id).all()
    runs = ContagionSimulationRun.query.filter_by(organization_id=org_id).all()
    return render_template(
        'admin_contagion_simulation.html',
        org_id=org_id,
        scenarios=scenarios,
        runs=runs
    )


@systemic_resilience_bp.route('/admin/systemic-resilience/concentration', methods=['GET'])
@require_admin
def admin_concentration():
    org_id = request.args.get('org_id', default=1, type=int)
    risks = SystemicStressService.identify_concentration_failures(org_id)
    return render_template(
        'admin_concentration_risk.html',
        org_id=org_id,
        risks=risks
    )


@systemic_resilience_bp.route('/admin/systemic-resilience/plans', methods=['GET'])
@require_admin
def admin_plans():
    org_id = request.args.get('org_id', default=1, type=int)
    plans = CollectiveResiliencePlan.query.filter_by(organization_id=org_id).all()
    return render_template(
        'admin_collective_resilience.html',
        org_id=org_id,
        plans=plans
    )


@systemic_resilience_bp.route('/admin/systemic-resilience/mutual-aid', methods=['GET'])
@require_admin
def admin_mutual_aid():
    org_id = request.args.get('org_id', default=1, type=int)
    records = MutualAidSimulation.query.filter_by(organization_id=org_id).all()
    return render_template(
        'admin_mutual_aid.html',
        org_id=org_id,
        records=records
    )


@systemic_resilience_bp.route('/admin/systemic-resilience/governance', methods=['GET'])
@require_admin
def admin_governance():
    org_id = request.args.get('org_id', default=1, type=int)
    proposals = FederationGovernanceRecord.query.filter_by(organization_id=org_id).all()
    return render_template(
        'admin_federation_governance.html',
        org_id=org_id,
        proposals=proposals
    )
