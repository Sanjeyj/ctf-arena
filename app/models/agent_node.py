"""
AgentNode model - Phase 24 Global Cyber Security Cloud.
Tracks federated artificial intelligence agent instances running regional scopes.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class AgentNode(db.Model, TimestampMixin, TenantMixin):
    """Federated intelligence agent node representation."""
    __tablename__ = 'agent_nodes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    agent_type = db.Column(db.String(64), default='SOC Agent') # SOC Agent, CTI Agent, LMS Agent, Executive Agent
    status = db.Column(db.String(32), default='active')

    def __repr__(self):
        return f'<AgentNode {self.name!r} type={self.agent_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'agent_type': self.agent_type,
            'status': self.status
        }
