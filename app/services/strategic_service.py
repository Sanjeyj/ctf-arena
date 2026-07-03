"""
StrategicService - Phase 29 Global Cyber Command Center.
Manages strategic objectives: prioritization, evaluation, and reporting.
"""
from app.extensions import db
from app.models.strategic_objective import StrategicObjective


class StrategicService:
    @staticmethod
    def prioritize(org_id: int) -> list:
        """Return objectives sorted by priority (ascending = most critical first)."""
        return (
            StrategicObjective.query
            .filter_by(organization_id=org_id)
            .order_by(StrategicObjective.priority.asc())
            .all()
        )

    @staticmethod
    def evaluate(objective_id: int) -> dict:
        """Evaluate progress and status of a single strategic objective."""
        obj = db.session.get(StrategicObjective, objective_id)
        if not obj:
            return {'error': 'Objective not found'}
        health = 'on_track' if obj.progress >= 0.5 else 'at_risk'
        return {
            'id': obj.id,
            'objective': obj.objective,
            'priority': obj.priority,
            'progress': obj.progress,
            'status': obj.status,
            'health': health,
        }

    @staticmethod
    def report(org_id: int) -> dict:
        """Generate a summary report of all strategic objectives."""
        objectives = StrategicObjective.query.filter_by(organization_id=org_id).all()
        if not objectives:
            return {'total': 0, 'achieved': 0, 'in_progress': 0, 'open': 0, 'avg_progress': 0.0}
        achieved = sum(1 for o in objectives if o.status == 'achieved')
        in_progress = sum(1 for o in objectives if o.status == 'in_progress')
        open_count = sum(1 for o in objectives if o.status == 'open')
        avg_progress = round(sum(o.progress for o in objectives) / len(objectives), 3)
        return {
            'total': len(objectives),
            'achieved': achieved,
            'in_progress': in_progress,
            'open': open_count,
            'avg_progress': avg_progress,
        }
