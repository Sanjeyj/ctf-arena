"""
ControlInvestmentOption model - Phase 37 Strategic Cyber Resilience.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class ControlInvestmentOption(db.Model, TimestampMixin, TenantMixin):
    """ControlInvestmentOption representation."""
    __tablename__ = 'control_investment_options'

    id = db.Column(db.Integer, primary_key=True)
    control_reference = db.Column(db.String(120), nullable=False)  # references compliance_controls
    title = db.Column(db.String(120), nullable=False)
    implementation_cost = db.Column(db.Float, default=0.0, nullable=False)
    annual_operating_cost = db.Column(db.Float, default=0.0, nullable=False)
    expected_control_improvement = db.Column(db.Float, default=0.0, nullable=False)  # percentage or 0-100 improvement
    expected_risk_reduction = db.Column(db.Float, default=0.0, nullable=False)  # 0 to 100
    expected_resilience_gain = db.Column(db.Float, default=0.0, nullable=False)
    implementation_time_days = db.Column(db.Integer, default=30, nullable=False)
    dependency_requirements_json = db.Column(db.Text, default='[]', nullable=False)  # list of prerequisite control_references
    status = db.Column(db.String(32), default='proposed', nullable=False)

    def __repr__(self):
        return f'<ControlInvestmentOption {self.title!r} ref={self.control_reference}>'

    def to_dict(self):
        import json
        try:
            deps = json.loads(self.dependency_requirements_json or '[]')
        except Exception:
            deps = []
        return {
            'id': self.id,
            'control_reference': self.control_reference,
            'title': self.title,
            'implementation_cost': self.implementation_cost,
            'annual_operating_cost': self.annual_operating_cost,
            'expected_control_improvement': self.expected_control_improvement,
            'expected_risk_reduction': self.expected_risk_reduction,
            'expected_resilience_gain': self.expected_resilience_gain,
            'implementation_time_days': self.implementation_time_days,
            'dependency_requirements': deps,
            'status': self.status,
            'organization_id': self.organization_id
        }
