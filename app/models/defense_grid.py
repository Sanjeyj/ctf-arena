"""
DefenseGrid model - Phase 28 Cyber Civilization Platform.
Represents an autonomous defense grid cluster protecting endpoints and zones.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class DefenseGrid(db.Model, TimestampMixin, TenantMixin):
    """Defense grid cluster model."""
    __tablename__ = 'defense_grids'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    coverage = db.Column(db.Float, default=0.5, nullable=False)  # 0.0 to 1.0
    health = db.Column(db.Float, default=1.0, nullable=False)  # 0.0 to 1.0
    readiness = db.Column(db.Float, default=0.8, nullable=False)  # 0.0 to 1.0

    def __repr__(self):
        return f'<DefenseGrid {self.name!r} health={self.health} readiness={self.readiness}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'coverage': self.coverage,
            'health': self.health,
            'readiness': self.readiness,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
