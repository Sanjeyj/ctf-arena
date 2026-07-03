"""
GlobalThreatFeed model - Phase 27 Global Security Intelligence Network.
Represents an incoming threat intelligence feed from a named source.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class GlobalThreatFeed(db.Model, TimestampMixin, TenantMixin):
    """Global threat intelligence feed profile."""
    __tablename__ = 'global_threat_feeds'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    source = db.Column(db.String(255), nullable=False)
    trust_score = db.Column(db.Float, default=0.5, nullable=False)
    status = db.Column(db.String(32), default='active', nullable=False)  # active, paused, deprecated
    update_frequency = db.Column(db.String(32), default='daily', nullable=False)  # realtime, hourly, daily

    def __repr__(self):
        return f'<GlobalThreatFeed {self.name!r} trust={self.trust_score}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'source': self.source,
            'trust_score': self.trust_score,
            'status': self.status,
            'update_frequency': self.update_frequency,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
