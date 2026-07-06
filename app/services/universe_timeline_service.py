"""
UniverseTimelineService - Phase 30 Unified Cyber Defense Universe.
Manages chronological recording, retrieving, and replaying of wargame events.
"""
from app.extensions import db
from app.models.universe_event import UniverseEvent
from app.models.universe_simulation import UniverseSimulation
import datetime


class UniverseTimelineService:
    @staticmethod
    def append_event(simulation_id: int, event_type: str, description: str, org_id: int, domain: str = None, severity: str = 'info', score_delta: float = 0.0, metadata: dict = None) -> UniverseEvent:
        """Append a chronological event to a simulation run."""
        import json
        meta_str = json.dumps(metadata) if metadata else None
        event = UniverseEvent(
            simulation_id=simulation_id,
            event_type=event_type,
            domain=domain,
            severity=severity,
            description=description,
            score_delta=score_delta,
            event_time=datetime.datetime.utcnow(),
            metadata_json=meta_str,
            organization_id=org_id
        )
        db.session.add(event)
        db.session.commit()
        return event

    @staticmethod
    def get_timeline(simulation_id: int, org_id: int) -> list:
        """Get chronological list of events for a simulation run."""
        return (
            UniverseEvent.query
            .filter_by(simulation_id=simulation_id, organization_id=org_id)
            .order_by(UniverseEvent.event_time.asc())
            .all()
        )

    @staticmethod
    def replay(simulation_id: int, org_id: int) -> dict:
        """Run simulated chronological event replay for audit analysis."""
        events = UniverseTimelineService.get_timeline(simulation_id, org_id)
        steps = []
        current_score = 1.0
        for evt in events:
            current_score = round(current_score + evt.score_delta, 3)
            steps.append({
                'event_id': evt.id,
                'event_type': evt.event_type,
                'description': evt.description,
                'score_delta': evt.score_delta,
                'simulated_score': current_score,
                'timestamp': evt.event_time.isoformat() if evt.event_time else None
            })
        return {
            'simulation_id': simulation_id,
            'total_steps': len(steps),
            'replay_timeline': steps
        }

    @staticmethod
    def summarize(simulation_id: int, org_id: int) -> dict:
        """Compute structural outcome summary statistics."""
        sim = db.session.get(UniverseSimulation, simulation_id)
        if not sim or sim.organization_id != org_id:
            return None
        events = UniverseTimelineService.get_timeline(simulation_id, org_id)
        impact = sum(e.score_delta for e in events)
        critical_count = sum(1 for e in events if e.severity == 'critical')
        return {
            'simulation_id': sim.id,
            'initial_score': sim.initial_score,
            'final_score': sim.final_score,
            'total_events': len(events),
            'net_impact': round(impact, 3),
            'critical_events': critical_count
        }

    @staticmethod
    def compare_runs(simulation_id_1: int, simulation_id_2: int, org_id: int) -> dict:
        """Compare structural metrics of two simulation runs."""
        sim1 = db.session.get(UniverseSimulation, simulation_id_1)
        sim2 = db.session.get(UniverseSimulation, simulation_id_2)

        if not sim1 or not sim2 or sim1.organization_id != org_id or sim2.organization_id != org_id:
            return {'error': 'One or both simulation runs not found or access denied'}

        sum1 = UniverseTimelineService.summarize(simulation_id_1, org_id)
        sum2 = UniverseTimelineService.summarize(simulation_id_2, org_id)

        return {
            'run_1': sum1,
            'run_2': sum2,
            'variance': round(sum1['final_score'] - sum2['final_score'], 3),
            'events_difference': sum1['total_events'] - sum2['total_events']
        }
