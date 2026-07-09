"""
MutualAidSimulationService — Phase 39: Systemic Cyber Risk, Collective Resilience
& Federated Governance Fabric.

Manages simulated mutual-aid capacity allocation between nodes.
NO real communication, resource dispatch, or external API calls.
Human approval is required before allocation is considered active.
"""
from app.extensions import db
from app.models.mutual_aid_simulation import MutualAidSimulation
from app.models.systemic_risk_node import SystemicRiskNode

VALID_ASSISTANCE_TYPES = [
    'recovery_capacity', 'resilience_boost', 'coordination_support',
    'technical_assistance', 'shared_control', 'information_sharing'
]


class MutualAidSimulationService:

    @staticmethod
    def calculate_available_capacity(provider_node_id, org_id):
        """Calculate capacity still available at a provider node."""
        node = SystemicRiskNode.query.filter_by(id=provider_node_id, organization_id=org_id).first()
        if not node:
            raise ValueError("Provider node not found")

        # Available capacity derived from node resilience score
        base_capacity = node.resilience_score
        already_allocated = sum(
            aid.capacity_allocated for aid in
            MutualAidSimulation.query.filter_by(
                provider_node_id=provider_node_id,
                organization_id=org_id,
                status='allocated_simulation'
            ).all()
        )
        return max(0.0, base_capacity - already_allocated)

    @staticmethod
    def identify_recipients(run_id, org_id):
        """Identify nodes in a simulation run that received significant impact."""
        from app.models.contagion_event import ContagionEvent
        events = ContagionEvent.query.filter_by(
            simulation_run_id=run_id,
            event_type='dependency_propagation',
            organization_id=org_id
        ).all()
        recipient_ids = list({e.target_node_id for e in events if e.target_node_id})
        recipients = SystemicRiskNode.query.filter(
            SystemicRiskNode.id.in_(recipient_ids),
            SystemicRiskNode.organization_id == org_id
        ).all()
        return recipients

    @staticmethod
    def calculate_allocation_score(capacity_available, capacity_requested,
                                   recipient_resilience, provider_resilience):
        """Calculate a scoring metric for the proposed allocation."""
        if capacity_available <= 0:
            return 0.0
        coverage = min(1.0, capacity_requested / max(1.0, capacity_available))
        need_factor = 1.0 - (recipient_resilience / 100.0)
        provider_factor = provider_resilience / 100.0
        score = coverage * need_factor * provider_factor * 100.0
        return round(max(0.0, min(100.0, score)), 2)

    @staticmethod
    def allocate_simulated_capacity(provider_node_id, recipient_node_id,
                                    assistance_type, capacity_requested,
                                    run_id, org_id):
        """Create a simulated aid allocation record."""
        if assistance_type not in VALID_ASSISTANCE_TYPES:
            raise ValueError(f"Invalid assistance_type: {assistance_type}")
        if capacity_requested < 0:
            raise ValueError("capacity_requested must be >= 0")

        available = MutualAidSimulationService.calculate_available_capacity(
            provider_node_id, org_id
        )
        if capacity_requested > available:
            raise ValueError(
                f"Requested {capacity_requested} exceeds available {available:.2f}"
            )

        provider = SystemicRiskNode.query.filter_by(id=provider_node_id, organization_id=org_id).first()
        recipient = SystemicRiskNode.query.filter_by(id=recipient_node_id, organization_id=org_id).first()
        if not provider or not recipient:
            raise ValueError("Provider or recipient node not found in this tenant")

        score = MutualAidSimulationService.calculate_allocation_score(
            available, capacity_requested,
            recipient.resilience_score, provider.resilience_score
        )
        recovery_gain = MutualAidSimulationService.estimate_recovery_gain(
            capacity_requested, recipient.resilience_score
        )

        aid = MutualAidSimulation(
            simulation_run_id=run_id,
            provider_node_id=provider_node_id,
            recipient_node_id=recipient_node_id,
            assistance_type=assistance_type,
            capacity_available=available,
            capacity_allocated=capacity_requested,
            estimated_recovery_gain=recovery_gain,
            allocation_score=score,
            approval_status='pending',
            status='simulated',
            organization_id=org_id
        )
        db.session.add(aid)
        db.session.commit()
        return aid

    @staticmethod
    def estimate_recovery_gain(capacity_allocated, recipient_resilience):
        """Estimate recovery improvement from simulated aid allocation."""
        resilience_gap = 1.0 - (recipient_resilience / 100.0)
        gain = capacity_allocated * resilience_gap * 0.3
        return round(max(0.0, min(100.0, gain)), 2)

    @staticmethod
    def validate_allocation(aid_id, org_id):
        """Validate that an allocation record is within bounds."""
        aid = MutualAidSimulation.query.filter_by(id=aid_id, organization_id=org_id).first()
        if not aid:
            raise ValueError("MutualAidSimulation not found")
        if aid.capacity_allocated > aid.capacity_available:
            return False
        if aid.estimated_recovery_gain < 0:
            return False
        return True

    @staticmethod
    def approve_allocation(aid_id, org_id):
        """Human-driven approval of simulated mutual aid allocation."""
        aid = MutualAidSimulation.query.filter_by(id=aid_id, organization_id=org_id).first()
        if not aid:
            raise ValueError("MutualAidSimulation not found")
        if aid.approval_status == 'approved':
            return aid
        aid.approval_status = 'approved'
        aid.status = 'allocated_simulation'
        db.session.commit()
        return aid

    @staticmethod
    def allocation_summary(org_id):
        """Return aggregate summary of mutual aid allocations."""
        records = MutualAidSimulation.query.filter_by(organization_id=org_id).all()
        approved = [r for r in records if r.approval_status == 'approved']
        total_gain = sum(r.estimated_recovery_gain for r in approved)
        return {
            'total_simulations': len(records),
            'approved_allocations': len(approved),
            'total_estimated_recovery_gain': round(total_gain, 2),
        }
