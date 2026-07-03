"""
AutonomousDecision model - Phase 26 Autonomous Cyber Enterprise.
Logs security assessments, threat analyses, and decision logs compiled by the agents.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class AutonomousDecision(db.Model, TimestampMixin, TenantMixin):
    """Decision log created by agents."""
    __tablename__ = 'autonomous_decisions'

    id = db.Column(db.Integer, primary_key=True)
    decision_type = db.Column(db.String(120), nullable=False)
    confidence = db.Column(db.Float, default=0.8, nullable=False)
    recommendation = db.Column(db.Text, nullable=False)
    approval_status = db.Column(db.String(32), default='pending_approval', nullable=False) # pending_approval, approved, rejected

    def __repr__(self):
        return f'<AutonomousDecision id={self.id} type={self.decision_type} status={self.approval_status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'decision_type': self.decision_type,
            'confidence': self.confidence,
            'recommendation': self.recommendation,
            'approval_status': self.approval_status,
            'organization_id': self.organization_id
        }
