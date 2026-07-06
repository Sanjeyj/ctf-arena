"""
TelemetryMetric model - Phase 33 Cyber Platform Observability, Reliability & Operations Fabric.
Stores individual metric snapshots.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class TelemetryMetric(db.Model, TimestampMixin, TenantMixin):
    """TelemetryMetric model."""
    __tablename__ = 'telemetry_metrics'

    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('telemetry_sources.id', ondelete='CASCADE'), nullable=False)
    metric_name = db.Column(db.String(120), nullable=False, index=True)
    metric_type = db.Column(db.String(64), nullable=False)  # counter, gauge, histogram
    metric_value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(32), nullable=True)
    dimensions_json = db.Column(db.Text, nullable=True)  # JSON stored as string
    recorded_at = db.Column(db.DateTime, nullable=False, index=True)

    def __repr__(self):
        return f'<TelemetryMetric {self.metric_name!r} value={self.metric_value}>'

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'source_id': self.source_id,
            'metric_name': self.metric_name,
            'metric_type': self.metric_type,
            'metric_value': self.metric_value,
            'unit': self.unit,
            'dimensions_json': json.loads(self.dimensions_json) if self.dimensions_json else {},
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'organization_id': self.organization_id,
        }
