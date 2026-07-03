"""
ThreatHuntSession model - Phase 21 AI Threat Hunter.
Tracks active and completed threat hunting session details.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class ThreatHuntSession(db.Model, TimestampMixin, TenantMixin):
    """AI-powered threat hunting session."""
    __tablename__ = 'threat_hunt_sessions'

    id = db.Column(db.Integer, primary_key=True)
    hunt_type = db.Column(db.String(32), default='ioc') # ioc, anomaly, mitre, sigma
    confidence = db.Column(db.Float, default=0.9)
    findings = db.Column(db.Text, nullable=True)
    recommendations = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<ThreatHuntSession id={self.id} type={self.hunt_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'hunt_type': self.hunt_type,
            'confidence': self.confidence,
            'findings': self.findings,
            'recommendations': self.recommendations,
            'created_at': self.created_at.isoformat() if hasattr(self, 'created_at') and self.created_at else None
        }
