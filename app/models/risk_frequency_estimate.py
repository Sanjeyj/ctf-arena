"""
RiskFrequencyEstimate model - Phase 36 Cyber Risk Quantification.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin
from sqlalchemy.orm import validates


class RiskFrequencyEstimate(db.Model, TimestampMixin, TenantMixin):
    """RiskFrequencyEstimate representation."""
    __tablename__ = 'risk_frequency_estimates'

    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('quantitative_risk_scenarios.id', ondelete='CASCADE'), nullable=False)
    frequency_type = db.Column(db.String(64), nullable=False)  # triangular, pert, fixed, historical_simulation
    minimum_frequency = db.Column(db.Float, default=0.0, nullable=False)
    most_likely_frequency = db.Column(db.Float, default=0.0, nullable=False)
    maximum_frequency = db.Column(db.Float, default=0.0, nullable=False)
    annual_rate = db.Column(db.Float, default=0.0, nullable=False)
    confidence_score = db.Column(db.Float, default=1.0, nullable=False)
    source_basis = db.Column(db.String(255), nullable=True)

    scenario = db.relationship('QuantitativeRiskScenario', backref=db.backref('frequency_estimates', lazy='dynamic', cascade='all, delete-orphan'))

    @validates('minimum_frequency', 'most_likely_frequency', 'maximum_frequency')
    def validate_frequency(self, key, value):
        if value < 0:
            raise ValueError(f"{key} must be >= 0")
        return value

    def __repr__(self):
        return f'<RiskFrequencyEstimate scenario_id={self.scenario_id} type={self.frequency_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'scenario_id': self.scenario_id,
            'frequency_type': self.frequency_type,
            'minimum_frequency': self.minimum_frequency,
            'most_likely_frequency': self.most_likely_frequency,
            'maximum_frequency': self.maximum_frequency,
            'annual_rate': self.annual_rate,
            'confidence_score': self.confidence_score,
            'source_basis': self.source_basis,
            'organization_id': self.organization_id
        }
