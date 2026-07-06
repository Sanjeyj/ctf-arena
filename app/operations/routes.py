"""
Operations Fabric REST API and Admin Routes - Phase 33 Cyber Platform Observability, Reliability & Operations Fabric.
Enforces multi-tenant isolation, JWT authentication, and administrative protection.
"""
import base64
import hmac
import hashlib
import json
from functools import wraps
from flask import request, jsonify, render_template, current_app

from app.operations import operations_bp
from app.extensions import db
from app.utils.decorators import require_admin

# Models
from app.models.telemetry_source import TelemetrySource
from app.models.telemetry_metric import TelemetryMetric
from app.models.trace_record import TraceRecord
from app.models.service_health_snapshot import ServiceHealthSnapshot
from app.models.error_budget_record import ErrorBudgetRecord
from app.models.operational_incident import OperationalIncident
from app.models.chaos_experiment import ChaosExperiment
from app.models.operations_timeline_event import OperationsTimelineEvent
from app.models.platform_service import PlatformService
from app.models.reliability_objective import ReliabilityObjective

# Services
from app.services.telemetry_service import TelemetryService
from app.services.trace_service import TraceService
from app.services.health_service import HealthService
from app.services.error_budget_service import ErrorBudgetService
from app.services.incident_correlation_service import IncidentCorrelationService
from app.services.chaos_simulation_service import ChaosSimulationService
from app.services.operations_timeline_service import OperationsTimelineService
from app.services.executive_reliability_ai import ExecutiveReliabilityAI


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

@operations_bp.route('/api/v1/operations-fabric/telemetry', methods=['GET'])
@jwt_required
def api_get_telemetry():
    """GET /api/v1/operations-fabric/telemetry — list registered telemetry sources."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    sources = TelemetrySource.query.filter_by(organization_id=org_id).all()
    return jsonify([s.to_dict() for s in sources]), 200


@operations_bp.route('/api/v1/operations-fabric/telemetry', methods=['POST'])
@jwt_required
def api_register_telemetry_source():
    """POST /api/v1/operations-fabric/telemetry — register telemetry source or ingest metric."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    data = request.get_json() or {}

    # If ingest metric fields are provided, ingest
    if 'source_id' in data and 'metric_name' in data:
        source_id = data.get('source_id')
        src = db.session.get(TelemetrySource, source_id)
        if not src or src.organization_id != org_id:
            return jsonify({'error': 'Unauthorized or invalid source_id'}), 403

        metric = TelemetryService.ingest_metric(
            source_id=source_id,
            metric_name=data.get('metric_name'),
            metric_type=data.get('metric_type', 'gauge'),
            metric_value=float(data.get('metric_value', 0.0)),
            unit=data.get('unit'),
            dimensions_json=data.get('dimensions'),
            org_id=org_id
        )
        return jsonify(metric.to_dict()), 201

    # Else, register new telemetry source
    name = data.get('name')
    stype = data.get('source_type')
    mname = data.get('module_name')
    if not name or not stype or not mname:
        return jsonify({'error': 'Missing name, source_type, or module_name'}), 400

    src = TelemetryService.register_source(
        name=name,
        source_type=stype,
        module_name=mname,
        org_id=org_id,
        collection_interval=int(data.get('collection_interval', 60))
    )
    return jsonify(src.to_dict()), 201


@operations_bp.route('/api/v1/operations-fabric/traces', methods=['GET'])
@jwt_required
def api_get_traces():
    """GET /api/v1/operations-fabric/traces — list active traces."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    spans = TraceRecord.query.filter_by(organization_id=org_id).all()
    return jsonify([s.to_dict() for s in spans]), 200


@operations_bp.route('/api/v1/operations-fabric/traces/<string:trace_id>', methods=['GET'])
@jwt_required
def api_get_trace_tree(trace_id):
    """GET /api/v1/operations-fabric/traces/<id> — retrieve hierarchical trace span tree."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    # Ensure spans exist for trace_id and check tenant boundary
    span = TraceRecord.query.filter_by(trace_id=trace_id).first()
    if not span:
        return jsonify({'error': 'Trace not found'}), 404
    if span.organization_id != org_id:
        return jsonify({'error': 'Unauthorized'}), 403

    tree = TraceService.build_trace_tree(trace_id, org_id)
    return jsonify(tree), 200


