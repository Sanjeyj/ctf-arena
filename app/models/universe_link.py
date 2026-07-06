"""
UniverseLink model - Phase 30 Unified Cyber Defense Universe.
Stores dependencies and trust links between universe nodes.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class UniverseLink(db.Model, TimestampMixin, TenantMixin):
    """Universe link model."""
    __tablename__ = 'universe_links'

    id = db.Column(db.Integer, primary_key=True)
    universe_id = db.Column(db.Integer, db.ForeignKey('defense_universes.id', ondelete='CASCADE'), nullable=False, index=True)
    source_node_id = db.Column(db.Integer, db.ForeignKey('universe_nodes.id', ondelete='CASCADE'), nullable=False, index=True)
    target_node_id = db.Column(db.Integer, db.ForeignKey('universe_nodes.id', ondelete='CASCADE'), nullable=False, index=True)
    relationship_type = db.Column(db.String(64), default='dependency', nullable=False)
    dependency_weight = db.Column(db.Float, default=1.0, nullable=False)
    trust_score = db.Column(db.Float, default=1.0, nullable=False)
    status = db.Column(db.String(32), default='active', nullable=False)

    def __repr__(self):
        return f'<UniverseLink {self.source_node_id}->{self.target_node_id} type={self.relationship_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'universe_id': self.universe_id,
            'source_node_id': self.source_node_id,
            'target_node_id': self.target_node_id,
            'relationship_type': self.relationship_type,
            'dependency_weight': self.dependency_weight,
            'trust_score': self.trust_score,
            'status': self.status,
            'organization_id': self.organization_id,
        }
