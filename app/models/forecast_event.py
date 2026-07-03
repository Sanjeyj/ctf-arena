"""
ForecastEvent model - Phase 27 Global Security Intelligence Network.
Represents a predicted future threat event with probability and impact scoring.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class ForecastEvent(db.Model, TimestampMixin, TenantMixin):
    """Forecast event produced by prediction models."""
    __tablename__ = 'forecast_events'

    id = db.Column(db.Integer, primary_key=True)
    prediction = db.Column(db.Text, nullable=False)
    probability = db.Column(db.Float, default=0.5, nullable=False)
    impact = db.Column(db.String(32), default='medium', nullable=False)  # low, medium, high, critical
    confidence = db.Column(db.Float, default=0.7, nullable=False)

    def __repr__(self):
        return f'<ForecastEvent impact={self.impact} prob={self.probability}>'

    def to_dict(self):
        return {
            'id': self.id,
            'prediction': self.prediction,
            'probability': self.probability,
            'impact': self.impact,
            'confidence': self.confidence,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
