"""
Runbook model - Phase 22 Security Knowledge Hub.
Stores executable runbooks steps templates.
"""
import json
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class Runbook(db.Model, TimestampMixin, TenantMixin):
    """Playbook guide runbook element."""
    __tablename__ = 'runbooks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    category = db.Column(db.String(80), default='SOC')
    steps_json = db.Column('steps', db.Text, default='[]')

    def __repr__(self):
        return f'<Runbook {self.name!r}>'

    def to_dict(self):
        try:
            steps = json.loads(self.steps_json) if self.steps_json else []
        except Exception:
            steps = []
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'steps': steps
        }
