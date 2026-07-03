"""
ThreatCampaignGlobal model - Phase 29 Global Cyber Command Center.
Represents a global threat campaign with regional impact and confidence score.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class ThreatCampaignGlobal(db.Model, TimestampMixin, TenantMixin):
    """Global threat campaign model."""
    __tablename__ = 'threat_campaigns_global'

    id = db.Column(db.Integer, primary_key=True)
    campaign_name = db.Column(db.String(120), nullable=False)
    region = db.Column(db.String(64), nullable=False)
    impact = db.Column(db.Float, default=0.5, nullable=False)       # 0.0 - 1.0
    confidence = db.Column(db.Float, default=0.5, nullable=False)   # 0.0 - 1.0

    def __repr__(self):
        return f'<ThreatCampaignGlobal {self.campaign_name!r} region={self.region}>'

    def to_dict(self):
        return {
            'id': self.id,
            'campaign_name': self.campaign_name,
            'region': self.region,
            'impact': self.impact,
            'confidence': self.confidence,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
