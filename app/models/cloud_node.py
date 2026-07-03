"""
CloudNode model - Phase 24 Global Cyber Security Cloud.
Tracks specific node instances inside geographical regions.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class CloudNode(db.Model, TimestampMixin, TenantMixin):
    """Cloud node instance running specific SecOS actions."""
    __tablename__ = 'cloud_nodes'

    id = db.Column(db.Integer, primary_key=True)
    region_id = db.Column(db.Integer, db.ForeignKey('cloud_regions.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(120), nullable=False, unique=True, index=True)
    node_type = db.Column(db.String(64), default='SOC Node') # SOC Node, CTI Node, AI Node, Training Node
    status = db.Column(db.String(32), default='online') # online, degraded, offline

    # Relationships
    region = db.relationship('CloudRegion', backref=db.backref('nodes', cascade='all, delete-orphan', lazy='dynamic'))

    def __repr__(self):
        return f'<CloudNode {self.name!r} type={self.node_type} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'region_id': self.region_id,
            'name': self.name,
            'node_type': self.node_type,
            'status': self.status
        }
