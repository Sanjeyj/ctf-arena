"""
DigitalTwin model - Phase 23 Security Digital Twin.
Simulates organizational networks vulnerabilities risk scenario impact scores.
"""
import json
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class DigitalTwin(db.Model, TimestampMixin, TenantMixin):
    """Digital twin simulation template profile."""
    __tablename__ = 'digital_twins'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    scenario_type = db.Column(db.String(80), default='ransomware') # asset_failure, ransomware, incident_propagation, control_failures
    configuration_json = db.Column('configuration', db.Text, default='{}')
    impact_score = db.Column(db.Float, default=50.0) # 0 to 100
    risk_score = db.Column(db.Float, default=50.0) # 0 to 100
    recovery_estimate_hours = db.Column(db.Integer, default=24)

    def __repr__(self):
        return f'<DigitalTwin {self.name!r} type={self.scenario_type}>'

    def to_dict(self):
        try:
            config = json.loads(self.configuration_json) if self.configuration_json else {}
        except Exception:
            config = {}
        return {
            'id': self.id,
            'name': self.name,
            'scenario_type': self.scenario_type,
            'configuration': config,
            'impact_score': self.impact_score,
            'risk_score': self.risk_score,
            'recovery_estimate_hours': self.recovery_estimate_hours
        }
