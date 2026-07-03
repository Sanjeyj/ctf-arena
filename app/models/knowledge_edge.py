"""
KnowledgeEdge model - Phase 21 Security Knowledge Graph.
Edges connect CTI entities with relationship types.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class KnowledgeEdge(db.Model, TimestampMixin, TenantMixin):
    """Edge connector in CTI security network."""
    __tablename__ = 'knowledge_edges'

    id = db.Column(db.Integer, primary_key=True)
    source_node_id = db.Column(db.Integer, db.ForeignKey('knowledge_nodes.id', ondelete='CASCADE'), nullable=False)
    target_node_id = db.Column(db.Integer, db.ForeignKey('knowledge_nodes.id', ondelete='CASCADE'), nullable=False)
    relationship = db.Column(db.String(80), nullable=False) # e.g. mapped_to, attributes_to, dropped_by

    # Relationships
    source_node = db.relationship('KnowledgeNode', foreign_keys=[source_node_id], backref='edges_out')
    target_node = db.relationship('KnowledgeNode', foreign_keys=[target_node_id], backref='edges_in')

    def __repr__(self):
        return f'<KnowledgeEdge {self.source_node_id} -> {self.target_node_id} rel={self.relationship}>'

    def to_dict(self):
        return {
            'id': self.id,
            'source_node_id': self.source_node_id,
            'target_node_id': self.target_node_id,
            'relationship': self.relationship
        }
