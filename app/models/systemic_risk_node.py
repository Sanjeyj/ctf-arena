"""
SystemicRiskNode model — Phase 39: Systemic Cyber Risk, Collective Resilience
& Federated Governance Fabric.

Graph projection referencing an existing platform resource.
Does NOT duplicate source records — acts as an analytical overlay node.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class SystemicRiskNode(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'systemic_risk_nodes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False)
    node_type = db.Column(db.String(64), nullable=False)
    # organization, service, vendor, cloud_region, sector, platform,
    # shared_dependency, coordination_center
    reference_type = db.Column(db.String(64), nullable=True)
    # Optional back-reference to a source model (e.g. PlatformService)
    reference_id = db.Column(db.Integer, nullable=True)
    sector = db.Column(db.String(120), nullable=True)
    region = db.Column(db.String(120), nullable=True)
    criticality_score = db.Column(db.Float, default=50.0)     # 0-100
    dependency_score = db.Column(db.Float, default=50.0)      # 0-100
    concentration_score = db.Column(db.Float, default=50.0)   # 0-100
    resilience_score = db.Column(db.Float, default=50.0)      # 0-100
    status = db.Column(db.String(32), default='active')
    # active, degraded_simulation, isolated_simulation, recovery_simulation, inactive

    # Relationships
    outbound_dependencies = db.relationship(
        'SystemicDependency',
        foreign_keys='SystemicDependency.source_node_id',
        backref=db.backref('source_node', lazy='joined'),
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    inbound_dependencies = db.relationship(
        'SystemicDependency',
        foreign_keys='SystemicDependency.target_node_id',
        backref=db.backref('target_node', lazy='joined'),
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    __table_args__ = (
        db.Index('ix_systemic_risk_nodes_org', 'organization_id'),
        db.Index('ix_systemic_risk_nodes_ref', 'organization_id', 'reference_type', 'reference_id'),
        db.UniqueConstraint('organization_id', 'reference_type', 'reference_id',
                            name='uq_systemic_risk_node_ref'),
    )

    def __repr__(self):
        return f'<SystemicRiskNode {self.name!r} type={self.node_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'node_type': self.node_type,
            'reference_type': self.reference_type,
            'reference_id': self.reference_id,
            'sector': self.sector,
            'region': self.region,
            'criticality_score': self.criticality_score,
            'dependency_score': self.dependency_score,
            'concentration_score': self.concentration_score,
            'resilience_score': self.resilience_score,
            'status': self.status,
            'organization_id': self.organization_id,
        }