@operations_bp.route('/api/v1/operations-fabric/health', methods=['GET'])
@jwt_required
def api_get_health():
    """GET /api/v1/operations-fabric/health — list current platform health states."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    summary = HealthService.health_summary(org_id)
    return jsonify(summary), 200


@operations_bp.route('/api/v1/operations-fabric/health/<int:service_id>', methods=['GET'])
@jwt_required
def api_get_service_health(service_id):
    """GET /api/v1/operations-fabric/health/<service_id> — retrieve health history and dependency tree for a specific service."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    srv = db.session.get(PlatformService, service_id)
    if not srv or srv.organization_id != org_id:
        return jsonify({'error': 'Unauthorized or invalid service'}), 403

    history = HealthService.health_history(service_id, 10, org_id)
    deps = HealthService.dependency_health(service_id, org_id)

    return jsonify({
        'service': srv.to_dict(),
        'history': [h.to_dict() for h in history],
        'dependencies': deps
    }), 200


@operations_bp.route('/api/v1/operations-fabric/error-budgets', methods=['GET'])
@jwt_required
def api_get_error_budgets():
    """GET /api/v1/operations-fabric/error-budgets — list SLO budgets status and forecasts."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    summary = ErrorBudgetService.budget_summary(org_id)
    records = ErrorBudgetRecord.query.filter_by(organization_id=org_id).all()

    detailed_records = []
    for r in records:
        forecast = ErrorBudgetService.forecast_exhaustion(r.reliability_objective_id, org_id)
        d = r.to_dict()
        d['exhaustion_forecast'] = forecast
        detailed_records.append(d)

    return jsonify({
        'summary': summary,
        'budgets': detailed_records
    }), 200


@operations_bp.route('/api/v1/operations-fabric/incidents', methods=['GET'])
@jwt_required
def api_get_incidents():
    """GET /api/v1/operations-fabric/incidents — list incidents."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    incidents = OperationalIncident.query.filter_by(organization_id=org_id).all()
    return jsonify([i.to_dict() for i in incidents]), 200


@operations_bp.route('/api/v1/operations-fabric/incidents', methods=['POST'])
@jwt_required
def api_create_incident():
    """POST /api/v1/operations-fabric/incidents — file operational incident."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    data = request.get_json() or {}

    title = data.get('title')
    severity = data.get('severity')
    source_module = data.get('source_module')
    affected = data.get('affected_services', [])

    if not title or not severity or not source_module:
        return jsonify({'error': 'Missing title, severity, or source_module'}), 400

    inc = IncidentCorrelationService.create_incident(
        title=title,
        severity=severity,
        source_module=source_module,
        affected_services_list=affected,
        root_cause_summary=data.get('root_cause_summary', ''),
        impact_summary=data.get('impact_summary', ''),
        org_id=org_id
    )
    return jsonify(inc.to_dict()), 201


@operations_bp.route('/api/v1/operations-fabric/incidents/<int:incident_id>', methods=['GET'])
@jwt_required
def api_get_incident_detail(incident_id):
    """GET /api/v1/operations-fabric/incidents/<id> — retrieve details, root cause suggested, and impact metrics."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    inc = db.session.get(OperationalIncident, incident_id)
    if not inc or inc.organization_id != org_id:
        return jsonify({'error': 'Unauthorized or invalid incident'}), 403

    impact = IncidentCorrelationService.calculate_impact(incident_id, org_id)
    root_cause = IncidentCorrelationService.suggest_root_cause(incident_id, org_id)

    return jsonify({
        'incident': inc.to_dict(),
        'impact_score': impact,
        'suggested_root_cause': root_cause
    }), 200


@operations_bp.route('/api/v1/operations-fabric/incidents/<int:incident_id>/timeline', methods=['GET'])
@jwt_required
def api_get_incident_timeline(incident_id):
    """GET /api/v1/operations-fabric/incidents/<id>/timeline — chronological events ledger for this incident."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    inc = db.session.get(OperationalIncident, incident_id)
    if not inc or inc.organization_id != org_id:
        return jsonify({'error': 'Unauthorized or invalid incident'}), 403

    events = OperationsTimelineEvent.query.filter_by(
        incident_id=incident_id,
        organization_id=org_id
    ).order_by(OperationsTimelineEvent.event_time.asc()).all()

    return jsonify([e.to_dict() for e in events]), 200


@operations_bp.route('/api/v1/operations-fabric/chaos', methods=['GET'])
@jwt_required
def api_get_chaos_experiments():
    """GET /api/v1/operations-fabric/chaos — list scheduled experiments."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    exps = ChaosExperiment.query.filter_by(organization_id=org_id).all()
    return jsonify([e.to_dict() for e in exps]), 200


