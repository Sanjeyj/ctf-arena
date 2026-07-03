"""
KnowledgeNode model - Phase 21 Security Knowledge Graph.
Nodes represent entities (Actor, Campaign, Malware, IOC, Detection, Incident).
"""
import json
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin

class KnowledgeNode(db.Model, TimestampMixin, TenantMixin):
    """Node entity in CTI security relationship network."""
    __tablename__ = 'knowledge_nodes'

    id = db.Column(db.Integer, primary_key=True)
    node_type = db.Column(db.String(32), nullable=False) # actor, campaign, malware, ioc, detection, incident
    name = db.Column(db.String(256), nullable=False, index=True)
    properties_json = db.Column('properties', db.Text, default='{}')

    def __repr__(self):
        return f'<KnowledgeNode {self.name!r} type={self.node_type}>'

    def to_dict(self):
        try:
            props = json.loads(self.properties_json) if self.properties_json else {}
        except Exception:
            props = {}
            
        return {
            'id': self.id,
            'node_type': self.node_type,
            'name': self.name,
            'properties': props
        }
