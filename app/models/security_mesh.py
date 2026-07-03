"""
SecurityMesh model - Phase 24 Global Cyber Security Cloud.
Details cross-region trust federation links status metrics.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class SecurityMesh(db.Model, TimestampMixin, TenantMixin):
    """Regional trust federation connection links."""
    __tablename__ = 'security_meshes'

    id = db.Column(db.Integer, primary_key=True)
    source_region = db.Column(db.String(64), nullable=False, index=True)
    destination_region = db.Column(db.String(64), nullable=False, index=True)
    trust_level = db.Column(db.String(32), default='trusted')
    status = db.Column(db.String(32), default='active') # active, degraded, offline

    def __repr__(self):
        return f'<SecurityMesh {self.source_region}->{self.destination_region} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'source_region': self.source_region,
            'destination_region': self.destination_region,
            'trust_level': self.trust_level,
            'status': self.status
        }