@operations_bp.route('/api/v1/operations-fabric/chaos', methods=['POST'])
@jwt_required
def api_create_chaos_experiment():
    """POST /api/v1/operations-fabric/chaos — configure chaos experiment."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400
    data = request.get_json() or {}

    name = data.get('name')
    etype = data.get('experiment_type')
    target = data.get('target_service')
    hypothesis = data.get('hypothesis')

    if not name or not etype or not target or not hypothesis:
        return jsonify({'error': 'Missing name, experiment_type, target_service, or hypothesis'}), 400

    exp = ChaosSimulationService.create_experiment(
        name=name,
        experiment_type=etype,
        target_service=target,
        hypothesis=hypothesis,
        org_id=org_id,
        simulation_parameters_json=data.get('simulation_parameters')
    )
    return jsonify(exp.to_dict()), 201


@operations_bp.route('/api/v1/operations-fabric/chaos/<int:experiment_id>/simulate', methods=['POST'])
@jwt_required
def api_simulate_chaos_experiment(experiment_id):
    """POST /api/v1/operations-fabric/chaos/<id>/simulate — trigger simulated run execution."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    exp = db.session.get(ChaosExperiment, experiment_id)
    if not exp or exp.organization_id != org_id:
        return jsonify({'error': 'Unauthorized or invalid experiment'}), 403

    target = exp.target_service
    etype = exp.experiment_type

    if etype == 'latency_injection':
        res = ChaosSimulationService.simulate_latency(experiment_id, target, org_id)
    elif etype == 'packet_loss':
        # Alias packet_loss to service degradation
        res = ChaosSimulationService.simulate_service_degradation(experiment_id, target, org_id)
    else:
        res = ChaosSimulationService.simulate_dependency_failure(experiment_id, target, org_id)

    passed = ChaosSimulationService.evaluate_hypothesis(experiment_id, org_id)

    return jsonify({
        'experiment': exp.to_dict(),
        'result_score': res,
        'hypothesis_supported': passed
    }), 200


@operations_bp.route('/api/v1/operations-fabric/brief', methods=['GET'])
@jwt_required
def api_get_brief():
    """GET /api/v1/operations-fabric/brief — retrieve AI executive brief summaries."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id required'}), 400

    brief = ExecutiveReliabilityAI.generate_operations_brief(org_id)
    health = ExecutiveReliabilityAI.summarize_platform_health(org_id)
    risk = ExecutiveReliabilityAI.explain_slo_risk(org_id)
    rec = ExecutiveReliabilityAI.recommend_reliability_priorities(org_id)

    return jsonify({
        'operations_brief': brief,
        'platform_health_summary': health,
        'slo_risk_analysis': risk,
        'reliability_recommendations': rec
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# Admin Dashboard Routes
# ─────────────────────────────────────────────────────────────────────────────

@operations_bp.route('/admin/operations-fabric', methods=['GET'])
@require_admin
def admin_operations_fabric():
    """Admin: Overview dashboard displaying overall operations summary and alert feeds."""
    sources = TelemetrySource.query.all()
    incidents = OperationalIncident.query.all()
    exps = ChaosExperiment.query.all()
    return render_template('admin_operations_fabric.html', sources=sources, incidents=incidents, experiments=exps)


@operations_bp.route('/admin/operations-fabric/telemetry', methods=['GET'])
@require_admin
def admin_telemetry():
    """Admin: Telemetry collection sources, status, and metric counts."""
    sources = TelemetrySource.query.all()
    metrics = TelemetryMetric.query.all()
    return render_template('admin_telemetry.html', sources=sources, metrics=metrics)


@operations_bp.route('/admin/operations-fabric/traces', methods=['GET'])
@require_admin
def admin_traces():
    """Admin: Visualized trace spans list."""
    spans = TraceRecord.query.all()
    return render_template('admin_traces.html', spans=spans)


@operations_bp.route('/admin/operations-fabric/health', methods=['GET'])
@require_admin
def admin_service_health():
    """Admin: Golden Signals dashboards for registered capabilities."""
    services = PlatformService.query.all()
    snapshots = ServiceHealthSnapshot.query.all()
    return render_template('admin_service_health.html', services=services, snapshots=snapshots)


@operations_bp.route('/admin/operations-fabric/reliability', methods=['GET'])
@require_admin
def admin_reliability():
    """Admin: Reliability engineering and SLO workspace."""
    objectives = ReliabilityObjective.query.all()
    records = ErrorBudgetRecord.query.all()
    return render_template('admin_reliability_engineering.html', objectives=objectives, records=records)


@operations_bp.route('/admin/operations-fabric/incidents', methods=['GET'])
@require_admin
def admin_incidents():
    """Admin: Incident workspace, affected services, and timelines."""
    incidents = OperationalIncident.query.all()
    events = OperationsTimelineEvent.query.all()
    return render_template('admin_operational_incidents.html', incidents=incidents, events=events)


@operations_bp.route('/admin/operations-fabric/chaos', methods=['GET'])
@require_admin
def admin_chaos():
    """Admin: Chaos engineering simulation workspace."""
    experiments = ChaosExperiment.query.all()
    return render_template('admin_chaos_simulation.html', experiments=experiments)
