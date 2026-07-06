"""
TraceRecord model - Phase 33 Cyber Platform Observability, Reliability & Operations Fabric.
Stores span and trace data for operations tracking.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class TraceRecord(db.Model, TimestampMixin, TenantMixin):
    """TraceRecord model."""
    __tablename__ = 'trace_records'

    id = db.Column(db.Integer, primary_key=True)
    trace_id = db.Column(db.String(64), nullable=False, index=True)
    span_id = db.Column(db.String(64), nullable=False)
    parent_span_id = db.Column(db.String(64), nullable=True)
    service_name = db.Column(db.String(120), nullable=False)
    operation_name = db.Column(db.String(120), nullable=False)
    duration_ms = db.Column(db.Float, default=0.0, nullable=False)
    status = db.Column(db.String(32), default='success', nullable=False)  # success, error
    started_at = db.Column(db.DateTime, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=False)
    metadata_json = db.Column(db.Text, nullable=True)  # JSON stored as string

    def __repr__(self):
        return f'<TraceRecord trace={self.trace_id!r} span={self.span_id!r} service={self.service_name!r}>'

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'trace_id': self.trace_id,
            'span_id': self.span_id,
            'parent_span_id': self.parent_span_id,
            'service_name': self.service_name,
            'operation_name': self.operation_name,
            'duration_ms': self.duration_ms,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'metadata_json': json.loads(self.metadata_json) if self.metadata_json else {},
            'organization_id': self.organization_id,
        }
