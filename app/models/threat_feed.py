"""
ThreatFeed model — Phase 18 SOC Platform.
Represents an external threat intelligence feed source (simulation only).
"""
import datetime
from app.extensions import db
from app.models.mixins import TimestampMixin


FEED_TYPES = ['open_source', 'commercial', 'isac', 'internal', 'government']


class ThreatFeed(TimestampMixin, db.Model):
    """External threat intelligence feed configuration."""
    __tablename__ = 'threat_feeds'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    url = db.Column(db.String(512), nullable=True)
    feed_type = db.Column(db.String(32), default='open_source')
    description = db.Column(db.Text, default='')
    enabled = db.Column(db.Boolean, default=True)
    api_key = db.Column(db.String(256), nullable=True)    # stored encrypted in prod

    # Aggregation tracking
    last_fetched = db.Column(db.DateTime, nullable=True)
    ioc_count = db.Column(db.Integer, default=0)
    fetch_interval_minutes = db.Column(db.Integer, default=60)
    last_error = db.Column(db.Text, nullable=True)

    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)

    def __repr__(self):
        return f'<ThreatFeed {self.name} type={self.feed_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'feed_type': self.feed_type,
            'enabled': self.enabled,
            'last_fetched': self.last_fetched.isoformat() if self.last_fetched else None,
            'ioc_count': self.ioc_count,
        }
