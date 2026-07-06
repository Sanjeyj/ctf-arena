"""
TopologyService - Phase 30 Unified Cyber Defense Universe.
Controls topology nodes registration, linkage creation, dependency mapping, and defensive critical paths validation.
"""
from app.extensions import db
from app.models.defense_domain import DefenseDomain
from app.models.universe_node import UniverseNode
from app.models.universe_link import UniverseLink
import json


class TopologyService:
    @staticmethod
    def add_domain(universe_id: int, name: str, domain_type: str, org_id: int) -> DefenseDomain:
        """Add a defense domain to the universe."""
        dom = DefenseDomain(
            universe_id=universe_id,
            name=name,
            domain_type=domain_type,
            health_score=1.0,
            readiness_score=0.5,
            status='healthy',
            organization_id=org_id
        )
        db.session.add(dom)
        db.session.commit()
        return dom

    @staticmethod
    def add_node(universe_id: int, domain_id: int, node_name: str, node_type: str, org_id: int, region: str = None, criticality: str = 'medium', metadata: dict = None) -> UniverseNode:
        """Add an asset/capability node to the topological tree."""
        meta_str = json.dumps(metadata) if metadata else None
        node = UniverseNode(
            universe_id=universe_id,
            domain_id=domain_id,
            node_name=node_name,
            node_type=node_type,
            region=region,
            criticality=criticality,
            health_score=1.0,
            status='online',
            metadata_json=meta_str,
            organization_id=org_id
        )
        db.session.add(node)
        db.session.commit()
        return node

    @staticmethod
    def link_nodes(universe_id: int, source_node_id: int, target_node_id: int, relationship_type: str, org_id: int, dependency_weight: float = 1.0, trust_score: float = 1.0) -> UniverseLink:
        """Link two nodes by representing trust or capability dependencies."""
        link = UniverseLink(
            universe_id=universe_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            relationship_type=relationship_type,
            dependency_weight=dependency_weight,
            trust_score=trust_score,
            status='active',
            organization_id=org_id
        )
        db.session.add(link)
        db.session.commit()
        return link

    @staticmethod
    def validate_topology(universe_id: int, org_id: int) -> dict:
        """Validate topological soundness (e.g. check for orphaned domains/nodes)."""
        nodes = UniverseNode.query.filter_by(universe_id=universe_id, organization_id=org_id).all()
        links = UniverseLink.query.filter_by(universe_id=universe_id, organization_id=org_id).all()

        linked_nodes = set()
        for link in links:
            linked_nodes.add(link.source_node_id)
            linked_nodes.add(link.target_node_id)

        orphans = [n.id for n in nodes if n.id not in linked_nodes]
        status = 'valid' if not orphans else 'warning'
        return {
            'universe_id': universe_id,
            'total_nodes': len(nodes),
            'total_links': len(links),
            'orphaned_nodes': orphans,
            'status': status
        }

    @staticmethod
    def dependency_map(universe_id: int, org_id: int) -> dict:
        """Generate downstream and upstream dependencies registry for topology rendering."""
        nodes = UniverseNode.query.filter_by(universe_id=universe_id, organization_id=org_id).all()
        links = UniverseLink.query.filter_by(universe_id=universe_id, organization_id=org_id).all()

        node_dict = {n.id: n.to_dict() for n in nodes}
        adj = {n.id: [] for n in nodes}
        for link in links:
            if link.source_node_id in adj:
                adj[link.source_node_id].append({
                    'target_node_id': link.target_node_id,
                    'type': link.relationship_type,
                    'weight': link.dependency_weight
                })

        return {
            'nodes': node_dict,
            'adjacency_list': adj
        }

    @staticmethod
    def calculate_critical_paths(universe_id: int, org_id: int) -> list:
        """Trace defensive dependency graph looking for critical nodes."""
        nodes = UniverseNode.query.filter_by(universe_id=universe_id, organization_id=org_id).all()
        links = UniverseLink.query.filter_by(universe_id=universe_id, organization_id=org_id).all()

        # Build incoming link counts
        incoming = {n.id: 0 for n in nodes}
        for link in links:
            if link.target_node_id in incoming:
                incoming[link.target_node_id] += 1

        # Sort nodes descending by criticality rating and dependency weight
        critical_paths = []
        for n in nodes:
            score = incoming.get(n.id, 0) * 1.5
            if n.criticality == 'critical':
                score += 3.0
            elif n.criticality == 'high':
                score += 2.0
            critical_paths.append({
                'node_id': n.id,
                'node_name': n.node_name,
                'weight': score
            })

        critical_paths.sort(key=lambda x: x['weight'], reverse=True)
        return critical_paths
