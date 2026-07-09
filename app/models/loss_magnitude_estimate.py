"""
LossMagnitudeEstimate model - Phase 36 Cyber Risk Quantification.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin
from sqlalchemy.orm import validates


class LossMagnitudeEstimate(db.Model, TimestampMixin, TenantMixin):
    """LossMagnitudeEstimate representation."""
    __tablename__ = 'loss_magnitude_estimates'

    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('quantitative_risk_scenarios.id', ondelete='CASCADE'), nullable=False)
    loss_type = db.Column(db.String(64), nullable=False)  # response_cost, recovery_cost, downtime_loss, etc.
    minimum_loss = db.Column(db.Float, default=0.0, nullable=False)
    most_likely_loss = db.Column(db.Float, default=0.0, nullable=False)
    maximum_loss = db.Column(db.Float, default=0.0, nullable=False)
    currency_code = db.Column(db.String(10), default='USD', nullable=False)
    confidence_score = db.Column(db.Float, default=1.0, nullable=False)

    scenario = db.relationship('QuantitativeRiskScenario', backref=db.backref('loss_estimates', lazy='dynamic', cascade='all, delete-orphan'))

    @validates('minimum_loss', 'most_likely_loss', 'maximum_loss')
    def validate_loss(self, key, value):
        if value < 0:
            raise ValueError(f"{key} must be >= 0")
        return value

    def __repr__(self):
        return f'<LossMagnitudeEstimate scenario_id={self.scenario_id} type={self.loss_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'scenario_id': self.scenario_id,
            'loss_type': self.loss_type,
            'minimum_loss': self.minimum_loss,
            'most_likely_loss': self.most_likely_loss,
            'maximum_loss': self.maximum_loss,
            'currency_code': self.currency_code,
            'confidence_score': self.confidence_score,
            'organization_id': self.organization_id
        }
