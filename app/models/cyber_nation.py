"""
CyberNation model - Phase 28 Cyber Civilization Platform.
Represents a cyber nation instance with population, region, status, and maturity index.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class CyberNation(db.Model, TimestampMixin, TenantMixin):
    """Cyber nation model."""
    __tablename__ = 'cyber_nations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    region = db.Column(db.String(64), nullable=False)
    maturity_score = db.Column(db.Float, default=0.5, nullable=False)
    population = db.Column(db.Integer, default=1000, nullable=False)
    status = db.Column(db.String(32), default='active', nullable=False)  # active, offline, quarantine

    def __repr__(self):
        return f'<CyberNation {self.name!r} region={self.region}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'region': self.region,
            'maturity_score': self.maturity_score,
            'population': self.population,
            'status': self.status,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
