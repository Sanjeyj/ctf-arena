"""
TrustNetwork model - Phase 27 Global Security Intelligence Network.
Represents a bilateral trust relationship between two organizations.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class TrustNetwork(db.Model, TimestampMixin, TenantMixin):
    """Organization trust network relationship."""
    __tablename__ = 'trust_networks'

    id = db.Column(db.Integer, primary_key=True)
    source_org = db.Column(db.String(255), nullable=False)
    target_org = db.Column(db.String(255), nullable=False)
    trust_score = db.Column(db.Float, default=0.5, nullable=False)
    status = db.Column(db.String(32), default='pending', nullable=False)  # pending, active, suspended, revoked

    def __repr__(self):
        return f'<TrustNetwork {self.source_org!r} -> {self.target_org!r} score={self.trust_score}>'

    def to_dict(self):
        return {
            'id': self.id,
            'source_org': self.source_org,
            'target_org': self.target_org,
            'trust_score': self.trust_score,
            'status': self.status,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
