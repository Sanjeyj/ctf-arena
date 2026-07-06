"""
DefenseUniverse model - Phase 30 Unified Cyber Defense Universe.
Root container for a unified defense simulation environment.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class DefenseUniverse(db.Model, TimestampMixin, TenantMixin):
    """Defense universe model."""
    __tablename__ = 'defense_universes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    universe_type = db.Column(db.String(64), default='default', nullable=False)
    status = db.Column(db.String(32), default='draft', nullable=False)  # draft, active, paused, completed, archived
    readiness_score = db.Column(db.Float, default=0.0, nullable=False)
    risk_score = db.Column(db.Float, default=0.0, nullable=False)
    resilience_score = db.Column(db.Float, default=0.0, nullable=False)

    def __repr__(self):
        return f'<DefenseUniverse {self.name!r} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'universe_type': self.universe_type,
            'status': self.status,
            'readiness_score': self.readiness_score,
            'risk_score': self.risk_score,
            'resilience_score': self.resilience_score,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
