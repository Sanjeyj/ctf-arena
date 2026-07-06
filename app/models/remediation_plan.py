"""
RemediationPlan model - Phase 34 Security Architecture, Exposure & Attack Surface Management Fabric.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin
import datetime


class RemediationPlan(db.Model, TimestampMixin, TenantMixin):
    __tablename__ = 'remediation_plans'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    finding_id = db.Column(db.Integer, db.ForeignKey('exposure_findings.id', name='fk_remediation_plans_finding_id'), nullable=False)
    priority_score = db.Column(db.Float, nullable=False, default=1.0)
    recommended_action = db.Column(db.Text, nullable=True)
    compensating_controls_json = db.Column(db.Text, nullable=True, default='[]')
    approval_status = db.Column(db.String(50), nullable=False, default='draft')  # draft, pending, approved, rejected
    status = db.Column(db.String(50), nullable=False, default='planned')  # planned, in_progress, completed, verified
    target_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.datetime.utcnow() + datetime.timedelta(days=30))
