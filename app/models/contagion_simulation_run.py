"""
ContagionSimulationRun model — Phase 39: Systemic Cyber Risk, Collective Resilience
& Federated Governance Fabric.

Records the execution results of a contagion propagation simulation.
All results are simulation-only. No live systems are affected.
"""
import datetime
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class ContagionSimulationRun(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'contagion_simulation_runs'

    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('contagion_scenarios.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(32), default='pending')
    # pending, running, completed, failed
    iteration_count = db.Column(db.Integer, default=1)
    random_seed = db.Column(db.Integer, default=42)
    nodes_affected = db.Column(db.Integer, default=0)
    maximum_depth_reached = db.Column(db.Integer, default=0)
    aggregate_impact_score = db.Column(db.Float, default=0.0)      # 0-100
    collective_resilience_score = db.Column(db.Float, default=0.0) # 0-100
    estimated_recovery_hours = db.Column(db.Float, default=0.0)
    result_summary = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    events = db.relationship('ContagionEvent',
                             backref=db.backref('simulation_run', lazy='joined'),
                             cascade='all, delete-orphan', lazy='dynamic')

    __table_args__ = (
        db.Index('ix_contagion_run_org', 'organization_id'),
        db.Index('ix_contagion_run_scenario', 'scenario_id'),
    )

    def __repr__(self):
        return f'<ContagionSimulationRun scenario={self.scenario_id} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'scenario_id': self.scenario_id,
            'status': self.status,
            'iteration_count': self.iteration_count,
            'random_seed': self.random_seed,
            'nodes_affected': self.nodes_affected,
            'maximum_depth_reached': self.maximum_depth_reached,
            'aggregate_impact_score': self.aggregate_impact_score,
            'collective_resilience_score': self.collective_resilience_score,
            'estimated_recovery_hours': self.estimated_recovery_hours,
            'result_summary': self.result_summary,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'organization_id': self.organization_id,
        }
