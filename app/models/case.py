"""
Case model — Phase 18 SOC Platform / Case Management.
Tracks an incident investigation from open to close.
"""
import datetime
from app.extensions import db
from app.models.mixins import TimestampMixin


CASE_PRIORITIES = ['low', 'medium', 'high', 'critical']
CASE_STATUSES = ['open', 'investigating', 'contained', 'resolved', 'closed']

# Valid state machine transitions
CASE_TRANSITIONS = {
    'open': ['investigating', 'closed'],
    'investigating': ['contained', 'resolved', 'open'],
    'contained': ['resolved', 'investigating'],
    'resolved': ['closed', 'open'],
    'closed': [],
}


class Case(TimestampMixin, db.Model):
    """Incident investigation case."""
    __tablename__ = 'cases'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text, default='')
    priority = db.Column(db.String(16), default='medium')
    status = db.Column(db.String(24), default='open')

    # Analyst assignment
    analyst_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_at = db.Column(db.DateTime, nullable=True)

    # Case content (JSON-serialized lists)
    notes = db.Column(db.Text, default='[]')
    evidence = db.Column(db.Text, default='[]')

    # Linked alert
    alert_id = db.Column(db.Integer, db.ForeignKey('alerts.id'), nullable=True)

    # MITRE context
    mitre_tactic = db.Column(db.String(64), nullable=True)
    mitre_technique = db.Column(db.String(64), nullable=True)

    # AI summary
    ai_summary = db.Column(db.Text, nullable=True)
    ai_guidance = db.Column(db.Text, nullable=True)

    # Resolution
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolution_summary = db.Column(db.Text, default='')

    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)

    # Relationships
    analyst = db.relationship('User', foreign_keys=[analyst_id], lazy='joined',
                              primaryjoin='Case.analyst_id == User.id')
    alert = db.relationship('Alert', foreign_keys=[alert_id], lazy='joined')

    def __repr__(self):
        return f'<Case {self.title!r} priority={self.priority} status={self.status}>'

    def can_transition_to(self, new_status):
        return new_status in CASE_TRANSITIONS.get(self.status, [])

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'analyst_id': self.analyst_id,
            'alert_id': self.alert_id,
            'mitre_tactic': self.mitre_tactic,
            'mitre_technique': self.mitre_technique,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'created_at': self.created_at.isoformat() if hasattr(self, 'created_at') and self.created_at else None,
        }
