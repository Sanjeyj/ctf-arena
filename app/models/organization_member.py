import datetime
from app.extensions import db
from app.models.mixins import TimestampMixin

MEMBER_ROLES = ('owner', 'administrator', 'manager', 'instructor', 'member', 'read_only')

# Role permission hierarchy — higher index = more privileged
ROLE_HIERARCHY = {role: idx for idx, role in enumerate(MEMBER_ROLES)}


class OrganizationMember(db.Model, TimestampMixin):
    """Membership record linking a User to an Organization with a specific role."""
    __tablename__ = 'organization_members'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    role = db.Column(db.String(20), default='member', nullable=False)
    invited_by = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True
    )
    joined_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Unique membership per org
    __table_args__ = (
        db.UniqueConstraint('organization_id', 'user_id', name='uq_org_member'),
    )

    organization = db.relationship('Organization', back_populates='members')
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('org_memberships', lazy='dynamic'))
    inviter = db.relationship('User', foreign_keys=[invited_by])

    def can(self, required_role: str) -> bool:
        """True if this member's role is at least as privileged as required_role."""
        return ROLE_HIERARCHY.get(self.role, -1) <= ROLE_HIERARCHY.get(required_role, 99)

    def __repr__(self):
        return f'<OrganizationMember user={self.user_id} org={self.organization_id} role={self.role}>'
