"""
RemediationAction model - Phase 26 Autonomous Cyber Enterprise.
Represents autonomous self-healing, blockades, and threat remediation tasks.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class RemediationAction(db.Model, TimestampMixin, TenantMixin):
    """Self-healing action record."""
    __tablename__ = 'remediation_actions'

    id = db.Column(db.Integer, primary_key=True)
    action_type = db.Column(db.String(120), nullable=False)
    severity = db.Column(db.String(32), default='medium', nullable=False) # low, medium, high, critical
    status = db.Column(db.String(32), default='pending', nullable=False) # pending, executing, completed, failed
    execution_time = db.Column(db.Float, nullable=True) # in seconds

    def __repr__(self):
        return f'<RemediationAction id={self.id} type={self.action_type} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'action_type': self.action_type,
            'severity': self.severity,
            'status': self.status,
            'execution_time': self.execution_time,
            'organization_id': self.organization_id
        }
