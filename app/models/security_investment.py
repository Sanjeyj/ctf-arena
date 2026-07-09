"""
SecurityInvestment model - Phase 36 Cyber Risk Quantification.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class SecurityInvestment(db.Model, TimestampMixin, TenantMixin):
    """SecurityInvestment representation."""
    __tablename__ = 'security_investments'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    investment_category = db.Column(db.String(64), nullable=False)  # control, detection, training, resilience, etc.
    cost = db.Column(db.Float, default=0.0, nullable=False)
    annual_operating_cost = db.Column(db.Float, default=0.0, nullable=False)
    expected_loss_reduction = db.Column(db.Float, default=0.0, nullable=False)
    expected_risk_reduction = db.Column(db.Float, default=0.0, nullable=False)
    roi_score = db.Column(db.Float, default=0.0, nullable=False)
    rosi_score = db.Column(db.Float, default=0.0, nullable=False)
    priority_score = db.Column(db.Float, default=0.0, nullable=False)
    status = db.Column(db.String(32), default='proposed', nullable=False)

    def __repr__(self):
        return f'<SecurityInvestment {self.title!r} cost={self.cost}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'investment_category': self.investment_category,
            'cost': self.cost,
            'annual_operating_cost': self.annual_operating_cost,
            'expected_loss_reduction': self.expected_loss_reduction,
            'expected_risk_reduction': self.expected_risk_reduction,
            'roi_score': self.roi_score,
            'rosi_score': self.rosi_score,
            'priority_score': self.priority_score,
            'status': self.status,
            'organization_id': self.organization_id
        }
