"""
RiskPortfolioMetric model - Phase 36 Cyber Risk Quantification.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin
import datetime


class RiskPortfolioMetric(db.Model, TimestampMixin, TenantMixin):
    """RiskPortfolioMetric representation."""
    __tablename__ = 'risk_portfolio_metrics'

    id = db.Column(db.Integer, primary_key=True)
    metric_type = db.Column(db.String(64), nullable=False)  # composite, single
    total_inherent_risk = db.Column(db.Float, default=0.0, nullable=False)
    total_residual_risk = db.Column(db.Float, default=0.0, nullable=False)
    expected_annual_loss = db.Column(db.Float, default=0.0, nullable=False)
    risk_reduction_value = db.Column(db.Float, default=0.0, nullable=False)
    investment_cost = db.Column(db.Float, default=0.0, nullable=False)
    portfolio_efficiency_score = db.Column(db.Float, default=0.0, nullable=False)
    measured_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<RiskPortfolioMetric type={self.metric_type} expected_annual_loss={self.expected_annual_loss}>'

    def to_dict(self):
        return {
            'id': self.id,
            'metric_type': self.metric_type,
            'total_inherent_risk': self.total_inherent_risk,
            'total_residual_risk': self.total_residual_risk,
            'expected_annual_loss': self.expected_annual_loss,
            'risk_reduction_value': self.risk_reduction_value,
            'investment_cost': self.investment_cost,
            'portfolio_efficiency_score': self.portfolio_efficiency_score,
            'measured_at': self.measured_at.isoformat() if self.measured_at else None,
            'organization_id': self.organization_id
        }
