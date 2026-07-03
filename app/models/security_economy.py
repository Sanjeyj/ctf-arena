"""
SecurityEconomy model - Phase 28 Cyber Civilization Platform.
Tracks security investments, ecosystem growth rates, and market valuations.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class SecurityEconomy(db.Model, TimestampMixin, TenantMixin):
    """Security economy profile model."""
    __tablename__ = 'security_economies'

    id = db.Column(db.Integer, primary_key=True)
    investment = db.Column(db.Float, default=0.0, nullable=False)
    growth_rate = db.Column(db.Float, default=0.05, nullable=False)
    workforce_score = db.Column(db.Float, default=0.7, nullable=False)
    market_value = db.Column(db.Float, default=1000000.0, nullable=False)

    def __repr__(self):
        return f'<SecurityEconomy investment={self.investment} growth={self.growth_rate}>'

    def to_dict(self):
        return {
            'id': self.id,
            'investment': self.investment,
            'growth_rate': self.growth_rate,
            'workforce_score': self.workforce_score,
            'market_value': self.market_value,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
