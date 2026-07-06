"""
OperationalIncident model - Phase 33 Cyber Platform Observability, Reliability & Operations Fabric.
Stores correlated platform outages, failures, or alerts.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class OperationalIncident(db.Model, TimestampMixin, TenantMixin):
    """OperationalIncident model."""
    __tablename__ = 'operational_incidents'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    severity = db.Column(db.String(32), default='medium', nullable=False)  # low, medium, high, critical
    status = db.Column(db.String(32), default='active', nullable=False)  # active, mitigating, resolved
    source_module = db.Column(db.String(64), nullable=False)  # lms, soc, cti, etc.
    affected_services_json = db.Column(db.Text, nullable=True)  # JSON stored as string
    root_cause_summary = db.Column(db.Text, nullable=True)
    impact_summary = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime, nullable=False)
    resolved_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<OperationalIncident {self.title!r} severity={self.severity} status={self.status}>'

    def to_dict(self):
        import json
        return {
            'id': self.id,
            'title': self.title,
            'severity': self.severity,
            'status': self.status,
            'source_module': self.source_module,
            'affected_services_json': json.loads(self.affected_services_json) if self.affected_services_json else [],
            'root_cause_summary': self.root_cause_summary,
            'impact_summary': self.impact_summary,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'organization_id': self.organization_id,
        }
