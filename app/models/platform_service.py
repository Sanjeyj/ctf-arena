"""
PlatformService model - Phase 31 Cyber Platform Control Plane.
Registry of logical services and platform capabilities.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class PlatformService(db.Model, TimestampMixin, TenantMixin):
    """PlatformService model."""
    __tablename__ = 'platform_services'

    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(120), nullable=False)
    service_type = db.Column(db.String(64), nullable=False)  # soc, cti, lms, cyber_range, grc, cloud, resilience, command, universe, ai
    version = db.Column(db.String(32), default='1.0.0', nullable=False)
    status = db.Column(db.String(32), default='healthy', nullable=False)  # healthy, degraded, unavailable, maintenance, unknown
    health_score = db.Column(db.Float, default=1.0, nullable=False)
    criticality = db.Column(db.String(32), default='medium', nullable=False)  # low, medium, high, critical
    owner = db.Column(db.String(120), nullable=True)
    last_heartbeat = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<PlatformService {self.service_name!r} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'service_name': self.service_name,
            'service_type': self.service_type,
            'version': self.version,
            'status': self.status,
            'health_score': self.health_score,
            'criticality': self.criticality,
            'owner': self.owner,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'organization_id': self.organization_id,
        }
