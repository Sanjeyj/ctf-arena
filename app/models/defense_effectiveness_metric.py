"""
DefenseEffectivenessMetric model - Phase 35 Continuous Security Validation.
Tracks historic scoring and daily trends for defense components.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin
import datetime


class DefenseEffectivenessMetric(db.Model, TimestampMixin, TenantMixin):
    """DefenseEffectivenessMetric representation."""
    __tablename__ = 'defense_effectiveness_metrics'

    id = db.Column(db.Integer, primary_key=True)
    metric_type = db.Column(db.String(64), nullable=False)  # control, detection, playbook, resilience, architecture, composite
    resource_type = db.Column(db.String(64), nullable=True)
    resource_id = db.Column(db.Integer, nullable=True)
    score = db.Column(db.Float, default=100.0, nullable=False)
    previous_score = db.Column(db.Float, default=100.0, nullable=False)
    delta = db.Column(db.Float, default=0.0, nullable=False)
    trend = db.Column(db.String(32), default='stable', nullable=False)  # improving, stable, declining
    measured_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<DefenseEffectivenessMetric type={self.metric_type} score={self.score} trend={self.trend}>'

    def to_dict(self):
        return {
            'id': self.id,
            'metric_type': self.metric_type,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'score': self.score,
            'previous_score': self.previous_score,
            'delta': self.delta,
            'trend': self.trend,
            'measured_at': self.measured_at.isoformat() if self.measured_at else None,
            'organization_id': self.organization_id
        }
