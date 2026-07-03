"""
ThreatReputation model - Phase 24 Global Cyber Security Cloud.
Stores global threat actor reputation rating scores.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class ThreatReputation(db.Model, TimestampMixin, TenantMixin):
    """Threat indicator score ratings."""
    __tablename__ = 'threat_reputations'

    id = db.Column(db.Integer, primary_key=True)
    entity_value = db.Column(db.String(256), nullable=False, unique=True, index=True)
    category = db.Column(db.String(64), default='ioc') # malware, ioc, actor, campaign
    score = db.Column(db.Integer, default=50) # 0 to 100
    level = db.Column(db.String(32), default='medium') # low, medium, high, critical

    def __repr__(self):
        return f'<ThreatReputation {self.entity_value!r} score={self.score}>'

    def to_dict(self):
        return {
            'id': self.id,
            'entity_value': self.entity_value,
            'category': self.category,
            'score': self.score,
            'level': self.level
        }
