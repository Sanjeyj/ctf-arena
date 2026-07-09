"""
StressTestScenario model - Phase 37 Strategic Cyber Resilience.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class StressTestScenario(db.Model, TimestampMixin, TenantMixin):
    """StressTestScenario representation."""
    __tablename__ = 'stress_test_scenarios'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    scenario_category = db.Column(db.String(64), nullable=False)  # ransomware_disruption, cloud_region_failure, etc.
    severity = db.Column(db.String(32), default='medium', nullable=False)  # low, medium, high, critical
    duration_hours = db.Column(db.Float, default=24.0, nullable=False)
    affected_domains_json = db.Column(db.Text, default='[]', nullable=False)  # JSON list of domains
    probability = db.Column(db.Float, default=0.1, nullable=False)  # 0 to 1
    impact_multiplier = db.Column(db.Float, default=1.0, nullable=False)
    status = db.Column(db.String(32), default='draft', nullable=False)  # draft, approved, running_simulation, completed, archived

    def __repr__(self):
        return f'<StressTestScenario {self.name!r} category={self.scenario_category}>'

    def to_dict(self):
        import json
        try:
            domains = json.loads(self.affected_domains_json or '[]')
        except Exception:
            domains = []
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'scenario_category': self.scenario_category,
            'severity': self.severity,
            'duration_hours': self.duration_hours,
            'affected_domains': domains,
            'probability': self.probability,
            'impact_multiplier': self.impact_multiplier,
            'status': self.status,
            'organization_id': self.organization_id
        }
