"""
Universe REST API and Admin Routes - Phase 30 Unified Cyber Defense Universe.
Enforces multi-tenant isolation, parent ownership validation, and JWT authentication.
"""
import base64
import hmac
import hashlib
import json
from functools import wraps
from flask import request, jsonify, render_template, current_app

from app.universe import universe_bp
from app.extensions import db
from app.utils.decorators import require_admin

# Models
from app.models.defense_universe import DefenseUniverse
from app.models.defense_domain import DefenseDomain
from app.models.universe_node import UniverseNode
from app.models.universe_link import UniverseLink
from app.models.universe_scenario import UniverseScenario
from app.models.universe_simulation import UniverseSimulation
from app.models.universe_event import UniverseEvent
from app.models.universe_metric import UniverseMetric

# Services
from app.services.universe_service import UniverseService
from app.services.topology_service import TopologyService
from app.services.scenario_engine_service import ScenarioEngineService
from app.services.universe_timeline_service import UniverseTimelineService
from app.services.posture_fusion_service import PostureFusionService
from app.services.executive_universe_ai import ExecutiveUniverseAI


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

@universe_bp.route('/api/v1/universe', methods=['GET'])
@jwt_required
def api_get_universes():
    """GET /api/v1/universe — list all universes for the organization."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    unis = DefenseUniverse.query.filter_by(organization_id=org_id).all()
    return jsonify([u.to_dict() for u in unis]), 200


@universe_bp.route('/api/v1/universe', methods=['POST'])
@jwt_required
def api_create_universe():
    """POST /api/v1/universe — create a new defense universe."""
    data = request.get_json() or {}
    name = data.get('name')
    org_id = data.get('org_id') or request.args.get('org_id', type=int)
    if not name or not org_id:
        return jsonify({'error': 'name and org_id are required'}), 400
    description = data.get('description')
    utype = data.get('universe_type', 'default')
    uni = UniverseService.create_universe(name, org_id, description, utype)
    return jsonify(uni.to_dict()), 201


@universe_bp.route('/api/v1/universe/<int:universe_id>', methods=['GET'])
@jwt_required
def api_get_universe(universe_id):
    """GET /api/v1/universe/<id> — retrieve a single universe."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    uni = db.session.get(DefenseUniverse, universe_id)
    if not uni or uni.organization_id != org_id:
        return jsonify({'error': 'Universe not found'}), 404
    return jsonify(uni.to_dict()), 200


@universe_bp.route('/api/v1/universe/<int:universe_id>/topology', methods=['GET'])
@jwt_required
def api_get_topology(universe_id):
    """GET /api/v1/universe/<id>/topology — retrieve universe domains, nodes, and links."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    uni = db.session.get(DefenseUniverse, universe_id)
    if not uni or uni.organization_id != org_id:
        return jsonify({'error': 'Universe not found'}), 404

    domains = DefenseDomain.query.filter_by(universe_id=universe_id, organization_id=org_id).all()
    nodes = UniverseNode.query.filter_by(universe_id=universe_id, organization_id=org_id).all()
    links = UniverseLink.query.filter_by(universe_id=universe_id, organization_id=org_id).all()

    return jsonify({
        'universe_id': universe_id,
        'domains': [d.to_dict() for d in domains],
        'nodes': [n.to_dict() for n in nodes],
        'links': [l.to_dict() for l in links],
    }), 200


@universe_bp.route('/api/v1/universe/<int:universe_id>/nodes', methods=['POST'])
@jwt_required
def api_add_node(universe_id):
    """POST /api/v1/universe/<id>/nodes — add a node to a domain in the universe."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    uni = db.session.get(DefenseUniverse, universe_id)
    if not uni or uni.organization_id != org_id:
        return jsonify({'error': 'Universe not found'}), 404

    data = request.get_json() or {}
    domain_id = data.get('domain_id')
    node_name = data.get('node_name')
    node_type = data.get('node_type')
    if not domain_id or not node_name or not node_type:
        return jsonify({'error': 'domain_id, node_name, and node_type are required'}), 400

    # Parent ownership validation
    dom = db.session.get(DefenseDomain, domain_id)
    if not dom or dom.universe_id != universe_id or dom.organization_id != org_id:
        return jsonify({'error': 'Invalid domain for this universe'}), 400

    node = TopologyService.add_node(
        universe_id=universe_id,
        domain_id=domain_id,
        node_name=node_name,
        node_type=node_type,
        org_id=org_id,
        region=data.get('region'),
        criticality=data.get('criticality', 'medium'),
        metadata=data.get('metadata')
    )
    return jsonify(node.to_dict()), 201


