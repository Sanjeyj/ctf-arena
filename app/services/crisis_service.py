"""
CrisisService - Phase 25 Cyber Resilience & Digital Enterprise.
Implements incident lifecycles to declare, coordinate, and resolve organizational crisis events.
"""
from app.extensions import db, utcnow
from app.models.crisis_event import CrisisEvent

class CrisisService:
    @staticmethod
    def declare_crisis(event_name: str, severity: str, organization_id: int) -> CrisisEvent:
        """Create and log a new active crisis event."""
        # Calculate starting impact score: critical=80, high=50, medium=30
        initial_scores = {'critical': 80.0, 'high': 50.0, 'medium': 30.0}
        score = initial_scores.get(severity.lower(), 20.0)

        crisis = CrisisEvent(
            event_name=event_name,
            severity=severity,
            status='active',
            start_time=utcnow(),
            impact_score=score,
            organization_id=organization_id
        )
        db.session.add(crisis)
        db.session.commit()
        return crisis

    @staticmethod
    def coordinate(event_id: int, update_text: str) -> dict:
        """Post a coordinating message update and re-evaluate crisis status."""
        event = CrisisEvent.query.get(event_id)
        if not event:
            return {'error': f"CrisisEvent {event_id} not found."}

        # Simulating that coordinating/handling updates reduces the threat impact score slightly
        event.impact_score = max(5.0, event.impact_score - 5.0)
        db.session.commit()

        return {
            'event_id': event.id,
            'event_name': event.event_name,
            'current_impact_score': event.impact_score,
            'update_logged': update_text
        }

    @staticmethod
    def resolve(event_id: int) -> CrisisEvent:
        """Set the crisis event status to resolved and minimize impact score."""
        event = CrisisEvent.query.get(event_id)
        if not event:
            return None

        event.status = 'resolved'
        event.impact_score = 0.0
        db.session.commit()
        return event
