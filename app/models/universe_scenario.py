"""
UniverseScenario model - Phase 30 Unified Cyber Defense Universe.
Defines safe strategic what-if simulations.
"""
import json
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class UniverseScenario(db.Model, TimestampMixin, TenantMixin):
    """Universe scenario model."""
    __tablename__ = 'universe_scenarios'

    id = db.Column(db.Integer, primary_key=True)
    universe_id = db.Column(db.Integer, db.ForeignKey('defense_universes.id', ondelete='CASCADE'), nullable=False, index=True)
    scenario_name = db.Column(db.String(120), nullable=False)
    scenario_type = db.Column(db.String(64), nullable=False)  # ransomware_outage, cloud_region_failure, etc.
    severity = db.Column(db.String(32), default='medium', nullable=False)  # low, medium, high, critical
    probability = db.Column(db.Float, default=0.5, nullable=False)
    impact_score = db.Column(db.Float, default=0.5, nullable=False)
    status = db.Column(db.String(32), default='active', nullable=False)
    configuration_json = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<UniverseScenario {self.scenario_name!r} type={self.scenario_type}>'

    def to_dict(self):
        config = {}
        if self.configuration_json:
            try:
                config = json.loads(self.configuration_json)
            except Exception:
                pass
        return {
            'id': self.id,
            'universe_id': self.universe_id,
            'scenario_name': self.scenario_name,
            'scenario_type': self.scenario_type,
            'severity': self.severity,
            'probability': self.probability,
            'impact_score': self.impact_score,
            'status': self.status,
            'configuration': config,
            'organization_id': self.organization_id,
        }
