import datetime
from flask import request, jsonify, g
from app.cyberrange import cyberrange_bp
from app.utils.decorators import require_login
from app.extensions import db
from app.models.attack_simulation import AttackSimulation
from app.models.incident import Incident
from app.models.mitre_technique import MitreTechnique
from app.services.mitre_service import MitreService
from app.services.timeline_service import TimelineService
from app.services.incident_service import IncidentService

@cyberrange_bp.route('/api/v1/simulation/start', methods=['POST'])
@require_login
def start_simulation():
    data = request.get_json(silent=True) or {}
    name = data.get('name', 'Simulated Cyber Exercise')
    attacker_type = data.get('attacker_type', 'easy_ai')
    defender_type = data.get('defender_type', 'l1_soc')

    sim = AttackSimulation(
        name=name,
        attacker_type=attacker_type,
        defender_type=defender_type,
        status='running',
        started_at=datetime.datetime.utcnow(),
        organization_id=getattr(g, 'current_org', None).id if getattr(g, 'current_org', None) else None
    )
    db.session.add(sim)
    db.session.commit()

    return jsonify({
        'message': 'Simulation started successfully.',
        'simulation': {
            'id': sim.id,
            'name': sim.name,
            'status': sim.status,
            'attacker_type': sim.attacker_type,
            'defender_type': sim.defender_type
        }
    }), 201


@cyberrange_bp.route('/api/v1/simulation/stop', methods=['POST'])
@require_login
def stop_simulation():
    data = request.get_json(silent=True) or {}
    sim_id = data.get('simulation_id')

    if not sim_id:
        return jsonify({'error': 'simulation_id is required.'}), 400

    sim = AttackSimulation.query.get(sim_id)
    if not sim:
        return jsonify({'error': 'Simulation session not found.'}), 404

    sim.status = 'completed'
    sim.ended_at = datetime.datetime.utcnow()
    db.session.commit()

    return jsonify({
        'message': 'Simulation completed.',
        'simulation': {
            'id': sim.id,
            'status': sim.status,
            'red_score': sim.red_score,
            'blue_score': sim.blue_score
        }
    }), 200


@cyberrange_bp.route('/api/v1/simulation/<int:sim_id>', methods=['GET'])
@require_login
def get_simulation(sim_id):
    sim = AttackSimulation.query.get(sim_id)
    if not sim:
        return jsonify({'error': 'Simulation not found.'}), 404

    return jsonify({
        'simulation': {
            'id': sim.id,
            'name': sim.name,
            'status': sim.status,
            'attacker_type': sim.attacker_type,
            'defender_type': sim.defender_type,
            'red_score': sim.red_score,
            'blue_score': sim.blue_score,
            'started_at': sim.started_at.isoformat() if sim.started_at else None,
            'ended_at': sim.ended_at.isoformat() if sim.ended_at else None
        }
    }), 200


@cyberrange_bp.route('/api/v1/timeline/<int:sim_id>', methods=['GET'])
@require_login
def get_timeline(sim_id):
    sim = AttackSimulation.query.get(sim_id)
    if not sim:
        return jsonify({'error': 'Simulation not found.'}), 404

    timeline = TimelineService.get_timeline(sim_id)
    return jsonify({
        'simulation_id': sim_id,
        'timeline': timeline
    }), 200


@cyberrange_bp.route('/api/v1/incident', methods=['POST'])
@require_login
def start_incident():
    data = request.get_json(silent=True) or {}
    title = data.get('title')
    description = data.get('description', '')
    simulation_id = data.get('simulation_id')

    if not title or not simulation_id:
        return jsonify({'error': 'title and simulation_id are required.'}), 400

    sim = AttackSimulation.query.get(simulation_id)
    if not sim:
        return jsonify({'error': 'Simulation not found.'}), 404

    incident = IncidentService.create_incident(title, description, simulation_id)
    return jsonify({
        'message': 'Incident escalated.',
        'incident': {
            'id': incident.id,
            'title': incident.title,
            'status': incident.status,
            'workflow_stage': incident.workflow_stage
        }
    }), 201


@cyberrange_bp.route('/api/v1/mitre', methods=['GET'])
@require_login
def get_mitre_techniques():
    MitreService.seed_techniques()
    techniques = MitreTechnique.query.all()
    
    # Group by tactic
    mitre_map = {}
    for t in techniques:
        if t.tactic not in mitre_map:
            mitre_map[t.tactic] = []
        mitre_map[t.tactic].append({
            'technique_id': t.technique_id,
            'name': t.name,
            'description': t.description,
            'mitigation': t.mitigation
        })

    return jsonify({
        'mitre_techniques': mitre_map
    }), 200
