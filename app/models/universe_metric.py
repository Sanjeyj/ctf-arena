"""
UniverseMetric model - Phase 30 Unified Cyber Defense Universe.
Stores posture measurements over time.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class UniverseMetric(db.Model, TimestampMixin, TenantMixin):
    """Universe metric model."""
    __tablename__ = 'universe_metrics'

    id = db.Column(db.Integer, primary_key=True)
    universe_id = db.Column(db.Integer, db.ForeignKey('defense_universes.id', ondelete='CASCADE'), nullable=False, index=True)
    metric_type = db.Column(db.String(64), nullable=False)  # readiness, risk, resilience, domain_health
    metric_value = db.Column(db.Float, nullable=False)
    domain = db.Column(db.String(64), nullable=True)
    measured_at = db.Column(db.DateTime, nullable=False, index=True)

    def __repr__(self):
        return f'<UniverseMetric type={self.metric_type} value={self.metric_value}>'

    def to_dict(self):
        return {
            'id': self.id,
            'universe_id': self.universe_id,
            'metric_type': self.metric_type,
            'metric_value': self.metric_value,
            'domain': self.domain,
            'measured_at': self.measured_at.isoformat() if self.measured_at else None,
            'organization_id': self.organization_id,
        }
