"""
CrisisRoom model - Phase 29 Global Cyber Command Center.
Represents an active crisis command room tied to a specific incident.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class CrisisRoom(db.Model, TimestampMixin, TenantMixin):
    """Crisis room model."""
    __tablename__ = 'crisis_rooms'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    incident = db.Column(db.String(180), nullable=False)
    severity = db.Column(db.String(32), default='high', nullable=False)  # low, medium, high, critical
    active = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f'<CrisisRoom {self.title!r} active={self.active}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'incident': self.incident,
            'severity': self.severity,
            'active': self.active,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
