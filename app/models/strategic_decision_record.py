"""
StrategicDecisionRecord model - Phase 37 Strategic Cyber Resilience.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class StrategicDecisionRecord(db.Model, TimestampMixin, TenantMixin):
    """StrategicDecisionRecord representation."""
    __tablename__ = 'strategic_decision_records'

    id = db.Column(db.Integer, primary_key=True)
    decision_type = db.Column(db.String(64), nullable=False)  # budget_allocation, control_prioritization, scenario_acceptance, vendor_mitigation, insurance_adjustment
    title = db.Column(db.String(120), nullable=False)
    decision_context = db.Column(db.Text, nullable=True)
    options_json = db.Column(db.Text, default='[]', nullable=False)  # JSON description of alternative options
    recommended_option = db.Column(db.String(120), nullable=True)
    confidence_score = db.Column(db.Float, default=1.0, nullable=False)
    risk_reduction_score = db.Column(db.Float, default=0.0, nullable=False)
    financial_efficiency_score = db.Column(db.Float, default=0.0, nullable=False)
    resilience_improvement_score = db.Column(db.Float, default=0.0, nullable=False)
    approval_status = db.Column(db.String(32), default='pending', nullable=False)  # pending, approved, rejected, requires_review
    approved_by = db.Column(db.String(120), nullable=True)

    def __repr__(self):
        return f'<StrategicDecisionRecord {self.title!r} status={self.approval_status}>'

    def to_dict(self):
        import json
        try:
            opts = json.loads(self.options_json or '[]')
        except Exception:
            opts = []
        return {
            'id': self.id,
            'decision_type': self.decision_type,
            'title': self.title,
            'decision_context': self.decision_context,
            'options': opts,
            'recommended_option': self.recommended_option,
            'confidence_score': self.confidence_score,
            'risk_reduction_score': self.risk_reduction_score,
            'financial_efficiency_score': self.financial_efficiency_score,
            'resilience_improvement_score': self.resilience_improvement_score,
            'approval_status': self.approval_status,
            'approved_by': self.approved_by,
            'organization_id': self.organization_id
        }
