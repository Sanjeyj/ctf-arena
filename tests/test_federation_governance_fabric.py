"""
Unit and Integration tests for Federation Governance.
Phase 39 — Systemic Cyber Risk, Collective Resilience & Federated Governance Fabric.
Contains 10 test cases.
"""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.federation_governance_record import FederationGovernanceRecord
from app.services.federation_governance_service import FederationGovernanceService


@pytest.fixture
def gov_setup(app):
    with app.app_context():
        db.session.query(FederationGovernanceRecord).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Tenant A", slug="tenant-a", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        yield {"org": org}


def test_create_proposal_success(app, gov_setup):
    """Test 1: Governance proposal registers successfully."""
    with app.app_context():
        proposal = FederationGovernanceService.create_proposal(
            "Mutual Aid Charter", "mutual_aid_policy", "all", "Joint mutual aid agreement",
            ["entity-a", "entity-b"], gov_setup["org"].id
        )
        assert proposal.id is not None
        assert proposal.decision_status == "proposed"


def test_create_proposal_invalid_type(app, gov_setup):
    """Test 2: Proposal creation rejects invalid types."""
    with app.app_context():
        with pytest.raises(ValueError, match="Invalid decision_type"):
            FederationGovernanceService.create_proposal(
                "Charter", "bad_type", "all", "desc", [], gov_setup["org"].id
            )


def test_calculate_support_score(app, gov_setup):
    """Test 3: Compute support score correctly."""
    with app.app_context():
        proposal = FederationGovernanceService.create_proposal("Charter", "mutual_aid_policy", "all", "desc", [], gov_setup["org"].id)
        score = FederationGovernanceService.calculate_support(proposal.id, 8, 10, gov_setup["org"].id)
        assert score == 80.0


def test_calculate_opposition_score(app, gov_setup):
    """Test 4: Compute opposition score correctly."""
    with app.app_context():
        proposal = FederationGovernanceService.create_proposal("Charter", "mutual_aid_policy", "all", "desc", [], gov_setup["org"].id)
        score = FederationGovernanceService.calculate_opposition(proposal.id, 2, 10, gov_setup["org"].id)
        assert score == 20.0


def test_calculate_consensus_score(app, gov_setup):
    """Test 5: Compute consensus score cleanly."""
    with app.app_context():
        proposal = FederationGovernanceService.create_proposal("Charter", "mutual_aid_policy", "all", "desc", [], gov_setup["org"].id)
        FederationGovernanceService.calculate_support(proposal.id, 8, 10, gov_setup["org"].id)
        FederationGovernanceService.calculate_opposition(proposal.id, 2, 10, gov_setup["org"].id)
        consensus = FederationGovernanceService.calculate_consensus(proposal.id, gov_setup["org"].id)
        assert consensus == 60.0


def test_evaluate_systemic_impact(app, gov_setup):
    """Test 6: Governance impact scores limits."""
    with app.app_context():
        proposal = FederationGovernanceService.create_proposal("Charter", "mutual_aid_policy", "all", "desc", [], gov_setup["org"].id)
        impact = FederationGovernanceService.evaluate_systemic_impact(proposal.id, -150.0, gov_setup["org"].id)
        assert impact == -100.0  # Clamped to -100.0


def test_evaluate_collective_resilience_impact(app, gov_setup):
    """Test 7: Governance resilience impact score bounds."""
    with app.app_context():
        proposal = FederationGovernanceService.create_proposal("Charter", "mutual_aid_policy", "all", "desc", [], gov_setup["org"].id)
        res = FederationGovernanceService.evaluate_collective_resilience_impact(proposal.id, 150.0, gov_setup["org"].id)
        assert res == 100.0  # Clamped to 100.0


def test_approve_decision_success(app, gov_setup):
    """Test 8: Human approval updates state transition."""
    with app.app_context():
        proposal = FederationGovernanceService.create_proposal("Charter", "mutual_aid_policy", "all", "desc", [], gov_setup["org"].id)
        # Transition proposed -> reviewing
        FederationGovernanceService.calculate_support(proposal.id, 8, 10, gov_setup["org"].id)
        proposal.decision_status = 'reviewing'
        db.session.commit()

        approved = FederationGovernanceService.approve_decision(proposal.id, "Gov Chairman", gov_setup["org"].id)
        assert approved.decision_status == "approved"
        assert approved.approved_by == "Gov Chairman"


def test_approve_decision_invalid_transition(app, gov_setup):
    """Test 9: Invalid state transition is rejected."""
    with app.app_context():
        proposal = FederationGovernanceService.create_proposal("Charter", "mutual_aid_policy", "all", "desc", [], gov_setup["org"].id)
        # Directly from proposed to approved (should fail without reviewing)
        with pytest.raises(ValueError, match="Invalid transition"):
            FederationGovernanceService.approve_decision(proposal.id, "Gov Chairman", gov_setup["org"].id)


def test_governance_summary(app, gov_setup):
    """Test 10: Summary registers all proposal statistics."""
    with app.app_context():
        FederationGovernanceService.create_proposal("Charter", "mutual_aid_policy", "all", "desc", [], gov_setup["org"].id)
        summary = FederationGovernanceService.governance_summary(gov_setup["org"].id)
        assert summary['total_proposals'] == 1
