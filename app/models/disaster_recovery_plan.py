"""
DisasterRecoveryPlan model - Phase 25 Cyber Resilience & Digital Enterprise.
Defines strategies, prioritizations, and approval lifecycles for recovery procedures.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class DisasterRecoveryPlan(db.Model, TimestampMixin, TenantMixin):
    """Disaster Recovery & Business Continuity Plans."""
    __tablename__ = 'disaster_recovery_plans'

    id = db.Column(db.Integer, primary_key=True)
    plan_name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    strategy = db.Column(db.Text, nullable=True)
    recovery_steps = db.Column(db.Text, nullable=True) # JSON list or raw text steps
    priority = db.Column(db.Integer, default=3, nullable=False) # 1-5 scale
    approval_status = db.Column(db.String(32), default='draft', nullable=False) # draft, approved, retired

    def __repr__(self):
        return f'<DisasterRecoveryPlan {self.plan_name!r} status={self.approval_status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'plan_name': self.plan_name,
            'strategy': self.strategy,
            'recovery_steps': self.recovery_steps,
            'priority': self.priority,
            'approval_status': self.approval_status,
            'organization_id': self.organization_id
        }
