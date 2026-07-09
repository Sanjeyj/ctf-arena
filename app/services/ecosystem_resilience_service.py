"""
EcosystemResilienceService — Phase 39: Systemic Cyber Risk, Collective Resilience
& Federated Governance Fabric.

Calculates composite ecosystem resilience index using documented weighted formula.
Weights must sum to exactly 100%.

Dependency Resilience:      25%
Sector Resilience:          20%
Regional Resilience:        15%
Collective Readiness:       20%
Recovery Capacity:          20%
Total:                     100%
"""
from app.extensions import db
from app.models.systemic_risk_node import SystemicRiskNode
from app.models.systemic_dependency import SystemicDependency
from app.models.collective_resilience_plan import CollectiveResiliencePlan
from app.models.contagion_simulation_run import ContagionSimulationRun

ECOSYSTEM_WEIGHTS = {
    'dependency_resilience': 0.25,
    'sector_resilience': 0.20,
    'regional_resilience': 0.15,
    'collective_readiness': 0.20,
    'recovery_capacity': 0.20,
}

assert abs(sum(ECOSYSTEM_WEIGHTS.values()) - 1.0) < 1e-9, "Ecosystem weights must sum to 100%"


class EcosystemResilienceService:

    @staticmethod
    def calculate_dependency_resilience(org_id):
        """Average resilience score weighted by dependency strength."""
        deps = SystemicDependency.query.filter_by(organization_id=org_id, status='active').all()
        if not deps:
            return 50.0

        total_weight = sum(d.dependency_strength for d in deps)
        if total_weight == 0:
            return 50.0

        weighted_sum = 0.0
        for dep in deps:
            node = SystemicRiskNode.query.get(dep.target_node_id)
            if node and node.organization_id == org_id:
                weighted_sum += node.resilience_score * dep.dependency_strength

        return round(max(0.0, min(100.0, weighted_sum / total_weight)), 2)

    @staticmethod
    def calculate_sector_resilience(org_id):
        """Average resilience score across all sectors (equal sector weighting)."""
        nodes = SystemicRiskNode.query.filter_by(organization_id=org_id, status='active').all()
        if not nodes:
            return 50.0

        sectors = {}
        for n in nodes:
            sector = n.sector or 'unknown'
            if sector not in sectors:
                sectors[sector] = []
            sectors[sector].append(n.resilience_score)

        sector_avgs = [sum(s) / len(s) for s in sectors.values()]
        return round(max(0.0, min(100.0, sum(sector_avgs) / max(1, len(sector_avgs)))), 2)

    @staticmethod
    def calculate_regional_resilience(org_id):
        """Average resilience score across all regions (equal region weighting)."""
        nodes = SystemicRiskNode.query.filter_by(organization_id=org_id, status='active').all()
        if not nodes:
            return 50.0

        regions = {}
        for n in nodes:
            region = n.region or 'unknown'
            if region not in regions:
                regions[region] = []
            regions[region].append(n.resilience_score)

        region_avgs = [sum(r) / len(r) for r in regions.values()]
        return round(max(0.0, min(100.0, sum(region_avgs) / max(1, len(region_avgs)))), 2)

    @staticmethod
    def calculate_collective_readiness(org_id):
        """Estimate collective readiness from approved resilience plans."""
        plans = CollectiveResiliencePlan.query.filter_by(
            organization_id=org_id, approval_status='approved'
        ).all()
        total = CollectiveResiliencePlan.query.filter_by(organization_id=org_id).count()
        if total == 0:
            return 50.0
        readiness = (len(plans) / total) * 100.0
        return round(max(0.0, min(100.0, readiness)), 2)

    @staticmethod
    def calculate_systemic_risk_index(org_id):
        """Composite systemic risk index using documented weights."""
        dep_res = EcosystemResilienceService.calculate_dependency_resilience(org_id)
        sec_res = EcosystemResilienceService.calculate_sector_resilience(org_id)
        reg_res = EcosystemResilienceService.calculate_regional_resilience(org_id)
        col_ready = EcosystemResilienceService.calculate_collective_readiness(org_id)
        rec_cap = EcosystemResilienceService.calculate_recovery_capacity(org_id)

        composite = (
            dep_res * ECOSYSTEM_WEIGHTS['dependency_resilience'] +
            sec_res * ECOSYSTEM_WEIGHTS['sector_resilience'] +
            reg_res * ECOSYSTEM_WEIGHTS['regional_resilience'] +
            col_ready * ECOSYSTEM_WEIGHTS['collective_readiness'] +
            rec_cap * ECOSYSTEM_WEIGHTS['recovery_capacity']
        )
        # Systemic risk is inverse of composite resilience
        systemic_risk = 100.0 - composite
        return round(max(0.0, min(100.0, systemic_risk)), 2)

    @staticmethod
    def calculate_recovery_capacity(org_id):
        """Estimate recovery capacity from completed simulations."""
        runs = ContagionSimulationRun.query.filter_by(
            organization_id=org_id, status='completed'
        ).all()
        if not runs:
            return 50.0
        avg_resilience = sum(r.collective_resilience_score for r in runs) / len(runs)
        return round(max(0.0, min(100.0, avg_resilience)), 2)

    @staticmethod
    def save_metrics(org_id):
        """Compute and return all ecosystem metrics as a dict."""
        dep_res = EcosystemResilienceService.calculate_dependency_resilience(org_id)
        sec_res = EcosystemResilienceService.calculate_sector_resilience(org_id)
        reg_res = EcosystemResilienceService.calculate_regional_resilience(org_id)
        col_ready = EcosystemResilienceService.calculate_collective_readiness(org_id)
        rec_cap = EcosystemResilienceService.calculate_recovery_capacity(org_id)
        systemic_risk = EcosystemResilienceService.calculate_systemic_risk_index(org_id)

        return {
            'dependency_resilience': dep_res,
            'sector_resilience': sec_res,
            'regional_resilience': reg_res,
            'collective_readiness': col_ready,
            'recovery_capacity': rec_cap,
            'systemic_risk_index': systemic_risk,
            'composite_resilience': round(100.0 - systemic_risk, 2),
        }

    @staticmethod
    def ecosystem_summary(org_id):
        """Full ecosystem summary including all metrics."""
        metrics = EcosystemResilienceService.save_metrics(org_id)
        nodes = SystemicRiskNode.query.filter_by(organization_id=org_id).count()
        deps = SystemicDependency.query.filter_by(organization_id=org_id).count()
        plans = CollectiveResiliencePlan.query.filter_by(organization_id=org_id).count()
        return {
            **metrics,
            'total_nodes': nodes,
            'total_dependencies': deps,
            'total_plans': plans,
            'weights': ECOSYSTEM_WEIGHTS,
        }
