"""
ResilienceInvestmentPlan model - Phase 37 Strategic Cyber Resilience.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class ResilienceInvestmentPlan(db.Model, TimestampMixin, TenantMixin):
    """ResilienceInvestmentPlan representation."""
    __tablename__ = 'resilience_investment_plans'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    budget_limit = db.Column(db.Float, default=100000.0, nullable=False)
    planning_horizon_months = db.Column(db.Integer, default=12, nullable=False)
    target_risk_reduction = db.Column(db.Float, default=0.0, nullable=False)  # percentage reduction target
    target_resilience_score = db.Column(db.Float, default=80.0, nullable=False)
    status = db.Column(db.String(32), default='draft', nullable=False)  # draft, analyzing, recommended, approved, rejected, completed
    approved_by = db.Column(db.String(120), nullable=True)

    def __repr__(self):
        return f'<ResilienceInvestmentPlan {self.name!r} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'budget_limit': self.budget_limit,
            'planning_horizon_months': self.planning_horizon_months,
            'target_risk_reduction': self.target_risk_reduction,
            'target_resilience_score': self.target_resilience_score,
            'status': self.status,
            'approved_by': self.approved_by,
            'organization_id': self.organization_id
        }
