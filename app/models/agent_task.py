"""
AgentTask model - Phase 26 Autonomous Cyber Enterprise.
Represents discrete actions assigned to and executed by autonomous agents.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class AgentTask(db.Model, TimestampMixin, TenantMixin):
    """Work item task assigned to an autonomous agent."""
    __tablename__ = 'agent_tasks'

    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('autonomous_agents.id', ondelete='CASCADE'), nullable=False)
    task_type = db.Column(db.String(120), nullable=False)
    priority = db.Column(db.String(32), default='medium', nullable=False) # low, medium, high
    status = db.Column(db.String(32), default='pending', nullable=False) # pending, running, completed, failed
    result = db.Column(db.Text, nullable=True)

    # Relationships
    agent = db.relationship('AutonomousAgent', back_populates='tasks')

    def __repr__(self):
        return f'<AgentTask id={self.id} type={self.task_type} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'task_type': self.task_type,
            'priority': self.priority,
            'status': self.status,
            'result': self.result,
            'organization_id': self.organization_id
        }
