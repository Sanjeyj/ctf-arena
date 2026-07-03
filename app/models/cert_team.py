"""
CertTeam model - Phase 29 Global Cyber Command Center.
Represents a national CERT (Computer Emergency Response Team) with capability and trust score.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class CertTeam(db.Model, TimestampMixin, TenantMixin):
    """National CERT team model."""
    __tablename__ = 'cert_teams'

    id = db.Column(db.Integer, primary_key=True)
    country = db.Column(db.String(64), nullable=False)
    capability = db.Column(db.Float, default=0.5, nullable=False)  # 0.0 - 1.0
    readiness = db.Column(db.Float, default=0.5, nullable=False)   # 0.0 - 1.0
    trust_score = db.Column(db.Float, default=0.5, nullable=False)  # 0.0 - 1.0

    def __repr__(self):
        return f'<CertTeam country={self.country!r} trust={self.trust_score}>'

    def to_dict(self):
        return {
            'id': self.id,
            'country': self.country,
            'capability': self.capability,
            'readiness': self.readiness,
            'trust_score': self.trust_score,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
