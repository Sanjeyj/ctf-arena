"""
CommandMetric model - Phase 29 Global Cyber Command Center.
Composite command performance metric tracking response, resilience, readiness, and intelligence scores.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class CommandMetric(db.Model, TimestampMixin, TenantMixin):
    """Command performance metric model."""
    __tablename__ = 'command_metrics'

    id = db.Column(db.Integer, primary_key=True)
    response_score = db.Column(db.Float, default=0.5, nullable=False)
    resilience_score = db.Column(db.Float, default=0.5, nullable=False)
    readiness_score = db.Column(db.Float, default=0.5, nullable=False)
    intelligence_score = db.Column(db.Float, default=0.5, nullable=False)

    def __repr__(self):
        return (f'<CommandMetric response={self.response_score} '
                f'resilience={self.resilience_score}>')

    def to_dict(self):
        return {
            'id': self.id,
            'response_score': self.response_score,
            'resilience_score': self.resilience_score,
            'readiness_score': self.readiness_score,
            'intelligence_score': self.intelligence_score,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
