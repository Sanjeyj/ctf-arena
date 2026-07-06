"""
TelemetrySource model - Phase 33 Cyber Platform Observability, Reliability & Operations Fabric.
Stores metadata for telemetry collectors/sources.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class TelemetrySource(db.Model, TimestampMixin, TenantMixin):
    """TelemetrySource model."""
    __tablename__ = 'telemetry_sources'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    source_type = db.Column(db.String(64), nullable=False)  # agent, metric_collector, trace_collector
    module_name = db.Column(db.String(64), nullable=False)  # lms, soc, cti, etc.
    status = db.Column(db.String(32), default='active', nullable=False)  # active, inactive, degraded
    collection_interval = db.Column(db.Integer, default=60, nullable=False)  # seconds
    last_collection_at = db.Column(db.DateTime, nullable=True)
    health_score = db.Column(db.Float, default=1.0, nullable=False)

    def __repr__(self):
        return f'<TelemetrySource {self.name!r} type={self.source_type} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'source_type': self.source_type,
            'module_name': self.module_name,
            'status': self.status,
            'collection_interval': self.collection_interval,
            'last_collection_at': self.last_collection_at.isoformat() if self.last_collection_at else None,
            'health_score': self.health_score,
            'organization_id': self.organization_id,
        }
