"""
SharedIOC model - Phase 23 Global Threat Exchange.
Threat indicators shared among trust partners.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class SharedIOC(db.Model, TimestampMixin, TenantMixin):
    """Aggregated threat intelligence indicator shared cross-tenant."""
    __tablename__ = 'shared_iocs'

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(256), nullable=False, index=True)
    ioc_type = db.Column(db.String(64), default='IP') # IP, domain, URL, file_hash, Sigma, YARA, research_report
    trust_level = db.Column(db.String(32), default='community') # community, verified, trusted
    shared_by_org_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True)

    # Relationships
    sharing_org = db.relationship('Organization', foreign_keys=[shared_by_org_id])

    def __repr__(self):
        return f'<SharedIOC value={self.value!r} type={self.ioc_type} trust={self.trust_level}>'

    def to_dict(self):
        return {
            'id': self.id,
            'value': self.value,
            'ioc_type': self.ioc_type,
            'trust_level': self.trust_level,
            'shared_by_org_id': self.shared_by_org_id
        }
