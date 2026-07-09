"""
ResiliencePortfolioMetric model - Phase 37 Strategic Cyber Resilience.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin
import datetime


class ResiliencePortfolioMetric(db.Model, TimestampMixin, TenantMixin):
    """ResiliencePortfolioMetric representation."""
    __tablename__ = 'resilience_portfolio_metrics'

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('resilience_investment_plans.id', ondelete='CASCADE'), nullable=False)
    total_budget = db.Column(db.Float, default=0.0, nullable=False)
    allocated_budget = db.Column(db.Float, default=0.0, nullable=False)
    expected_loss_before = db.Column(db.Float, default=0.0, nullable=False)
    expected_loss_after = db.Column(db.Float, default=0.0, nullable=False)
    risk_reduction_percentage = db.Column(db.Float, default=0.0, nullable=False)
    resilience_before = db.Column(db.Float, default=100.0, nullable=False)
    resilience_after = db.Column(db.Float, default=100.0, nullable=False)
    portfolio_efficiency_score = db.Column(db.Float, default=0.0, nullable=False)
    risk_appetite_alignment_score = db.Column(db.Float, default=0.0, nullable=False)
    measured_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)

    plan = db.relationship('ResilienceInvestmentPlan', backref=db.backref('portfolio_metrics', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<ResiliencePortfolioMetric plan_id={self.plan_id} efficiency={self.portfolio_efficiency_score}>'

    def to_dict(self):
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'total_budget': self.total_budget,
            'allocated_budget': self.allocated_budget,
            'expected_loss_before': self.expected_loss_before,
            'expected_loss_after': self.expected_loss_after,
            'risk_reduction_percentage': self.risk_reduction_percentage,
            'resilience_before': self.resilience_before,
            'resilience_after': self.resilience_after,
            'portfolio_efficiency_score': self.portfolio_efficiency_score,
            'risk_appetite_alignment_score': self.risk_appetite_alignment_score,
            'measured_at': self.measured_at.isoformat() if self.measured_at else None,
            'organization_id': self.organization_id
        }
