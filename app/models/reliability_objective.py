"""
ReliabilityObjective model - Phase 31 Cyber Platform Control Plane.
Stores simulated SLI/SLO definitions.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class ReliabilityObjective(db.Model, TimestampMixin, TenantMixin):
    """ReliabilityObjective model."""
    __tablename__ = 'reliability_objectives'

    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('platform_services.id', ondelete='CASCADE'), nullable=False, index=True)
    metric_name = db.Column(db.String(120), nullable=False)  # availability, response_time, simulation_success_rate, etc.
    target_value = db.Column(db.Float, nullable=False)
    current_value = db.Column(db.Float, default=1.0, nullable=False)
    measurement_window = db.Column(db.String(32), default='30d', nullable=False)
    error_budget = db.Column(db.Float, default=1.0, nullable=False)
    status = db.Column(db.String(32), default='compliant', nullable=False)  # compliant, breaching

    def __repr__(self):
        return f'<ReliabilityObjective metric={self.metric_name!r} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'service_id': self.service_id,
            'metric_name': self.metric_name,
            'target_value': self.target_value,
            'current_value': self.current_value,
            'measurement_window': self.measurement_window,
            'error_budget': self.error_budget,
            'status': self.status,
            'organization_id': self.organization_id,
        }
