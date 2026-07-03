"""
IntelligenceSource model - Phase 27 Global Security Intelligence Network.
Represents a trusted organization contributing intelligence to the network.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class IntelligenceSource(db.Model, TimestampMixin, TenantMixin):
    """Intelligence contributor source profile."""
    __tablename__ = 'intelligence_sources'

    id = db.Column(db.Integer, primary_key=True)
    organization = db.Column(db.String(255), nullable=False)
    source_type = db.Column(db.String(64), nullable=False)  # government, commercial, open-source, private
    reputation = db.Column(db.Float, default=0.5, nullable=False)
    status = db.Column(db.String(32), default='active', nullable=False)  # active, suspended, probation

    def __repr__(self):
        return f'<IntelligenceSource {self.organization!r} type={self.source_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'organization': self.organization,
            'source_type': self.source_type,
            'reputation': self.reputation,
            'status': self.status,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