@universe_bp.route('/api/v1/universe/<int:universe_id>/links', methods=['POST'])
@jwt_required
def api_add_link(universe_id):
    """POST /api/v1/universe/<id>/links — add dependency linkage between nodes."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    uni = db.session.get(DefenseUniverse, universe_id)
    if not uni or uni.organization_id != org_id:
        return jsonify({'error': 'Universe not found'}), 404

    data = request.get_json() or {}
    source_id = data.get('source_node_id')
    target_id = data.get('target_node_id')
    rel_type = data.get('relationship_type', 'dependency')
    if not source_id or not target_id:
        return jsonify({'error': 'source_node_id and target_node_id are required'}), 400

    # Parent ownership validation on both nodes
    n1 = db.session.get(UniverseNode, source_id)
    n2 = db.session.get(UniverseNode, target_id)
    if not n1 or n1.universe_id != universe_id or n1.organization_id != org_id:
        return jsonify({'error': 'Invalid source node'}), 400
    if not n2 or n2.universe_id != universe_id or n2.organization_id != org_id:
        return jsonify({'error': 'Invalid target node'}), 400

    link = TopologyService.link_nodes(
        universe_id=universe_id,
        source_node_id=source_id,
        target_node_id=target_id,
        relationship_type=rel_type,
        org_id=org_id,
        dependency_weight=data.get('dependency_weight', 1.0),
        trust_score=data.get('trust_score', 1.0)
    )
    return jsonify(link.to_dict()), 201


@universe_bp.route('/api/v1/universe/<int:universe_id>/scenarios', methods=['GET'])
@jwt_required
def api_get_scenarios(universe_id):
    """GET /api/v1/universe/<id>/scenarios — list scenarios for a universe."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    uni = db.session.get(DefenseUniverse, universe_id)
    if not uni or uni.organization_id != org_id:
        return jsonify({'error': 'Universe not found'}), 404

    scenarios = UniverseScenario.query.filter_by(universe_id=universe_id, organization_id=org_id).all()
    return jsonify([s.to_dict() for s in scenarios]), 200


@universe_bp.route('/api/v1/universe/<int:universe_id>/scenarios', methods=['POST'])
@jwt_required
def api_create_scenario(universe_id):
    """POST /api/v1/universe/<id>/scenarios — create a scenario in the universe."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    uni = db.session.get(DefenseUniverse, universe_id)
    if not uni or uni.organization_id != org_id:
        return jsonify({'error': 'Universe not found'}), 404

    data = request.get_json() or {}
    name = data.get('scenario_name')
    stype = data.get('scenario_type')
    if not name or not stype:
        return jsonify({'error': 'scenario_name and scenario_type are required'}), 400

    scen = ScenarioEngineService.create_scenario(
        universe_id=universe_id,
        scenario_name=name,
        scenario_type=stype,
        org_id=org_id,
        severity=data.get('severity', 'medium'),
        configuration=data.get('configuration')
    )
    return jsonify(scen.to_dict()), 201


@universe_bp.route('/api/v1/universe/scenarios/<int:scenario_id>/simulate', methods=['POST'])
@jwt_required
def api_simulate_scenario(scenario_id):
    """POST /api/v1/universe/scenarios/<id>/simulate — run wargame simulation for scenario."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    scen = db.session.get(UniverseScenario, scenario_id)
    if not scen or scen.organization_id != org_id:
        return jsonify({'error': 'Scenario not found'}), 404

    sim = ScenarioEngineService.simulate(scenario_id, org_id)
    if not sim:
        return jsonify({'error': 'Simulation failed'}), 500
    return jsonify(sim.to_dict()), 201


@universe_bp.route('/api/v1/universe/simulations/<int:simulation_id>', methods=['GET'])
@jwt_required
def api_get_simulation(simulation_id):
    """GET /api/v1/universe/simulations/<id> — get simulation details."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    sim = db.session.get(UniverseSimulation, simulation_id)
    if not sim or sim.organization_id != org_id:
        return jsonify({'error': 'Simulation not found'}), 404
    return jsonify(sim.to_dict()), 200


@universe_bp.route('/api/v1/universe/simulations/<int:simulation_id>/timeline', methods=['GET'])
@jwt_required
def api_get_timeline(simulation_id):
    """GET /api/v1/universe/simulations/<id>/timeline — retrieve wargame timeline events."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    sim = db.session.get(UniverseSimulation, simulation_id)
    if not sim or sim.organization_id != org_id:
        return jsonify({'error': 'Simulation not found'}), 404

    events = UniverseTimelineService.get_timeline(simulation_id, org_id)
    return jsonify([e.to_dict() for e in events]), 200


