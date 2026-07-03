"""
Playbook model - Phase 21 Playbook Engine.
Defines dynamic automated orchestration actions.
"""
import json
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class Playbook(db.Model, TimestampMixin, TenantMixin):
    """Orchestration playbook profile."""
    __tablename__ = 'playbooks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)
    trigger_type = db.Column(db.String(64), default='manual') # alert_severity, event_type, manual
    steps_json = db.Column('steps', db.Text, default='[]')
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Playbook {self.name!r} trigger={self.trigger_type}>'

    def to_dict(self):
        try:
            steps = json.loads(self.steps_json) if self.steps_json else []
        except Exception:
            steps = []
            
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'trigger_type': self.trigger_type,
            'steps': steps,
            'is_active': self.is_active
        }
