"""
OperationsTimelineEvent model - Phase 33 Cyber Platform Observability, Reliability & Operations Fabric.
Chronological ledger of operational transitions, status updates, and incident progress.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class OperationsTimelineEvent(db.Model, TimestampMixin, TenantMixin):
    """OperationsTimelineEvent model."""
    __tablename__ = 'operations_timeline_events'

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('operational_incidents.id', ondelete='SET NULL'), nullable=True)
    event_type = db.Column(db.String(64), nullable=False)  # alert, incident_start, mitigation, resolution, chaos_start, health_degrade
    severity = db.Column(db.String(32), default='info', nullable=False)  # info, warning, error, critical
    description = db.Column(db.Text, nullable=False)
    source_service = db.Column(db.String(120), nullable=False)
    score_delta = db.Column(db.Float, default=0.0, nullable=False)
    event_time = db.Column(db.DateTime, nullable=False, index=True)
    metadata_json = db.Column(db.Text, nullable=True)  # JSON stored as string

    def __repr__(self):
        return f'<OperationsTimelineEvent type={self.event_type} severity={self.severity} time={self.event_time}>'

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'incident_id': self.incident_id,
            'event_type': self.event_type,
            'severity': self.severity,
            'description': self.description,
            'source_service': self.source_service,
            'score_delta': self.score_delta,
            'event_time': self.event_time.isoformat() if self.event_time else None,
            'metadata_json': json.loads(self.metadata_json) if self.metadata_json else {},
            'organization_id': self.organization_id,
        }
