"""
UniverseNode model - Phase 30 Unified Cyber Defense Universe.
Represents simulated infrastructure or capability nodes.
"""
import json
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class UniverseNode(db.Model, TimestampMixin, TenantMixin):
    """Universe node model."""
    __tablename__ = 'universe_nodes'

    id = db.Column(db.Integer, primary_key=True)
    universe_id = db.Column(db.Integer, db.ForeignKey('defense_universes.id', ondelete='CASCADE'), nullable=False, index=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('defense_domains.id', ondelete='CASCADE'), nullable=False, index=True)
    node_name = db.Column(db.String(120), nullable=False)
    node_type = db.Column(db.String(64), nullable=False)
    region = db.Column(db.String(64), nullable=True)
    criticality = db.Column(db.String(32), default='medium', nullable=False)  # low, medium, high, critical
    health_score = db.Column(db.Float, default=1.0, nullable=False)
    status = db.Column(db.String(32), default='online', nullable=False)
    metadata_json = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<UniverseNode {self.node_name!r} type={self.node_type}>'

    def to_dict(self):
        meta = {}
        if self.metadata_json:
            try:
                meta = json.loads(self.metadata_json)
            except Exception:
                pass
        return {
            'id': self.id,
            'universe_id': self.universe_id,
            'domain_id': self.domain_id,
            'node_name': self.node_name,
            'node_type': self.node_type,
            'region': self.region,
            'criticality': self.criticality,
            'health_score': self.health_score,
            'status': self.status,
            'metadata': meta,
            'organization_id': self.organization_id,
        }
