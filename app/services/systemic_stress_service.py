"""
SystemicStressService — Phase 39: Systemic Cyber Risk, Collective Resilience
& Federated Governance Fabric.

Applies correlated multi-node stress scenarios. Reuses Phase 36/37 stress data
where applicable. All operations are offline and simulation-only.
"""
from app.extensions import db
from app.models.systemic_risk_node import SystemicRiskNode
from app.models.contagion_simulation_run import ContagionSimulationRun


class SystemicStressService:

    @staticmethod
    def create_correlated_stress(node_ids, correlation_factor, org_id):
        """Create a correlated stress payload across a set of nodes."""
        if not (0.0 <= correlation_factor <= 1.0):
            raise ValueError("correlation_factor must be 0-1")

        nodes = SystemicRiskNode.query.filter(
            SystemicRiskNode.id.in_(node_ids),
            SystemicRiskNode.organization_id == org_id
        ).all()

        if len(nodes) != len(node_ids):
            raise ValueError("One or more nodes not found in this tenant")

        return {
            'node_count': len(nodes),
            'correlation_factor': correlation_factor,
            'avg_criticality': round(sum(n.criticality_score for n in nodes) / len(nodes), 2),
            'avg_resilience': round(sum(n.resilience_score for n in nodes) / len(nodes), 2),
        }

    @staticmethod
    def apply_multi_node_failure(node_ids, failure_impact, org_id):
        """Apply a simultaneous failure event to multiple nodes and calculate aggregate impact."""
        nodes = SystemicRiskNode.query.filter(
            SystemicRiskNode.id.in_(node_ids),
            SystemicRiskNode.organization_id == org_id
        ).all()

        if not nodes:
            return {'aggregate_impact': 0.0, 'nodes_failed': 0}

        total_impact = 0.0
        for node in nodes:
            absorption = node.resilience_score / 100.0
            impact = failure_impact * (1.0 - absorption)
            total_impact += max(0.0, min(100.0, impact))

        aggregate = min(100.0, total_impact / len(nodes))
        return {
            'aggregate_impact': round(aggregate, 2),
            'nodes_failed': len(nodes),
            'total_raw_impact': round(total_impact, 2)
        }

    @staticmethod
    def calculate_aggregate_impact(node_ids, initial_impact, org_id):
        """Calculate total impact for a set of nodes given an initial impact value."""
        nodes = SystemicRiskNode.query.filter(
            SystemicRiskNode.id.in_(node_ids),
            SystemicRiskNode.organization_id == org_id
        ).all()
        total = sum(
            initial_impact * (1.0 - n.resilience_score / 100.0)
            for n in nodes
        )
        return round(min(100.0, total / max(1, len(nodes))), 2)

    @staticmethod
    def calculate_sector_impact(sector, initial_impact, org_id):
        """Calculate aggregate impact for all nodes in a given sector."""
        nodes = SystemicRiskNode.query.filter_by(
            sector=sector, organization_id=org_id, status='active'
        ).all()
        if not nodes:
            return {'sector': sector, 'nodes': 0, 'impact': 0.0}

        total = sum(initial_impact * (1.0 - n.resilience_score / 100.0) for n in nodes)
        avg = min(100.0, total / len(nodes))
        return {
            'sector': sector,
            'nodes': len(nodes),
            'impact': round(avg, 2)
        }

    @staticmethod
    def calculate_regional_impact(region, initial_impact, org_id):
        """Calculate aggregate impact for all nodes in a given region."""
        nodes = SystemicRiskNode.query.filter_by(
            region=region, organization_id=org_id, status='active'
        ).all()
        if not nodes:
            return {'region': region, 'nodes': 0, 'impact': 0.0}

        total = sum(initial_impact * (1.0 - n.resilience_score / 100.0) for n in nodes)
        avg = min(100.0, total / len(nodes))
        return {
            'region': region,
            'nodes': len(nodes),
            'impact': round(avg, 2)
        }

    @staticmethod
    def compare_stress_runs(run_id_a, run_id_b, org_id):
        """Compare two simulation runs by aggregate impact and resilience score."""
        run_a = ContagionSimulationRun.query.filter_by(id=run_id_a, organization_id=org_id).first()
        run_b = ContagionSimulationRun.query.filter_by(id=run_id_b, organization_id=org_id).first()
        if not run_a or not run_b:
            raise ValueError("One or both simulation runs not found in this tenant")

        return {
            'run_a_id': run_id_a,
            'run_b_id': run_id_b,
            'impact_diff': round(run_a.aggregate_impact_score - run_b.aggregate_impact_score, 2),
            'resilience_diff': round(
                run_a.collective_resilience_score - run_b.collective_resilience_score, 2
            ),
            'nodes_diff': run_a.nodes_affected - run_b.nodes_affected,
        }

    @staticmethod
    def identify_concentration_failures(org_id, threshold=3):
        """Identify nodes depended on by more than `threshold` other nodes."""
        from app.models.systemic_dependency import SystemicDependency
        from sqlalchemy import func

        results = (
            db.session.query(
                SystemicDependency.target_node_id,
                func.count(SystemicDependency.id).label('dep_count')
            )
            .filter(SystemicDependency.organization_id == org_id)
            .group_by(SystemicDependency.target_node_id)
            .having(func.count(SystemicDependency.id) >= threshold)
            .all()
        )

        concentration = []
        for row in results:
            node = SystemicRiskNode.query.get(row.target_node_id)
            if node and node.organization_id == org_id:
                concentration.append({
                    'node_id': row.target_node_id,
                    'name': node.name,
                    'dependency_count': row.dep_count,
                    'concentration_score': node.concentration_score
                })
        return concentration

    @staticmethod
    def stress_summary(org_id):
        """Return aggregate summary of stress analysis for this tenant."""
        nodes = SystemicRiskNode.query.filter_by(organization_id=org_id).all()
        sectors = list({n.sector for n in nodes if n.sector})
        regions = list({n.region for n in nodes if n.region})
        concentration = SystemicStressService.identify_concentration_failures(org_id)
        return {
            'total_nodes': len(nodes),
            'sectors': sectors,
            'regions': regions,
            'concentration_failure_nodes': len(concentration),
        }
