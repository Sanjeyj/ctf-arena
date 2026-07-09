"""
QuantitativeRiskScenario model - Phase 36 Cyber Risk Quantification.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class QuantitativeRiskScenario(db.Model, TimestampMixin, TenantMixin):
    """QuantitativeRiskScenario representation."""
    __tablename__ = 'quantitative_risk_scenarios'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    scenario_type = db.Column(db.String(64), nullable=False)  # ransomware, data_breach, Cloud_outage, etc.
    asset_reference_type = db.Column(db.String(64), nullable=True)
    asset_reference_id = db.Column(db.Integer, nullable=True)
    business_process_id = db.Column(db.Integer, db.ForeignKey('business_processes.id', ondelete='SET NULL'), nullable=True)
    threat_category = db.Column(db.String(64), nullable=True)
    likelihood_score = db.Column(db.Float, default=0.0, nullable=False)
    impact_score = db.Column(db.Float, default=0.0, nullable=False)
    inherent_risk_score = db.Column(db.Float, default=0.0, nullable=False)
    residual_risk_score = db.Column(db.Float, default=0.0, nullable=False)
    status = db.Column(db.String(32), default='draft', nullable=False)  # draft, active, analyzed, accepted, mitigating, closed

    business_process = db.relationship('BusinessProcess', backref=db.backref('risk_scenarios', lazy='dynamic'))

    def __repr__(self):
        return f'<QuantitativeRiskScenario {self.name!r} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'scenario_type': self.scenario_type,
            'asset_reference_type': self.asset_reference_type,
            'asset_reference_id': self.asset_reference_id,
            'business_process_id': self.business_process_id,
            'threat_category': self.threat_category,
            'likelihood_score': self.likelihood_score,
            'impact_score': self.impact_score,
            'inherent_risk_score': self.inherent_risk_score,
            'residual_risk_score': self.residual_risk_score,
            'status': self.status,
            'organization_id': self.organization_id
        }
