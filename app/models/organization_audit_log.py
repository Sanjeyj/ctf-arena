import json
from app.extensions import db
from app.models.mixins import TimestampMixin

AUDIT_ACTIONS = (
    'org_created', 'org_updated', 'org_suspended', 'org_deleted',
    'member_invited', 'member_removed', 'member_role_changed',
    'plan_changed', 'billing_status_changed',
    'competition_created', 'competition_deleted',
    'setting_changed',
)


class OrganizationAuditLog(db.Model, TimestampMixin):
    """Immutable audit trail for all organization-scoped events."""
    __tablename__ = 'organization_audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True, index=True
    )

    action = db.Column(db.String(60), nullable=False, index=True)
    resource_type = db.Column(db.String(60), nullable=True)   # e.g. 'user', 'competition'
    resource_id = db.Column(db.Integer, nullable=True)

    ip_address = db.Column(db.String(45), nullable=True)
    _details = db.Column('details', db.Text, nullable=True)

    organization = db.relationship('Organization', back_populates='audit_logs')
    actor = db.relationship('User', foreign_keys=[user_id])

    @property
    def details(self) -> dict:
        if self._details:
            try:
                return json.loads(self._details)
            except Exception:
                return {}
        return {}

    @details.setter
    def details(self, value: dict):
        self._details = json.dumps(value or {})

    def __repr__(self):
        return f'<OrgAuditLog org={self.organization_id} action={self.action}>'
