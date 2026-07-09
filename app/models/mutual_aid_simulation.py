"""
MutualAidSimulation model — Phase 39: Systemic Cyber Risk, Collective Resilience
& Federated Governance Fabric.

Simulation-only mutual aid capacity allocation record.
NO real communication or resource dispatch occurs.
Human approval is required before allocation is considered active.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class MutualAidSimulation(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'mutual_aid_simulations'

    id = db.Column(db.Integer, primary_key=True)
    simulation_run_id = db.Column(db.Integer, db.ForeignKey('contagion_simulation_runs.id', ondelete='SET NULL'), nullable=True)
    provider_node_id = db.Column(db.Integer, db.ForeignKey('systemic_risk_nodes.id', ondelete='SET NULL'), nullable=True)
    recipient_node_id = db.Column(db.Integer, db.ForeignKey('systemic_risk_nodes.id', ondelete='SET NULL'), nullable=True)
    assistance_type = db.Column(db.String(64), nullable=False)
    # recovery_capacity, resilience_boost, coordination_support,
    # technical_assistance, shared_control, information_sharing
    capacity_available = db.Column(db.Float, default=100.0)     # 0-100
    capacity_allocated = db.Column(db.Float, default=0.0)       # 0 <= allocated <= available
    estimated_recovery_gain = db.Column(db.Float, default=0.0)  # >= 0
    allocation_score = db.Column(db.Float, default=0.0)         # 0-100
    approval_status = db.Column(db.String(32), default='pending')
    # pending, approved, rejected
    status = db.Column(db.String(32), default='simulated')
    # simulated, allocated_simulation, cancelled

    provider_node = db.relationship('SystemicRiskNode', foreign_keys=[provider_node_id])
    recipient_node = db.relationship('SystemicRiskNode', foreign_keys=[recipient_node_id])

    __table_args__ = (
        db.Index('ix_mutual_aid_org', 'organization_id'),
        db.Index('ix_mutual_aid_run', 'simulation_run_id'),
    )

    def __repr__(self):
        return f'<MutualAidSimulation provider={self.provider_node_id} recipient={self.recipient_node_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'simulation_run_id': self.simulation_run_id,
            'provider_node_id': self.provider_node_id,
            'recipient_node_id': self.recipient_node_id,
            'assistance_type': self.assistance_type,
            'capacity_available': self.capacity_available,
            'capacity_allocated': self.capacity_allocated,
            'estimated_recovery_gain': self.estimated_recovery_gain,
            'allocation_score': self.allocation_score,
            'approval_status': self.approval_status,
            'status': self.status,
            'organization_id': self.organization_id,
        }
