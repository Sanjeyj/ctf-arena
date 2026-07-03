"""
PredictionScenario model - Phase 28 Cyber Civilization Platform.
Represents simulated cyber defense/threat prediction scenarios.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class PredictionScenario(db.Model, TimestampMixin, TenantMixin):
    """Threat prediction scenario model."""
    __tablename__ = 'prediction_scenarios'

    id = db.Column(db.Integer, primary_key=True)
    scenario_name = db.Column(db.String(120), nullable=False)
    impact_score = db.Column(db.Float, default=0.5, nullable=False)  # 0.0 to 1.0
    probability = db.Column(db.Float, default=0.5, nullable=False)  # 0.0 to 1.0
    confidence = db.Column(db.Float, default=0.7, nullable=False)  # 0.0 to 1.0

    def __repr__(self):
        return f'<PredictionScenario {self.scenario_name!r} prob={self.probability}>'

    def to_dict(self):
        return {
            'id': self.id,
            'scenario_name': self.scenario_name,
            'impact_score': self.impact_score,
            'probability': self.probability,
            'confidence': self.confidence,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
