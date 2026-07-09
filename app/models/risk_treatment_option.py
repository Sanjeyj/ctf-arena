"""
RiskTreatmentOption model - Phase 36 Cyber Risk Quantification.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class RiskTreatmentOption(db.Model, TimestampMixin, TenantMixin):
    """RiskTreatmentOption representation."""
    __tablename__ = 'risk_treatment_options'

    id = db.Column(db.Integer, primary_key=True)
    scenario_id = db.Column(db.Integer, db.ForeignKey('quantitative_risk_scenarios.id', ondelete='CASCADE'), nullable=False)
    treatment_type = db.Column(db.String(64), nullable=False)  # mitigate, avoid, transfer_simulation, accept
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    estimated_cost = db.Column(db.Float, default=0.0, nullable=False)
    expected_risk_reduction = db.Column(db.Float, default=0.0, nullable=False)  # percentage reduction, 0-100
    implementation_complexity = db.Column(db.String(32), default='medium', nullable=False)  # low, medium, high
    status = db.Column(db.String(32), default='proposed', nullable=False)  # proposed, reviewing, approved, simulated, rejected, completed

    scenario = db.relationship('QuantitativeRiskScenario', backref=db.backref('treatment_options', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<RiskTreatmentOption scenario_id={self.scenario_id} type={self.treatment_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'scenario_id': self.scenario_id,
            'treatment_type': self.treatment_type,
            'title': self.title,
            'description': self.description,
            'estimated_cost': self.estimated_cost,
            'expected_risk_reduction': self.expected_risk_reduction,
            'implementation_complexity': self.implementation_complexity,
            'status': self.status,
            'organization_id': self.organization_id
        }
