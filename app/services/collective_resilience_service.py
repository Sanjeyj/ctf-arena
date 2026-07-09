"""
CollectiveResilienceService — Phase 39: Systemic Cyber Risk, Collective Resilience
& Federated Governance Fabric.

Manages collective resilience plans. Approval requires explicit human action.
All operations are offline and simulation-only.
"""
import json
from app.extensions import db
from app.models.collective_resilience_plan import CollectiveResiliencePlan
from app.models.systemic_risk_node import SystemicRiskNode

VALID_PLAN_TYPES = [
    'dependency_diversification', 'shared_recovery', 'mutual_aid_simulation',
    'collective_control', 'sector_resilience', 'regional_resilience',
    'shared_service_recovery'
]


class CollectiveResilienceService:

    @staticmethod
    def create_plan(name, scope, plan_type, participating_node_ids,
                    estimated_cost, org_id):
        """Create a new collective resilience plan."""
        if plan_type not in VALID_PLAN_TYPES:
            raise ValueError(f"Invalid plan_type: {plan_type}")
        if estimated_cost < 0:
            raise ValueError("estimated_cost must be >= 0")

        # Validate all nodes belong to this tenant
        for node_id in participating_node_ids:
            node = SystemicRiskNode.query.filter_by(id=node_id, organization_id=org_id).first()
            if not node:
                raise ValueError(f"Node {node_id} not found in this tenant")

        plan = CollectiveResiliencePlan(
            name=name,
            scope=scope,
            plan_type=plan_type,
            participating_nodes_json=json.dumps(participating_node_ids),
            estimated_cost=estimated_cost,
            baseline_resilience_score=0.0,
            target_resilience_score=0.0,
            expected_systemic_risk_reduction=0.0,
            priority_score=0.0,
            approval_status='pending',
            status='draft',
            organization_id=org_id
        )
        db.session.add(plan)
        db.session.commit()
        return plan

    @staticmethod
    def calculate_baseline(plan_id, org_id):
        """Calculate current average resilience score of participating nodes."""
        plan = CollectiveResiliencePlan.query.filter_by(id=plan_id, organization_id=org_id).first()
        if not plan:
            raise ValueError("CollectiveResiliencePlan not found")

        node_ids = json.loads(plan.participating_nodes_json or '[]')
        if not node_ids:
            return 0.0

        nodes = SystemicRiskNode.query.filter(
            SystemicRiskNode.id.in_(node_ids),
            SystemicRiskNode.organization_id == org_id
        ).all()
        baseline = sum(n.resilience_score for n in nodes) / max(1, len(nodes))
        plan.baseline_resilience_score = round(baseline, 2)
        db.session.commit()
        return plan.baseline_resilience_score

    @staticmethod
    def calculate_target(plan_id, improvement_factor, org_id):
        """Estimate target resilience after plan implementation."""
        plan = CollectiveResiliencePlan.query.filter_by(id=plan_id, organization_id=org_id).first()
        if not plan:
            raise ValueError("CollectiveResiliencePlan not found")
        if not (0.0 <= improvement_factor <= 1.0):
            raise ValueError("improvement_factor must be 0-1")

        target = min(100.0, plan.baseline_resilience_score * (1.0 + improvement_factor))
        plan.target_resilience_score = round(target, 2)
        db.session.commit()
        return plan.target_resilience_score

    @staticmethod
    def estimate_risk_reduction(plan_id, org_id):
        """Estimate systemic risk reduction from plan implementation."""
        plan = CollectiveResiliencePlan.query.filter_by(id=plan_id, organization_id=org_id).first()
        if not plan:
            raise ValueError("CollectiveResiliencePlan not found")

        delta = plan.target_resilience_score - plan.baseline_resilience_score
        reduction = max(0.0, min(100.0, delta * 0.8))
        plan.expected_systemic_risk_reduction = round(reduction, 2)
        db.session.commit()
        return plan.expected_systemic_risk_reduction

    @staticmethod
    def rank_plans(org_id):
        """Rank all plans by priority score descending."""
        plans = CollectiveResiliencePlan.query.filter_by(organization_id=org_id).all()
        for p in plans:
            # Priority = risk_reduction * 0.6 + (100 - cost/1000) * 0.4 clamped
            cost_factor = max(0.0, 100.0 - (p.estimated_cost / 1000.0))
            p.priority_score = round(
                min(100.0, p.expected_systemic_risk_reduction * 0.6 + cost_factor * 0.4), 2
            )
        db.session.commit()
        return sorted(plans, key=lambda p: p.priority_score, reverse=True)

    @staticmethod
    def evaluate_plan(plan_id, improvement_factor, org_id):
        """Run full plan evaluation: baseline → target → risk reduction → ranking."""
        CollectiveResilienceService.calculate_baseline(plan_id, org_id)
        CollectiveResilienceService.calculate_target(plan_id, improvement_factor, org_id)
        CollectiveResilienceService.estimate_risk_reduction(plan_id, org_id)
        plan = CollectiveResiliencePlan.query.filter_by(id=plan_id, organization_id=org_id).first()
        return plan

    @staticmethod
    def approve_plan(plan_id, approved_by, org_id):
        """Human-driven approval of a resilience plan."""
        if not approved_by or not approved_by.strip():
            raise ValueError("approved_by is required for plan approval")
        plan = CollectiveResiliencePlan.query.filter_by(id=plan_id, organization_id=org_id).first()
        if not plan:
            raise ValueError("CollectiveResiliencePlan not found")
        if plan.approval_status == 'approved':
            return plan
        plan.approval_status = 'approved'
        plan.status = 'active'
        db.session.commit()
        return plan

    @staticmethod
    def collective_resilience_summary(org_id):
        """Return summary statistics for all collective resilience plans."""
        plans = CollectiveResiliencePlan.query.filter_by(organization_id=org_id).all()
        approved = [p for p in plans if p.approval_status == 'approved']
        avg_reduction = (
            sum(p.expected_systemic_risk_reduction for p in plans) / len(plans)
            if plans else 0.0
        )
        return {
            'total_plans': len(plans),
            'approved_plans': len(approved),
            'avg_expected_risk_reduction': round(avg_reduction, 2),
        }
