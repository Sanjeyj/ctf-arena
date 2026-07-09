"""
RiskSimulationRun model - Phase 36 Cyber Risk Quantification.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin
import datetime


class RiskSimulationRun(db.Model, TimestampMixin, TenantMixin):
    """RiskSimulationRun representation."""
    __tablename__ = 'risk_simulation_runs'

    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('quantitative_risk_scenarios.id', ondelete='CASCADE'), nullable=False)
    simulation_type = db.Column(db.String(64), nullable=False)  # deterministic, monte_carlo_simulation
    iteration_count = db.Column(db.Integer, default=1000, nullable=False)
    random_seed = db.Column(db.Integer, default=42, nullable=False)
    status = db.Column(db.String(32), default='pending', nullable=False)
    expected_loss = db.Column(db.Float, default=0.0, nullable=False)
    median_loss = db.Column(db.Float, default=0.0, nullable=False)
    p90_loss = db.Column(db.Float, default=0.0, nullable=False)
    p95_loss = db.Column(db.Float, default=0.0, nullable=False)
    maximum_simulated_loss = db.Column(db.Float, default=0.0, nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    scenario = db.relationship('QuantitativeRiskScenario', backref=db.backref('simulation_runs', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<RiskSimulationRun scenario_id={self.scenario_id} expected_loss={self.expected_loss}>'

    def to_dict(self):
        return {
            'id': self.id,
            'scenario_id': self.scenario_id,
            'simulation_type': self.simulation_type,
            'iteration_count': self.iteration_count,
            'random_seed': self.random_seed,
            'status': self.status,
            'expected_loss': self.expected_loss,
            'median_loss': self.median_loss,
            'p90_loss': self.p90_loss,
            'p95_loss': self.p95_loss,
            'maximum_simulated_loss': self.maximum_simulated_loss,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'organization_id': self.organization_id
        }
