"""
ChangeRecord model - Phase 31 Cyber Platform Control Plane.
Tracks simulated platform configuration changes.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class ChangeRecord(db.Model, TimestampMixin, TenantMixin):
    """ChangeRecord model."""
    __tablename__ = 'change_records'

    id = db.Column(db.Integer, primary_key=True)
    change_type = db.Column(db.String(64), nullable=False)  # feature_enable, policy_update, model_swap, health_maintenance
    resource_type = db.Column(db.String(64), nullable=False)
    resource_id = db.Column(db.String(64), nullable=False)
    requested_by = db.Column(db.String(120), nullable=False)
    approval_status = db.Column(db.String(32), default='requested', nullable=False)  # requested, reviewed, approved, rejected
    risk_score = db.Column(db.Float, default=0.0, nullable=False)
    rollback_plan = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), default='planned', nullable=False)  # planned, simulated, completed, rolled_back

    def __repr__(self):
        return f'<ChangeRecord type={self.change_type} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'change_type': self.change_type,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'requested_by': self.requested_by,
            'approval_status': self.approval_status,
            'risk_score': self.risk_score,
            'rollback_plan': self.rollback_plan,
            'status': self.status,
            'organization_id': self.organization_id,
        }
