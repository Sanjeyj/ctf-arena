"""
SystemicDependency model — Phase 39: Systemic Cyber Risk, Collective Resilience
& Federated Governance Fabric.

Directed dependency edge between two SystemicRiskNodes.
Rejects self-edges, cross-tenant edges, and duplicates.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class SystemicDependency(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'systemic_dependencies'

    id = db.Column(db.Integer, primary_key=True)
    source_node_id = db.Column(db.Integer, db.ForeignKey('systemic_risk_nodes.id', ondelete='CASCADE'), nullable=False)
    target_node_id = db.Column(db.Integer, db.ForeignKey('systemic_risk_nodes.id', ondelete='CASCADE'), nullable=False)
    dependency_type = db.Column(db.String(64), nullable=False)
    # technical, vendor, cloud, identity, data, operational,
    # financial_simulation, coordination, intelligence, recovery
    dependency_strength = db.Column(db.Float, default=50.0)         # 0-100
    substitutability_score = db.Column(db.Float, default=50.0)      # 0=not substitutable, 100=easily substitutable
    recovery_dependency_score = db.Column(db.Float, default=50.0)   # 0-100
    propagation_probability = db.Column(db.Float, default=0.5)      # 0-1
    trust_dependency_score = db.Column(db.Float, default=50.0)      # 0-100
    status = db.Column(db.String(32), default='active')

    __table_args__ = (
        db.Index('ix_systemic_dep_org', 'organization_id'),
        db.Index('ix_systemic_dep_source', 'source_node_id'),
        db.Index('ix_systemic_dep_target', 'target_node_id'),
        db.UniqueConstraint('organization_id', 'source_node_id', 'target_node_id',
                            name='uq_systemic_dep_edge'),
    )

    def __repr__(self):
        return f'<SystemicDependency {self.source_node_id}->{self.target_node_id} type={self.dependency_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'source_node_id': self.source_node_id,
            'target_node_id': self.target_node_id,
            'dependency_type': self.dependency_type,
            'dependency_strength': self.dependency_strength,
            'substitutability_score': self.substitutability_score,
            'recovery_dependency_score': self.recovery_dependency_score,
            'propagation_probability': self.propagation_probability,
            'trust_dependency_score': self.trust_dependency_score,
            'status': self.status,
            'organization_id': self.organization_id,
        }
