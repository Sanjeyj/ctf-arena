"""
IncidentCommander model - Phase 21 AI Incident Commander.
Manages incident response automated timelines and lesson logging files.
"""
import json
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class IncidentCommander(db.Model, TimestampMixin, TenantMixin):
    """AI Incident Commander workflow coordinator."""
    __tablename__ = 'incident_commanders'

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(32), default='active') # active, completed
    current_phase = db.Column(db.String(32), default='contain') # contain, eradicate, recover, postmortem
    timeline_events_json = db.Column('timeline_events', db.Text, default='[]')
    ir_report = db.Column(db.Text, nullable=True)
    lessons_learned = db.Column(db.Text, nullable=True)

    # Relationships
    incident = db.relationship('Incident', backref=db.backref('commander', uselist=False, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<IncidentCommander id={self.id} phase={self.current_phase}>'

    def to_dict(self):
        try:
            events = json.loads(self.timeline_events_json) if self.timeline_events_json else []
        except Exception:
            events = []
            
        return {
            'id': self.id,
            'incident_id': self.incident_id,
            'status': self.status,
            'current_phase': self.current_phase,
            'timeline_events': events,
            'ir_report': self.ir_report,
            'lessons_learned': self.lessons_learned
        }
