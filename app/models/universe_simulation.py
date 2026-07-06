"""
UniverseSimulation model - Phase 30 Unified Cyber Defense Universe.
Tracks individual simulation executions.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class UniverseSimulation(db.Model, TimestampMixin, TenantMixin):
    """Universe simulation model."""
    __tablename__ = 'universe_simulations'

    id = db.Column(db.Integer, primary_key=True)
    universe_id = db.Column(db.Integer, db.ForeignKey('defense_universes.id', ondelete='CASCADE'), nullable=False, index=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('universe_scenarios.id', ondelete='CASCADE'), nullable=False, index=True)
    status = db.Column(db.String(32), default='pending', nullable=False)  # pending, running, complete, failed
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    initial_score = db.Column(db.Float, default=0.0, nullable=False)
    final_score = db.Column(db.Float, default=0.0, nullable=False)
    result_summary = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<UniverseSimulation id={self.id} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'universe_id': self.universe_id,
            'scenario_id': self.scenario_id,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'initial_score': self.initial_score,
            'final_score': self.final_score,
            'result_summary': self.result_summary,
            'organization_id': self.organization_id,
        }
