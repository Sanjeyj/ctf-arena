from app.extensions import db
from app.models.mixins import TimestampMixin, UUIDMixin, SoftDeleteMixin

PLAN_TYPES = ('free', 'professional', 'enterprise')
ORG_STATUSES = ('active', 'suspended', 'deleted')

# Default quota limits per plan
PLAN_QUOTAS = {
    'free': {
        'max_users': 100,
        'max_competitions': 1,
        'max_challenges': 50,
        'max_containers': 5,
        'max_ai_tokens': 10_000,
        'max_storage_mb': 512,
    },
    'professional': {
        'max_users': 1000,
        'max_competitions': 10,
        'max_challenges': 500,
        'max_containers': 50,
        'max_ai_tokens': 500_000,
        'max_storage_mb': 10_240,
    },
    'enterprise': {
        'max_users': -1,           # -1 = unlimited
        'max_competitions': -1,
        'max_challenges': -1,
        'max_containers': -1,
        'max_ai_tokens': -1,
        'max_storage_mb': -1,
    },
}


class Organization(db.Model, TimestampMixin, UUIDMixin, SoftDeleteMixin):
    """Top-level tenant entity. Each org is an isolated workspace."""
    __tablename__ = 'organizations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False, index=True)  # subdomain key

    # Ownership
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)

    # Plan
    plan_type = db.Column(db.String(20), default='free', nullable=False)  # free | professional | enterprise
    status = db.Column(db.String(20), default='active', nullable=False, index=True)  # active | suspended | deleted

    # Custom quota overrides (NULL = use plan defaults)
    max_users = db.Column(db.Integer, nullable=True)
    max_competitions = db.Column(db.Integer, nullable=True)
    max_challenges = db.Column(db.Integer, nullable=True)
    max_containers = db.Column(db.Integer, nullable=True)
    max_ai_tokens = db.Column(db.Integer, nullable=True)
    max_storage_mb = db.Column(db.Integer, nullable=True)

    # Relationships
    owner = db.relationship('User', foreign_keys=[owner_id], backref=db.backref('owned_organizations', lazy='dynamic'))
    members = db.relationship('OrganizationMember', back_populates='organization', cascade='all, delete-orphan', lazy='dynamic')
    settings = db.relationship('OrganizationSetting', back_populates='organization', cascade='all, delete-orphan', lazy='dynamic')
    billing = db.relationship('OrganizationBilling', back_populates='organization', uselist=False, cascade='all, delete-orphan')
    audit_logs = db.relationship('OrganizationAuditLog', back_populates='organization', cascade='all, delete-orphan', lazy='dynamic')

    def get_quota(self, resource: str) -> int:
        """Return effective quota for a resource; falls back to plan default."""
        override = getattr(self, f'max_{resource}', None)
        if override is not None:
            return override
        return PLAN_QUOTAS.get(self.plan_type, PLAN_QUOTAS['free']).get(f'max_{resource}', 0)

    def __repr__(self):
        return f'<Organization {self.slug} ({self.plan_type})>'
