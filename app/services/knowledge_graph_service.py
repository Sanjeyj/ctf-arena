"""
KnowledgeGraph Service - Phase 21 Security Knowledge Graph.
Manages nodes (entities) and edges (relationships) linking Actors, Campaigns,
Malware, IOCs, and Incidents.
"""
import json
from app.extensions import db
from app.models.knowledge_node import KnowledgeNode
from app.models.knowledge_edge import KnowledgeEdge

class KnowledgeGraphService:

    @staticmethod
    def add_node(node_type: str, name: str, properties: dict = None, org_id: int = None) -> KnowledgeNode:
        node = KnowledgeNode(
            node_type=node_type,
            name=name,
            properties_json=json.dumps(properties or {}),
            organization_id=org_id
        )
        db.session.add(node)
        db.session.commit()
        return node

    @staticmethod
    def add_edge(source_node_id: int, target_node_id: int, relationship: str, org_id: int = None) -> KnowledgeEdge:
        edge = KnowledgeEdge(
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            relationship=relationship,
            organization_id=org_id
        )
        db.session.add(edge)
        db.session.commit()
        return edge

    @staticmethod
    def get_full_graph(org_id: int = None) -> dict:
        """Retrieve compiled nodes and links mapping representation for visualization."""
        node_query = KnowledgeNode.query
        edge_query = KnowledgeEdge.query
        
        if org_id:
            node_query = node_query.filter_by(organization_id=org_id)
            edge_query = edge_query.filter_by(organization_id=org_id)
            
        nodes = node_query.all()
        edges = edge_query.all()
        
        return {
            "nodes": [n.to_dict() for n in nodes],
            "links": [e.to_dict() for e in edges]
        }
