"""
InvestmentPlanItem model - Phase 37 Strategic Cyber Resilience.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class InvestmentPlanItem(db.Model, TimestampMixin, TenantMixin):
    """InvestmentPlanItem representation."""
    __tablename__ = 'investment_plan_items'

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('resilience_investment_plans.id', ondelete='CASCADE'), nullable=False)
    security_investment_id = db.Column(db.Integer, db.ForeignKey('security_investments.id', ondelete='CASCADE'), nullable=False)
    allocated_budget = db.Column(db.Float, default=0.0, nullable=False)
    expected_loss_reduction = db.Column(db.Float, default=0.0, nullable=False)
    expected_resilience_improvement = db.Column(db.Float, default=0.0, nullable=False)
    priority_rank = db.Column(db.Integer, default=1, nullable=False)
    selection_reason = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(32), default='candidate', nullable=False)  # candidate, selected, deferred, rejected, approved

    plan = db.relationship('ResilienceInvestmentPlan', backref=db.backref('items', lazy='dynamic', cascade='all, delete-orphan'))
    security_investment = db.relationship('SecurityInvestment', backref=db.backref('plan_items', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<InvestmentPlanItem plan_id={self.plan_id} investment_id={self.security_investment_id} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'security_investment_id': self.security_investment_id,
            'allocated_budget': self.allocated_budget,
            'expected_loss_reduction': self.expected_loss_reduction,
            'expected_resilience_improvement': self.expected_resilience_improvement,
            'priority_rank': self.priority_rank,
            'selection_reason': self.selection_reason,
            'status': self.status,
            'organization_id': self.organization_id
        }
