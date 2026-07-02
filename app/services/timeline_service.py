from app.models.attack_event import AttackEvent
from app.models.defense_action import DefenseAction
from app.models.incident import Incident
from app.models.attack_simulation import AttackSimulation

class TimelineService:
    @staticmethod
    def get_timeline(simulation_id: int) -> list[dict]:
        """
        Generate a chronological feed of all simulation milestones, attack steps,
        detection alerts, and mitigation actions for playback and review.
        """
        timeline = []

        # Fetch the simulation root timing
        sim = AttackSimulation.query.get(simulation_id)
        if not sim:
            return []

        if sim.started_at:
            timeline.append({
                'timestamp': sim.started_at.isoformat(),
                'type': 'simulation_started',
                'title': 'Simulation Started',
                'description': f'Cyber range simulation "{sim.name}" initiated.',
                'severity': 'info'
            })

        # 1. Add Attack Events
        attack_events = AttackEvent.query.filter_by(simulation_id=simulation_id).all()
        for ae in attack_events:
            ts = ae.created_at or sim.created_at
            timeline.append({
                'timestamp': ts.isoformat(),
                'type': 'attack_event',
                'title': f'Attack: {ae.technique or ae.tactic.replace("_", " ").title()}',
                'description': ae.payload_metadata.get('description', 'Simulated attack action.'),
                'severity': ae.severity,
                'details': {
                    'tactic': ae.tactic,
                    'technique_id': ae.technique_id,
                    'source': ae.source,
                    'target': ae.target,
                    'points': ae.points_awarded
                }
            })

        # 2. Add Defense Actions
        defense_actions = DefenseAction.query.join(AttackEvent).filter(AttackEvent.simulation_id == simulation_id).all()
        for da in defense_actions:
            ts = da.created_at or sim.created_at
            timeline.append({
                'timestamp': ts.isoformat(),
                'type': 'defense_action',
                'title': f'Defense: {da.action.replace("_", " ").title()}',
                'description': f'Mitigation executed by SOC Analyst: {da.analyst}.',
                'severity': 'low' if da.effectiveness >= 0.8 else 'medium',
                'details': {
                    'analyst': da.analyst,
                    'response_time_seconds': da.response_time,
                    'effectiveness': da.effectiveness,
                    'points': da.points_awarded
                }
            })

        # 3. Add Incident Milestones
        incidents = Incident.query.filter_by(simulation_id=simulation_id).all()
        for inc in incidents:
            if inc.detected_at:
                timeline.append({
                    'timestamp': inc.detected_at.isoformat(),
                    'type': 'incident_detected',
                    'title': f'Incident Escalation: {inc.title}',
                    'description': inc.description,
                    'severity': 'medium'
                })
            if inc.contained_at:
                timeline.append({
                    'timestamp': inc.contained_at.isoformat(),
                    'type': 'incident_contained',
                    'title': f'Incident Contained',
                    'description': f'Incident "{inc.title}" has been contained.',
                    'severity': 'info'
                })
            if inc.resolved_at:
                timeline.append({
                    'timestamp': inc.resolved_at.isoformat(),
                    'type': 'incident_resolved',
                    'title': f'Incident Resolved',
                    'description': f'Lessons learned stage complete for incident: "{inc.title}".',
                    'severity': 'info'
                })

        if sim.ended_at:
            timeline.append({
                'timestamp': sim.ended_at.isoformat(),
                'type': 'simulation_completed',
                'title': 'Simulation Completed',
                'description': f'Simulation session ended. Final scores: Red Team {sim.red_score} | Blue Team {sim.blue_score}',
                'severity': 'info'
            })

        # Sort timeline chronologically by timestamp string
        timeline.sort(key=lambda x: x['timestamp'])
        return timeline
