"""
CivilizationMetric model - Phase 28 Cyber Civilization Platform.
Tracks total maturity, resilience, intelligence, and innovation index tracking.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class CivilizationMetric(db.Model, TimestampMixin, TenantMixin):
    """Civilization composite index tracking model."""
    __tablename__ = 'civilization_metrics'

    id = db.Column(db.Integer, primary_key=True)
    maturity = db.Column(db.Float, default=0.5, nullable=False)
    resilience = db.Column(db.Float, default=0.5, nullable=False)
    intelligence = db.Column(db.Float, default=0.5, nullable=False)
    innovation = db.Column(db.Float, default=0.5, nullable=False)

    def __repr__(self):
        return f'<CivilizationMetric maturity={self.maturity} resilience={self.resilience}>'

    def to_dict(self):
        return {
            'id': self.id,
            'maturity': self.maturity,
            'resilience': self.resilience,
            'intelligence': self.intelligence,
            'innovation': self.innovation,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
