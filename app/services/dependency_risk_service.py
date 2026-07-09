"""
DependencyRiskService - Phase 37 Strategic Cyber Resilience.
"""
from app.extensions import db
from app.models.business_dependency_risk import BusinessDependencyRisk
from app.models.business_process import BusinessProcess


class DependencyRiskService:
    @staticmethod
    def map_dependency(business_process_id, dep_ref_type, dep_ref_id, dep_type, criticality, org_id):
        bp = BusinessProcess.query.filter_by(id=business_process_id, organization_id=org_id).first()
        if not bp:
            raise ValueError("Business process not found or access denied")

        allowed_types = ['service', 'vendor', 'cloud_region', 'application', 'identity', 'network_simulation', 'data', 'security_control']
        if dep_type not in allowed_types:
            raise ValueError(f"Invalid dependency_type. Must be one of: {allowed_types}")

        dep = BusinessDependencyRisk(
            business_process_id=business_process_id,
            dependency_reference_type=dep_ref_type,
            dependency_reference_id=dep_ref_id,
            dependency_type=dep_type,
            criticality_score=criticality,
            concentration_risk_score=0.0,
            failure_impact_score=0.0,
            recovery_dependency_score=0.0,
            status='active',
            organization_id=org_id
        )
        db.session.add(dep)
        db.session.commit()

        # Update scores
        dep.concentration_risk_score = DependencyRiskService.calculate_concentration_risk(dep_ref_type, dep_ref_id, org_id)
        dep.failure_impact_score = DependencyRiskService.calculate_failure_impact(dep.id, org_id)
        dep.recovery_dependency_score = DependencyRiskService.calculate_recovery_dependency(dep.id, org_id)
        db.session.commit()

        return dep

    @staticmethod
    def calculate_concentration_risk(dep_ref_type, dep_ref_id, org_id):
        # Count business processes sharing this exact dependency reference
        shared = BusinessDependencyRisk.query.filter_by(
            dependency_reference_type=dep_ref_type,
            dependency_reference_id=dep_ref_id,
            organization_id=org_id
        ).all()
        # Scale: processes count * 20.0 clamped to 100.0
        score = min(100.0, max(0.0, len(shared) * 20.0))
        return round(score, 2)

    @staticmethod
    def calculate_failure_impact(dependency_id, org_id):
        dep = BusinessDependencyRisk.query.filter_by(id=dependency_id, organization_id=org_id).first()
        if not dep:
            return 0.0
        bp = BusinessProcess.query.get(dep.business_process_id)
        bp_sev = {'low': 20.0, 'medium': 50.0, 'high': 80.0, 'critical': 100.0}
        bp_score = bp_sev.get(bp.criticality, 50.0) if bp else 50.0

        # Avg of process criticality and dependency criticality
        val = (bp_score + dep.criticality_score) / 2.0
        return round(val, 2)

    @staticmethod
    def calculate_recovery_dependency(dependency_id, org_id):
        dep = BusinessDependencyRisk.query.filter_by(id=dependency_id, organization_id=org_id).first()
        if not dep:
            return 0.0
        # Recovery objective duration dependencies
        bp = BusinessProcess.query.get(dep.business_process_id)
        rto = bp.rto if bp else 4.0
        # Lower RTO = higher dependency score: score = max(0.0, 100 - (RTO * 10))
        score = min(100.0, max(0.0, 100.0 - (rto * 10.0)))
        return round(score, 2)

    @staticmethod
    def find_single_points_of_failure(org_id):
        # Single point of failure: concentration risk > 60 or criticality_score > 80
        deps = BusinessDependencyRisk.query.filter_by(organization_id=org_id).all()
        spofs = []
        for d in deps:
            if d.criticality_score >= 80.0 or d.concentration_risk_score >= 60.0:
                spofs.append(d)
        return spofs

    @staticmethod
    def rank_critical_dependencies(org_id):
        deps = BusinessDependencyRisk.query.filter_by(organization_id=org_id).all()
        return sorted(deps, key=lambda x: x.failure_impact_score, reverse=True)

    @staticmethod
    def dependency_summary(org_id):
        deps = BusinessDependencyRisk.query.filter_by(organization_id=org_id).all()
        spofs = DependencyRiskService.find_single_points_of_failure(org_id)
        return {
            "total_dependencies": len(deps),
            "spof_count": len(spofs),
            "max_concentration_score": max([d.concentration_risk_score for d in deps]) if deps else 0.0
        }
