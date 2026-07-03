"""
IntelligenceGraph model - Phase 27 Global Security Intelligence Network.
Represents a node/edge entry in the federated security knowledge graph.
"""
import json
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class IntelligenceGraph(db.Model, TimestampMixin, TenantMixin):
    """Security intelligence knowledge graph node."""
    __tablename__ = 'intelligence_graphs'

    id = db.Column(db.Integer, primary_key=True)
    node_type = db.Column(db.String(64), nullable=False)  # actor, ttp, ioc, campaign, asset
    relationship = db.Column(db.String(64), nullable=False)  # uses, targets, attributes_to, related_to
    confidence = db.Column(db.Float, default=0.7, nullable=False)
    meta = db.Column(db.Text, nullable=True)  # JSON-encoded metadata

    def get_meta(self) -> dict:
        """Deserialize JSON metadata."""
        if self.meta:
            try:
                return json.loads(self.meta)
            except (ValueError, TypeError):
                return {}
        return {}

    def set_meta(self, data: dict):
        """Serialize metadata to JSON."""
        self.meta = json.dumps(data)

    def __repr__(self):
        return f'<IntelligenceGraph {self.node_type!r} -> {self.relationship!r}>'

    def to_dict(self):
        return {
            'id': self.id,
            'node_type': self.node_type,
            'relationship': self.relationship,
            'confidence': self.confidence,
            'meta': self.get_meta(),
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
