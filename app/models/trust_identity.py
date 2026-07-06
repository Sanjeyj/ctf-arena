"""
TrustIdentity model - Phase 32 Cyber Trust, Assurance & Verification Fabric.
Stores simulated identity assurance posture.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class TrustIdentity(db.Model, TimestampMixin, TenantMixin):
    """TrustIdentity model."""
    __tablename__ = 'trust_identities'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    identity_type = db.Column(db.String(64), nullable=False)  # user, service_account, api_key, system
    authentication_strength = db.Column(db.Float, default=1.0, nullable=False)  # 0.0 to 1.0
    risk_score = db.Column(db.Float, default=0.0, nullable=False)  # 0.0 to 1.0
    trust_score = db.Column(db.Float, default=100.0, nullable=False)  # 0 to 100
    verification_status = db.Column(db.String(64), default='unverified', nullable=False)  # unverified, pending, verified, restricted, revoked_simulation
    last_verified_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<TrustIdentity user_id={self.user_id} status={self.verification_status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'identity_type': self.identity_type,
            'authentication_strength': self.authentication_strength,
            'risk_score': self.risk_score,
            'trust_score': self.trust_score,
            'verification_status': self.verification_status,
            'last_verified_at': self.last_verified_at.isoformat() if self.last_verified_at else None,
            'organization_id': self.organization_id,
        }
