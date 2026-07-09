"""Phase 40 — Capability Dependency Model."""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class CapabilityDependency(db.Model, TimestampMixin, TenantMixin):
    """Directed dependency edge between two platform capabilities."""
    __tablename__ = 'capability_dependencies'

    DEPENDENCY_TYPES = (
        'data_flow', 'service_call', 'schema_reference', 'hook_chain',
        'route_delegation', 'ai_pipeline', 'audit_chain',
    )
    CRITICALITY_LEVELS = ('low', 'medium', 'high', 'critical')
    STATUS_CHOICES = ('active', 'deprecated', 'pending')

    id = db.Column(db.Integer, primary_key=True)
    source_capability_id = db.Column(
        db.Integer, db.ForeignKey('platform_capabilities.id', ondelete='CASCADE'),
        nullable=False, index=True,
    )
    target_capability_id = db.Column(
        db.Integer, db.ForeignKey('platform_capabilities.id', ondelete='CASCADE'),
        nullable=False, index=True,
    )
    dependency_type = db.Column(db.String(60), nullable=False, default='service_call')
    criticality = db.Column(db.String(30), nullable=False, default='medium')
    coupling_score = db.Column(db.Float, nullable=False, default=0.5)
    health_impact_score = db.Column(db.Float, nullable=False, default=0.5)
    status = db.Column(db.String(30), nullable=False, default='active', index=True)
    notes = db.Column(db.Text, nullable=True)

    # No self-edges, no duplicate active edges per tenant
    __table_args__ = (
        db.UniqueConstraint(
            'source_capability_id', 'target_capability_id', 'organization_id',
            name='uq_cap_dep_src_tgt_org',
        ),
        db.CheckConstraint(
            'source_capability_id != target_capability_id',
            name='ck_cap_dep_no_self_edge',
        ),
    )

    source_capability = db.relationship(
        'PlatformCapability',
        foreign_keys=[source_capability_id],
        backref=db.backref('outgoing_dependencies', lazy='dynamic'),
    )
    target_capability = db.relationship(
        'PlatformCapability',
        foreign_keys=[target_capability_id],
        backref=db.backref('incoming_dependencies', lazy='dynamic'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'source_capability_id': self.source_capability_id,
            'target_capability_id': self.target_capability_id,
            'dependency_type': self.dependency_type,
            'criticality': self.criticality,
            'coupling_score': round(float(self.coupling_score or 0.5), 4),
            'health_impact_score': round(float(self.health_impact_score or 0.5), 4),
            'status': self.status,
            'notes': self.notes,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
