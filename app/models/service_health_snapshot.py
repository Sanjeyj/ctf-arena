"""
ServiceHealthSnapshot model - Phase 33 Cyber Platform Observability, Reliability & Operations Fabric.
Stores health status history for registered platform services.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class ServiceHealthSnapshot(db.Model, TimestampMixin, TenantMixin):
    """ServiceHealthSnapshot model."""
    __tablename__ = 'service_health_snapshots'

    id = db.Column(db.Integer, primary_key=True)
    platform_service_id = db.Column(db.Integer, db.ForeignKey('platform_services.id', ondelete='CASCADE'), nullable=False)
    health_score = db.Column(db.Float, default=100.0, nullable=False)
    availability = db.Column(db.Float, default=1.0, nullable=False)  # 0.0 to 1.0
    latency_ms = db.Column(db.Float, default=0.0, nullable=False)
    error_rate = db.Column(db.Float, default=0.0, nullable=False)  # 0.0 to 1.0
    saturation = db.Column(db.Float, default=0.0, nullable=False)  # 0.0 to 1.0
    status = db.Column(db.String(32), default='healthy', nullable=False)  # healthy, warning, degraded, critical
    measured_at = db.Column(db.DateTime, nullable=False, index=True)

    def __repr__(self):
        return f'<ServiceHealthSnapshot service_id={self.platform_service_id} health={self.health_score}>'

    def to_dict(self):
        return {
            'id': self.id,
            'platform_service_id': self.platform_service_id,
            'health_score': self.health_score,
            'availability': self.availability,
            'latency_ms': self.latency_ms,
            'error_rate': self.error_rate,
            'saturation': self.saturation,
            'status': self.status,
            'measured_at': self.measured_at.isoformat() if self.measured_at else None,
            'organization_id': self.organization_id,
        }
