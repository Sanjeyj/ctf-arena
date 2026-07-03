"""
ObservatoryNode model - Phase 27 Global Security Intelligence Network.
Represents a regional security monitoring node in the global cyber observatory.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class ObservatoryNode(db.Model, TimestampMixin, TenantMixin):
    """Global observatory monitoring node."""
    __tablename__ = 'observatory_nodes'

    id = db.Column(db.Integer, primary_key=True)
    region = db.Column(db.String(64), nullable=False)  # us-east, eu-west, asia-south, etc.
    node_type = db.Column(db.String(64), nullable=False)  # threat, intelligence, compliance, resilience, enterprise
    status = db.Column(db.String(32), default='online', nullable=False)  # online, degraded, offline
    health = db.Column(db.Float, default=1.0, nullable=False)  # 0.0 to 1.0

    def __repr__(self):
        return f'<ObservatoryNode region={self.region!r} type={self.node_type} health={self.health}>'

    def to_dict(self):
        return {
            'id': self.id,
            'region': self.region,
            'node_type': self.node_type,
            'status': self.status,
            'health': self.health,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
