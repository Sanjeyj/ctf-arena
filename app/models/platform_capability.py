"""Phase 40 — Platform Capability Registry Model."""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class PlatformCapability(db.Model, TimestampMixin, TenantMixin):
    """Canonical registry of platform capabilities across all phases."""
    __tablename__ = 'platform_capabilities'

    MATURITY_MIN = 0.0
    MATURITY_MAX = 100.0

    STATUS_CHOICES = ('active', 'deprecated', 'experimental', 'retired')
    CATEGORY_CHOICES = (
        'risk', 'resilience', 'governance', 'operations', 'observability',
        'intelligence', 'validation', 'exposure', 'trust', 'assurance',
        'simulation', 'ai', 'federation', 'platform', 'certification',
        'release', 'mission_control',
    )

    id = db.Column(db.Integer, primary_key=True)
    capability_key = db.Column(db.String(120), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    phase_introduced = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(60), nullable=False, default='platform')
    description = db.Column(db.Text, nullable=True)
    owner_module = db.Column(db.String(120), nullable=True)
    service_reference = db.Column(db.String(200), nullable=True)
    route_prefix = db.Column(db.String(120), nullable=True)
    maturity_score = db.Column(db.Float, nullable=False, default=50.0)
    status = db.Column(db.String(30), nullable=False, default='active', index=True)

    # Tenant-unique constraint: capability_key per org
    __table_args__ = (
        db.UniqueConstraint('capability_key', 'organization_id',
                            name='uq_platform_capability_key_org'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'capability_key': self.capability_key,
            'name': self.name,
            'phase_introduced': self.phase_introduced,
            'category': self.category,
            'description': self.description,
            'owner_module': self.owner_module,
            'service_reference': self.service_reference,
            'route_prefix': self.route_prefix,
            'maturity_score': round(float(self.maturity_score or 50.0), 4),
            'status': self.status,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
