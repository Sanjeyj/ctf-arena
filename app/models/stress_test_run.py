"""
StressTestRun model - Phase 37 Strategic Cyber Resilience.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin
import datetime


class StressTestRun(db.Model, TimestampMixin, TenantMixin):
    """StressTestRun representation."""
    __tablename__ = 'stress_test_runs'

    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('stress_test_scenarios.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(32), default='pending', nullable=False)
    random_seed = db.Column(db.Integer, default=42, nullable=False)
    iteration_count = db.Column(db.Integer, default=1000, nullable=False)
    baseline_loss = db.Column(db.Float, default=0.0, nullable=False)
    stressed_loss = db.Column(db.Float, default=0.0, nullable=False)
    baseline_resilience = db.Column(db.Float, default=100.0, nullable=False)
    stressed_resilience = db.Column(db.Float, default=100.0, nullable=False)
    recovery_time_hours = db.Column(db.Float, default=4.0, nullable=False)
    risk_appetite_breached = db.Column(db.Boolean, default=False, nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    result_summary = db.Column(db.Text, nullable=True)

    scenario = db.relationship('StressTestScenario', backref=db.backref('runs', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<StressTestRun scenario_id={self.scenario_id} stressed_loss={self.stressed_loss}>'

    def to_dict(self):
        return {
            'id': self.id,
            'scenario_id': self.scenario_id,
            'status': self.status,
            'random_seed': self.random_seed,
            'iteration_count': self.iteration_count,
            'baseline_loss': self.baseline_loss,
            'stressed_loss': self.stressed_loss,
            'baseline_resilience': self.baseline_resilience,
            'stressed_resilience': self.stressed_resilience,
            'recovery_time_hours': self.recovery_time_hours,
            'risk_appetite_breached': self.risk_appetite_breached,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result_summary': self.result_summary,
            'organization_id': self.organization_id
        }
