"""
OrganizationTrust model - Phase 20 Federation.
Tracks partner trust profiles, pending/active connections, and capability grants.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin

class OrganizationTrust(db.Model, TimestampMixin):
    """Federated trust bridge between organization tenants."""
    __tablename__ = 'organization_trusts'

    id = db.Column(db.Integer, primary_key=True)
    source_org_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    target_org_id = db.Column(db.Integer, db.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    relationship = db.Column(db.String(32), default='pending') # trusted, blocked, pending
    capabilities = db.Column(db.Text, nullable=True) # comma-separated list of granted capabilities

    # Relationships
    source_org = db.relationship('Organization', foreign_keys=[source_org_id], backref='trusts_initiated')
    target_org = db.relationship('Organization', foreign_keys=[target_org_id], backref='trusts_received')

    def __repr__(self):
        return f'<OrganizationTrust {self.source_org_id} -> {self.target_org_id} status={self.relationship}>'

    def to_dict(self):
        return {
            'id': self.id,
            'source_org_id': self.source_org_id,
            'target_org_id': self.target_org_id,
            'relationship': self.relationship,
            'capabilities': [c.strip() for c in self.capabilities.split(',')] if self.capabilities else []
        }
