"""
IOC (Indicator of Compromise) model — Phase 18 SOC Platform.
Simulation-only: no live threat blocking or network actions.
"""
import datetime
from app.extensions import db
from app.models.mixins import TimestampMixin


IOC_TYPES = ['ip', 'domain', 'url', 'hash', 'email']
IOC_SEVERITIES = ['info', 'low', 'medium', 'high', 'critical']


class IOC(TimestampMixin, db.Model):
    """Indicator of Compromise — threat intelligence artifact."""
    __tablename__ = 'iocs'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(32), nullable=False)          # ip/domain/url/hash/email
    value = db.Column(db.String(512), nullable=False)
    severity = db.Column(db.String(16), default='medium')    # info/low/medium/high/critical
    confidence = db.Column(db.Integer, default=50)           # 0–100
    source = db.Column(db.String(128), default='manual')
    tags = db.Column(db.Text, default='')                    # comma-separated
    description = db.Column(db.Text, default='')
    is_blocked = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    # Enrichment fields (simulated)
    geo_country = db.Column(db.String(64), nullable=True)
    reputation_score = db.Column(db.Integer, nullable=True)  # 0–100, lower = worse
    enriched_at = db.Column(db.DateTime, nullable=True)

    first_seen = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)

    def __repr__(self):
        return f'<IOC {self.type}:{self.value} sev={self.severity}>'

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'value': self.value,
            'severity': self.severity,
            'confidence': self.confidence,
            'source': self.source,
            'tags': self.tags,
            'description': self.description,
            'is_blocked': self.is_blocked,
            'is_active': self.is_active,
            'geo_country': self.geo_country,
            'reputation_score': self.reputation_score,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
        }
