from app.extensions import db
from app.models.mixins import TimestampMixin


class OrganizationSetting(db.Model, TimestampMixin):
    """Per-organization key-value configuration store."""
    __tablename__ = 'organization_settings'

    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(
        db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    key = db.Column(db.String(100), nullable=False)
    value = db.Column(db.Text, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('organization_id', 'key', name='uq_org_setting_key'),
    )

    organization = db.relationship('Organization', back_populates='settings')

    def __repr__(self):
        return f'<OrganizationSetting org={self.organization_id} {self.key}={self.value!r}>'
