"""
ValidationScenario model - Phase 35 Continuous Security Validation.
Defines validation scopes, rules, and expected outcomes.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class ValidationScenario(db.Model, TimestampMixin, TenantMixin):
    """ValidationScenario representation."""
    __tablename__ = 'validation_scenarios'

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('validation_campaigns.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    scenario_type = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text, nullable=True)
    severity = db.Column(db.String(32), default='medium', nullable=False)
    expected_outcome = db.Column(db.String(120), nullable=False)
    configuration_json = db.Column(db.Text, nullable=True)  # JSON-encoded options
    status = db.Column(db.String(32), default='active', nullable=False)

    campaign = db.relationship('ValidationCampaign', backref=db.backref('scenarios', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<ValidationScenario {self.name!r} type={self.scenario_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'name': self.name,
            'scenario_type': self.scenario_type,
            'description': self.description,
            'severity': self.severity,
            'expected_outcome': self.expected_outcome,
            'configuration_json': self.configuration_json,
            'status': self.status,
            'organization_id': self.organization_id
        }
