"""
SecurityWorkflow model - Phase 26 Autonomous Cyber Enterprise.
Configures orchestrated action triggers and steps for the security orchestration mesh.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class SecurityWorkflow(db.Model, TimestampMixin, TenantMixin):
    """Security workflow rule definition."""
    __tablename__ = 'security_workflows'

    id = db.Column(db.Integer, primary_key=True)
    workflow_name = db.Column(db.String(120), nullable=False)
    trigger = db.Column(db.String(120), nullable=False) # e.g. on_incident, on_compliance_drift
    steps = db.Column(db.Text, nullable=True) # JSON array of step details
    status = db.Column(db.String(32), default='active', nullable=False) # active, inactive

    def __repr__(self):
        return f'<SecurityWorkflow {self.workflow_name!r} trigger={self.trigger}>'

    def to_dict(self):
        return {
            'id': self.id,
            'workflow_name': self.workflow_name,
            'trigger': self.trigger,
            'steps': self.steps,
            'status': self.status,
            'organization_id': self.organization_id
        }
