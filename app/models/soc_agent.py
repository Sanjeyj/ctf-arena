"""
SocAgent model - Phase 21 AI SOC Analyst.
Manages configured autonomous security analysts.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class SocAgent(db.Model, TimestampMixin, TenantMixin):
    """AI SOC Analyst configurations."""
    __tablename__ = 'soc_agents'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    role = db.Column(db.String(80), default='analyst') # analyst, threat_hunter, incident_commander
    confidence = db.Column(db.Float, default=0.85)
    status = db.Column(db.String(32), default='idle') # idle, executing, paused
    model = db.Column(db.String(80), default='gemini-2.0-pro')
    last_run = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<SocAgent {self.name!r} role={self.role}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role,
            'confidence': self.confidence,
            'status': self.status,
            'model': self.model,
            'last_run': self.last_run.isoformat() if self.last_run else None
        }
