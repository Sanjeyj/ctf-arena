"""
AutonomousAgent model - Phase 26 Autonomous Cyber Enterprise.
Represents autonomous software agents deployed inside the security orchestration mesh.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class AutonomousAgent(db.Model, TimestampMixin, TenantMixin):
    """Autonomous Agent profile."""
    __tablename__ = 'autonomous_agents'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(64), nullable=False) # SOC Agent, CTI Agent, Compliance Agent, etc.
    model = db.Column(db.String(64), nullable=True) # AI model name
    confidence = db.Column(db.Float, default=0.9, nullable=False)
    status = db.Column(db.String(32), default='idle', nullable=False) # idle, running, offline
    last_execution = db.Column(db.DateTime, nullable=True)

    # Relationships
    tasks = db.relationship('AgentTask', back_populates='agent', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<AutonomousAgent {self.name!r} role={self.role}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role,
            'model': self.model,
            'confidence': self.confidence,
            'status': self.status,
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'organization_id': self.organization_id
        }
