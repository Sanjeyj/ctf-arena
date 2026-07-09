"""
ContagionEvent model — Phase 39: Systemic Cyber Risk, Collective Resilience
& Federated Governance Fabric.

Records a single propagation step within a contagion simulation run.
Events are ordered by event_sequence and event_time for deterministic replay.
"""
import datetime
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class ContagionEvent(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'contagion_events'

    id = db.Column(db.Integer, primary_key=True)
    simulation_run_id = db.Column(db.Integer, db.ForeignKey('contagion_simulation_runs.id', ondelete='CASCADE'), nullable=False)
    source_node_id = db.Column(db.Integer, db.ForeignKey('systemic_risk_nodes.id', ondelete='SET NULL'), nullable=True)
    target_node_id = db.Column(db.Integer, db.ForeignKey('systemic_risk_nodes.id', ondelete='SET NULL'), nullable=True)
    event_sequence = db.Column(db.Integer, nullable=False, default=0)
    event_type = db.Column(db.String(64), nullable=False)
    # initial_failure, dependency_propagation, control_block,
    # resilience_absorption, recovery, isolation_simulation, collective_assistance
    propagation_probability = db.Column(db.Float, default=0.0)  # 0-1
    impact_delta = db.Column(db.Float, default=0.0)             # 0-100
    resilience_delta = db.Column(db.Float, default=0.0)         # can be negative
    description = db.Column(db.Text, nullable=True)
    event_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    metadata_json = db.Column(db.Text, default='{}')

    source_node = db.relationship('SystemicRiskNode', foreign_keys=[source_node_id])
    target_node = db.relationship('SystemicRiskNode', foreign_keys=[target_node_id])

    __table_args__ = (
        db.Index('ix_contagion_event_org', 'organization_id'),
        db.Index('ix_contagion_event_run', 'simulation_run_id'),
        db.Index('ix_contagion_event_seq', 'simulation_run_id', 'event_sequence'),
        db.Index('ix_contagion_event_time', 'event_time'),
    )

    def __repr__(self):
        return f'<ContagionEvent run={self.simulation_run_id} seq={self.event_sequence} type={self.event_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'simulation_run_id': self.simulation_run_id,
            'source_node_id': self.source_node_id,
            'target_node_id': self.target_node_id,
            'event_sequence': self.event_sequence,
            'event_type': self.event_type,
            'propagation_probability': self.propagation_probability,
            'impact_delta': self.impact_delta,
            'resilience_delta': self.resilience_delta,
            'description': self.description,
            'event_time': self.event_time.isoformat() if self.event_time else None,
            'organization_id': self.organization_id,
        }
