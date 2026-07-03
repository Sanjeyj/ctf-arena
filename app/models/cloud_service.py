"""
CloudService model - Phase 24 Global Cyber Security Cloud.
Tracks deployed service instances and status mappings.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class CloudService(db.Model, TimestampMixin, TenantMixin):
    """Regional service running status mapper."""
    __tablename__ = 'cloud_services'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    service_type = db.Column(db.String(64), default='SOC') # SOC, CTI, LMS, SIEM
    status = db.Column(db.String(32), default='running') # running, paused, maintenance

    def __repr__(self):
        return f'<CloudService {self.name!r} type={self.service_type} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'service_type': self.service_type,
            'status': self.status
        }
