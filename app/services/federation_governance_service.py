"""
FederationGovernanceService — Phase 39: Systemic Cyber Risk, Collective Resilience
& Federated Governance Fabric.

Manages federated governance proposals and decisions.
Explicit human approval required. Valid state transitions enforced.
"""
import datetime
from app.extensions import db
from app.models.federation_governance_record import FederationGovernanceRecord

VALID_DECISION_TYPES = [
    'collective_control', 'dependency_diversification', 'shared_recovery',
    'mutual_aid_policy', 'sector_priority', 'systemic_risk_acceptance',
    'collective_investment'
]

VALID_STATUSES = ['proposed', 'reviewing', 'approved', 'rejected', 'deferred', 'superseded']
VALID_TRANSITIONS = {
    'proposed': ['reviewing', 'rejected', 'deferred'],
    'reviewing': ['approved', 'rejected', 'deferred'],
    'approved': ['superseded'],
    'rejected': [],
    'deferred': ['reviewing', 'rejected'],
    'superseded': [],
}


class FederationGovernanceService:

    @staticmethod
    def create_proposal(title, decision_type, scope, proposal_summary,
                        participating_entities, org_id):
        """Create a new governance proposal in 'proposed' state."""
        if decision_type not in VALID_DECISION_TYPES:
            raise ValueError(f"Invalid decision_type: {decision_type}")

        import json
        record = FederationGovernanceRecord(
            title=title,
            decision_type=decision_type,
            scope=scope,
            proposal_summary=proposal_summary,
            participating_entities_json=json.dumps(participating_entities or []),
            decision_status='proposed',
            organization_id=org_id
        )
        db.session.add(record)
        db.session.commit()
        return record

    @staticmethod
    def calculate_support(record_id, supporter_count, total_entities, org_id):
        """Calculate support score as percentage of supporters."""
        record = FederationGovernanceRecord.query.filter_by(
            id=record_id, organization_id=org_id
        ).first()
        if not record:
            raise ValueError("FederationGovernanceRecord not found")
        if total_entities <= 0:
            raise ValueError("total_entities must be > 0")

        support = min(100.0, (supporter_count / total_entities) * 100.0)
        record.support_score = round(support, 2)
        db.session.commit()
        return record.support_score

    @staticmethod
    def calculate_opposition(record_id, opposition_count, total_entities, org_id):
        """Calculate opposition score as percentage."""
        record = FederationGovernanceRecord.query.filter_by(
            id=record_id, organization_id=org_id
        ).first()
        if not record:
            raise ValueError("FederationGovernanceRecord not found")
        if total_entities <= 0:
            raise ValueError("total_entities must be > 0")

        opp = min(100.0, (opposition_count / total_entities) * 100.0)
        record.opposition_score = round(opp, 2)
        db.session.commit()
        return record.opposition_score

    @staticmethod
    def calculate_consensus(record_id, org_id):
        """Consensus = support - opposition, clamped to 0-100."""
        record = FederationGovernanceRecord.query.filter_by(
            id=record_id, organization_id=org_id
        ).first()
        if not record:
            raise ValueError("FederationGovernanceRecord not found")

        consensus = max(0.0, min(100.0, record.support_score - record.opposition_score))
        record.consensus_score = round(consensus, 2)
        db.session.commit()
        return record.consensus_score

    @staticmethod
    def evaluate_systemic_impact(record_id, impact_value, org_id):
        """Record estimated systemic risk impact (negative = risk reduction)."""
        record = FederationGovernanceRecord.query.filter_by(
            id=record_id, organization_id=org_id
        ).first()
        if not record:
            raise ValueError("FederationGovernanceRecord not found")

        record.systemic_risk_impact = max(-100.0, min(100.0, impact_value))
        db.session.commit()
        return record.systemic_risk_impact

    @staticmethod
    def evaluate_collective_resilience_impact(record_id, impact_value, org_id):
        """Record estimated collective resilience impact (0-100)."""
        record = FederationGovernanceRecord.query.filter_by(
            id=record_id, organization_id=org_id
        ).first()
        if not record:
            raise ValueError("FederationGovernanceRecord not found")

        record.collective_resilience_impact = max(0.0, min(100.0, impact_value))
        db.session.commit()
        return record.collective_resilience_impact

    @staticmethod
    def _transition(record_id, new_status, org_id):
        """Internal: validate and apply status transition."""
        record = FederationGovernanceRecord.query.filter_by(
            id=record_id, organization_id=org_id
        ).first()
        if not record:
            raise ValueError("FederationGovernanceRecord not found")

        allowed = VALID_TRANSITIONS.get(record.decision_status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Invalid transition: {record.decision_status} -> {new_status}"
            )
        return record

    @staticmethod
    def approve_decision(record_id, approved_by, org_id):
        """Human-driven approval of a governance decision."""
        if not approved_by or not approved_by.strip():
            raise ValueError("approved_by is required for governance approval")
        record = FederationGovernanceService._transition(record_id, 'approved', org_id)
        record.decision_status = 'approved'
        record.approved_by = approved_by
        record.decided_at = datetime.datetime.utcnow()
        db.session.commit()
        return record

    @staticmethod
    def reject_decision(record_id, org_id):
        """Reject a governance decision."""
        record = FederationGovernanceService._transition(record_id, 'rejected', org_id)
        record.decision_status = 'rejected'
        record.decided_at = datetime.datetime.utcnow()
        db.session.commit()
        return record

    @staticmethod
    def governance_summary(org_id):
        """Return aggregate summary of governance decisions."""
        records = FederationGovernanceRecord.query.filter_by(organization_id=org_id).all()
        approved = [r for r in records if r.decision_status == 'approved']
        avg_consensus = (
            sum(r.consensus_score for r in records) / len(records)
            if records else 0.0
        )
        return {
            'total_proposals': len(records),
            'approved_decisions': len(approved),
            'avg_consensus_score': round(avg_consensus, 2),
            'pending_proposals': sum(1 for r in records if r.decision_status in ('proposed', 'reviewing')),
        }
