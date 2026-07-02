"""
Alert model — Phase 18 SOC Platform / SIEM Engine.
Represents a SIEM-generated security alert.
"""
import datetime
from app.extensions import db
from app.models.mixins import TimestampMixin


ALERT_SEVERITIES = ['info', 'low', 'medium', 'high', 'critical']
ALERT_STATUSES = ['new', 'acknowledged', 'investigating', 'resolved', 'false_positive']
ALERT_EVENT_TYPES = ['authentication', 'network', 'endpoint', 'web', 'cloud', 'other']


class Alert(TimestampMixin, db.Model):
    """SIEM-generated security alert."""
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text, default='')
    severity = db.Column(db.String(16), default='medium')
    status = db.Column(db.String(24), default='new')
    event_type = db.Column(db.String(32), default='other')

    # Network context
    source_ip = db.Column(db.String(64), nullable=True)
    dest_ip = db.Column(db.String(64), nullable=True)
    source_port = db.Column(db.Integer, nullable=True)
    dest_port = db.Column(db.Integer, nullable=True)

    # Raw event data (JSON string)
    raw_event = db.Column(db.Text, default='')

    # Assignment
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_at = db.Column(db.DateTime, nullable=True)

    # MITRE mapping (simulated)
    mitre_tactic = db.Column(db.String(64), nullable=True)
    mitre_technique = db.Column(db.String(64), nullable=True)

    # AI triage fields
    ai_severity_recommendation = db.Column(db.String(16), nullable=True)
    ai_analysis = db.Column(db.Text, nullable=True)

    # Resolution
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolution_notes = db.Column(db.Text, default='')

    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)

    # Relationships
    assignee = db.relationship('User', foreign_keys=[assigned_to], lazy='joined',
                               primaryjoin='Alert.assigned_to == User.id')
    detections = db.relationship('Detection', backref='alert', lazy='dynamic',
                                 foreign_keys='Detection.alert_id')

    def __repr__(self):
        return f'<Alert {self.title!r} sev={self.severity} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity,
            'status': self.status,
            'event_type': self.event_type,
            'source_ip': self.source_ip,
            'dest_ip': self.dest_ip,
            'mitre_tactic': self.mitre_tactic,
            'mitre_technique': self.mitre_technique,
            'ai_severity_recommendation': self.ai_severity_recommendation,
            'assigned_to': self.assigned_to,
            'created_at': self.created_at.isoformat() if hasattr(self, 'created_at') and self.created_at else None,
        }
