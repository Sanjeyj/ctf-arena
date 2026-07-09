"""
SystemicRiskGraphService — Phase 39: Systemic Cyber Risk, Collective Resilience
& Federated Governance Fabric.

Builds and analyzes the systemic dependency graph.
All operations are offline, simulation-only, and tenant-isolated.
"""
import math
from app.extensions import db
from app.models.systemic_risk_node import SystemicRiskNode
from app.models.systemic_dependency import SystemicDependency


VALID_NODE_TYPES = [
    'organization', 'service', 'vendor', 'cloud_region', 'sector',
    'platform', 'shared_dependency', 'coordination_center'
]

VALID_DEPENDENCY_TYPES = [
    'technical', 'vendor', 'cloud', 'identity', 'data', 'operational',
    'financial_simulation', 'coordination', 'intelligence', 'recovery'
]

MAX_GRAPH_DEPTH = 20


class SystemicRiskGraphService:

    @staticmethod
    def register_projection(name, node_type, reference_type, reference_id,
                            sector, region, org_id, **scores):
        """Register a graph projection node. Reuses existing projection for same reference."""
        if node_type not in VALID_NODE_TYPES:
            raise ValueError(f"Invalid node_type: {node_type}")

        # Prevent duplicates within tenant
        if reference_type and reference_id:
            existing = SystemicRiskNode.query.filter_by(
                organization_id=org_id,
                reference_type=reference_type,
                reference_id=reference_id
            ).first()
            if existing:
                return existing

        node = SystemicRiskNode(
            name=name,
            node_type=node_type,
            reference_type=reference_type,
            reference_id=reference_id,
            sector=sector,
            region=region,
            criticality_score=max(0.0, min(100.0, scores.get('criticality_score', 50.0))),
            dependency_score=max(0.0, min(100.0, scores.get('dependency_score', 50.0))),
            concentration_score=max(0.0, min(100.0, scores.get('concentration_score', 50.0))),
            resilience_score=max(0.0, min(100.0, scores.get('resilience_score', 50.0))),
            status='active',
            organization_id=org_id
        )
        db.session.add(node)
        db.session.commit()
        return node

    @staticmethod
    def resolve_reference(reference_type, reference_id, org_id):
        """Resolve a reference to a registered SystemicRiskNode."""
        return SystemicRiskNode.query.filter_by(
            organization_id=org_id,
            reference_type=reference_type,
            reference_id=reference_id
        ).first()

    @staticmethod
    def add_dependency(source_node_id, target_node_id, dep_type, strength,
                       substitutability, recovery_dep, propagation_prob,
                       trust_dep, org_id):
        """Add a directed dependency edge between two tenant-owned nodes."""
        if dep_type not in VALID_DEPENDENCY_TYPES:
            raise ValueError(f"Invalid dependency_type: {dep_type}")

        # Tenant isolation check
        source = SystemicRiskNode.query.filter_by(id=source_node_id, organization_id=org_id).first()
        target = SystemicRiskNode.query.filter_by(id=target_node_id, organization_id=org_id).first()
        if not source or not target:
            raise ValueError("Source or target node not found in this tenant")

        if source_node_id == target_node_id:
            raise ValueError("Self-edges are not permitted")

        # Check for existing edge
        existing = SystemicDependency.query.filter_by(
            organization_id=org_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id
        ).first()
        if existing:
            raise ValueError("Dependency edge already exists")

        dep = SystemicDependency(
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            dependency_type=dep_type,
            dependency_strength=max(0.0, min(100.0, strength)),
            substitutability_score=max(0.0, min(100.0, substitutability)),
            recovery_dependency_score=max(0.0, min(100.0, recovery_dep)),
            propagation_probability=max(0.0, min(1.0, propagation_prob)),
            trust_dependency_score=max(0.0, min(100.0, trust_dep)),
            status='active',
            organization_id=org_id
        )
        db.session.add(dep)
        db.session.commit()
        return dep

    @staticmethod
    def validate_dependency(source_node_id, target_node_id, org_id):
        """Validate that a dependency edge is valid (tenant-owned, no self-edge)."""
        if source_node_id == target_node_id:
            return False, "Self-edge rejected"
        source = SystemicRiskNode.query.filter_by(id=source_node_id, organization_id=org_id).first()
        target = SystemicRiskNode.query.filter_by(id=target_node_id, organization_id=org_id).first()
        if not source or not target:
            return False, "Cross-tenant edge rejected"
        return True, "Valid"

    @staticmethod
    def build_graph(org_id):
        """Build adjacency list representation of the dependency graph."""
        nodes = SystemicRiskNode.query.filter_by(organization_id=org_id, status='active').all()
        deps = SystemicDependency.query.filter_by(organization_id=org_id, status='active').all()

        graph = {n.id: {'node': n, 'outbound': [], 'inbound': []} for n in nodes}
        for dep in deps:
            if dep.source_node_id in graph and dep.target_node_id in graph:
                graph[dep.source_node_id]['outbound'].append(dep)
                graph[dep.target_node_id]['inbound'].append(dep)
        return graph

    @staticmethod
    def calculate_node_centrality(org_id):
        """Calculate degree centrality for each node (in + out degree)."""
        graph = SystemicRiskGraphService.build_graph(org_id)
        centrality = {}
        total = max(1, len(graph) - 1)
        for node_id, data in graph.items():
            degree = len(data['outbound']) + len(data['inbound'])
            centrality[node_id] = round(degree / total, 4)
        return centrality

    @staticmethod
    def calculate_concentration_risk(org_id):
        """Identify nodes with high inbound dependency count (concentration points)."""
        graph = SystemicRiskGraphService.build_graph(org_id)
        result = []
        for node_id, data in graph.items():
            inbound_count = len(data['inbound'])
            if inbound_count >= 2:
                node = data['node']
                result.append({
                    'node_id': node_id,
                    'name': node.name,
                    'inbound_dependencies': inbound_count,
                    'concentration_score': node.concentration_score
                })
        result.sort(key=lambda x: x['inbound_dependencies'], reverse=True)
        return result

    @staticmethod
    def identify_systemic_nodes(org_id, threshold=70.0):
        """Identify nodes that are systemically important (high criticality)."""
        nodes = SystemicRiskNode.query.filter_by(
            organization_id=org_id, status='active'
        ).filter(SystemicRiskNode.criticality_score >= threshold).all()
        return nodes

    @staticmethod
    def identify_single_points_of_failure(org_id):
        """Identify nodes with low substitutability and high inbound dependency count."""
        graph = SystemicRiskGraphService.build_graph(org_id)
        spofs = []
        for node_id, data in graph.items():
            inbound = data['inbound']
            if len(inbound) >= 2:
                avg_sub = sum(d.substitutability_score for d in inbound) / len(inbound)
                if avg_sub <= 30.0:
                    spofs.append({
                        'node_id': node_id,
                        'name': data['node'].name,
                        'inbound_count': len(inbound),
                        'avg_substitutability': round(avg_sub, 2)
                    })
        return spofs

    @staticmethod
    def graph_summary(org_id):
        """Return aggregate summary of the dependency graph."""
        graph = SystemicRiskGraphService.build_graph(org_id)
        nodes = SystemicRiskNode.query.filter_by(organization_id=org_id).all()
        deps = SystemicDependency.query.filter_by(organization_id=org_id).all()
        spofs = SystemicRiskGraphService.identify_single_points_of_failure(org_id)
        systemic = SystemicRiskGraphService.identify_systemic_nodes(org_id)
        return {
            'total_nodes': len(nodes),
            'total_dependencies': len(deps),
            'active_nodes': sum(1 for n in nodes if n.status == 'active'),
            'single_points_of_failure': len(spofs),
            'systemically_important_nodes': len(systemic),
            'avg_resilience_score': round(
                sum(n.resilience_score for n in nodes) / max(1, len(nodes)), 2
            )
        }