@universe_bp.route('/api/v1/universe/<int:universe_id>/posture', methods=['GET'])
@jwt_required
def api_get_posture(universe_id):
    """GET /api/v1/universe/<id>/posture — get posture fusion KPIs."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    uni = db.session.get(DefenseUniverse, universe_id)
    if not uni or uni.organization_id != org_id:
        return jsonify({'error': 'Universe not found'}), 404

    score = PostureFusionService.calculate_global_score(universe_id, org_id)
    agg = PostureFusionService.aggregate_domains(universe_id, org_id)
    weak = PostureFusionService.identify_weak_domains(universe_id, org_id)
    trends = PostureFusionService.trend(universe_id, org_id)

    return jsonify({
        'universe_id': universe_id,
        'global_score': score,
        'aggregated_domains': agg,
        'weak_domains': weak,
        'trends': trends
    }), 200


@universe_bp.route('/api/v1/universe/<int:universe_id>/brief', methods=['GET'])
@jwt_required
def api_get_brief(universe_id):
    """GET /api/v1/universe/<id>/brief — retrieve AI executive brief guide."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    uni = db.session.get(DefenseUniverse, universe_id)
    if not uni or uni.organization_id != org_id:
        return jsonify({'error': 'Universe not found'}), 404

    brief = ExecutiveUniverseAI.generate_brief(universe_id, org_id)
    summary = ExecutiveUniverseAI.summarize(universe_id, org_id)
    risk = ExecutiveUniverseAI.explain_risk(universe_id, org_id)

    return jsonify({
        'universe_id': universe_id,
        'brief': brief,
        'summary': summary,
        'risk_analysis': risk
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# Admin Dashboard Routes
# ─────────────────────────────────────────────────────────────────────────────

@universe_bp.route('/admin/universe', methods=['GET'])
@require_admin
def admin_universe():
    """Admin: Overview dashboard for all universes."""
    unis = DefenseUniverse.query.all()
    return render_template('admin_universe.html', universes=unis)


@universe_bp.route('/admin/universe/<int:universe_id>', methods=['GET'])
@require_admin
def admin_universe_detail(universe_id):
    """Admin: Single universe details view."""
    uni = db.session.get(DefenseUniverse, universe_id)
    if not uni:
         return "Universe not found", 404
    domains = DefenseDomain.query.filter_by(universe_id=universe_id).all()
    sims = UniverseSimulation.query.filter_by(universe_id=universe_id).order_by(UniverseSimulation.started_at.desc()).all()
    return render_template('admin_universe_detail.html', universe=uni, domains=domains, simulations=sims)


@universe_bp.route('/admin/universe/<int:universe_id>/topology', methods=['GET'])
@require_admin
def admin_universe_topology(universe_id):
    """Admin: Topology nodes and dependency links map."""
    uni = db.session.get(DefenseUniverse, universe_id)
    if not uni:
         return "Universe not found", 404
    nodes = UniverseNode.query.filter_by(universe_id=universe_id).all()
    links = UniverseLink.query.filter_by(universe_id=universe_id).all()
    return render_template('admin_universe_topology.html', universe=uni, nodes=nodes, links=links)


@universe_bp.route('/admin/universe/<int:universe_id>/scenarios', methods=['GET'])
@require_admin
def admin_universe_scenarios(universe_id):
    """Admin: What-if scenarios config list."""
    uni = db.session.get(DefenseUniverse, universe_id)
    if not uni:
         return "Universe not found", 404
    scenarios = UniverseScenario.query.filter_by(universe_id=universe_id).all()
    return render_template('admin_universe_scenarios.html', universe=uni, scenarios=scenarios)


@universe_bp.route('/admin/universe/simulation/<int:simulation_id>/timeline', methods=['GET'])
@require_admin
def admin_universe_timeline(simulation_id):
    """Admin: Chronological training simulation events timeline."""
    sim = db.session.get(UniverseSimulation, simulation_id)
    if not sim:
        return "Simulation not found", 404
    events = UniverseEvent.query.filter_by(simulation_id=simulation_id).order_by(UniverseEvent.event_time.asc()).all()
    return render_template('admin_universe_timeline.html', simulation=sim, events=events)


@universe_bp.route('/admin/universe/<int:universe_id>/posture', methods=['GET'])
@require_admin
def admin_universe_posture(universe_id):
    """Admin: Composite health metrics posture fusion KPIs."""
    uni = db.session.get(DefenseUniverse, universe_id)
    if not uni:
         return "Universe not found", 404
    metrics = UniverseMetric.query.filter_by(universe_id=universe_id).order_by(UniverseMetric.measured_at.desc()).all()
    return render_template('admin_universe_posture.html', universe=uni, metrics=metrics)
