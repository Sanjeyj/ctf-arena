"""
CommandService - Phase 29 Global Cyber Command Center.
Manages command center activation, multi-center coordination, and status monitoring.
"""
from app.extensions import db
from app.models.command_center import CommandCenter
from app.models.command_metric import CommandMetric


class CommandService:
    @staticmethod
    def activate(center_id: int) -> CommandCenter:
        """Activate a command center and set readiness to full."""
        center = db.session.get(CommandCenter, center_id)
        if not center:
            return None
        center.status = 'operational'
        center.readiness = 1.0
        db.session.commit()
        return center

    @staticmethod
    def coordinate(org_id: int) -> dict:
        """Coordinate all command centers in an organization — return summary."""
        centers = CommandCenter.query.filter_by(organization_id=org_id).all()
        if not centers:
            return {'centers': 0, 'avg_readiness': 0.0, 'coordination': 'no_centers'}
        avg = sum(c.readiness for c in centers) / len(centers)
        coordination = 'optimal' if avg >= 0.8 else 'degraded' if avg >= 0.5 else 'critical'
        return {
            'centers': len(centers),
            'avg_readiness': round(avg, 3),
            'coordination': coordination,
        }

    @staticmethod
    def monitor(org_id: int) -> CommandMetric:
        """Return or create a command metric snapshot for the organization."""
        metric = CommandMetric.query.filter_by(organization_id=org_id).first()
        if not metric:
            metric = CommandMetric(
                response_score=0.6,
                resilience_score=0.65,
                readiness_score=0.7,
                intelligence_score=0.6,
                organization_id=org_id,
            )
            db.session.add(metric)
            db.session.commit()
        return metric
