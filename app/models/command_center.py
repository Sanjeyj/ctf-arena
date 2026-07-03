"""
CommandCenter model - Phase 29 Global Cyber Command Center.
Represents a regional command center with readiness and commander info.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class CommandCenter(db.Model, TimestampMixin, TenantMixin):
    """Command center model."""
    __tablename__ = 'command_centers'

    id = db.Column(db.Integer, primary_key=True)
    region = db.Column(db.String(64), nullable=False)
    commander = db.Column(db.String(120), nullable=False)
    readiness = db.Column(db.Float, default=0.7, nullable=False)
    status = db.Column(db.String(32), default='operational', nullable=False)  # operational, degraded, offline

    def __repr__(self):
        return f'<CommandCenter region={self.region!r} commander={self.commander!r}>'

    def to_dict(self):
        return {
            'id': self.id,
            'region': self.region,
            'commander': self.commander,
            'readiness': self.readiness,
            'status': self.status,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
