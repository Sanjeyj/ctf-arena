"""
Unit and Integration tests for Mutual Aid Simulation.
Phase 39 — Systemic Cyber Risk, Collective Resilience & Federated Governance Fabric.
Contains 10 test cases.
"""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.systemic_risk_node import SystemicRiskNode
from app.models.contagion_simulation_run import ContagionSimulationRun
from app.models.contagion_scenario import ContagionScenario
from app.models.mutual_aid_simulation import MutualAidSimulation
from app.services.systemic_risk_graph_service import SystemicRiskGraphService
from app.services.contagion_simulation_service import ContagionSimulationService
from app.services.mutual_aid_simulation_service import MutualAidSimulationService


@pytest.fixture
def aid_setup(app):
    with app.app_context():
        db.session.query(MutualAidSimulation).delete()
        db.session.query(ContagionSimulationRun).delete()
        db.session.query(ContagionScenario).delete()
        db.session.query(SystemicRiskNode).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Tenant A", slug="tenant-a", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        yield {"org": org}


def test_calculate_available_capacity_baseline(app, aid_setup):
    """Test 1: Available capacity equals resilience score."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection(
            "DNS Provider", "coordination_center", None, None, "f", "r", aid_setup["org"].id, resilience_score=80.0
        )
        cap = MutualAidSimulationService.calculate_available_capacity(n1.id, aid_setup["org"].id)
        assert cap == 80.0


def test_allocate_capacity_within_bounds(app, aid_setup):
    """Test 2: Allocate capacity within available bounds."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("DNS Provider", "coordination_center", None, None, "f", "r", aid_setup["org"].id, resilience_score=80.0)
        n2 = SystemicRiskGraphService.register_projection("DNS Recipient", "service", None, None, "f", "r", aid_setup["org"].id, resilience_score=30.0)
        sc = ContagionSimulationService.create_scenario("S", "T", "cloud_region_disruption", n1.id, "high", 80.0, 5, 0.5, 42, aid_setup["org"].id)
        run = ContagionSimulationService.start_simulation(sc.id, aid_setup["org"].id)

        aid = MutualAidSimulationService.allocate_simulated_capacity(
            n1.id, n2.id, "recovery_capacity", 30.0, run.id, aid_setup["org"].id
        )
        assert aid.id is not None
        assert aid.capacity_allocated == 30.0
        assert aid.approval_status == "pending"


def test_allocate_capacity_over_bounds_rejected(app, aid_setup):
    """Test 3: Rejects allocations exceeding available capacity."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("DNS Provider", "coordination_center", None, None, "f", "r", aid_setup["org"].id, resilience_score=50.0)
        n2 = SystemicRiskGraphService.register_projection("DNS Recipient", "service", None, None, "f", "r", aid_setup["org"].id, resilience_score=30.0)
        sc = ContagionSimulationService.create_scenario("S", "T", "cloud_region_disruption", n1.id, "high", 80.0, 5, 0.5, 42, aid_setup["org"].id)
        run = ContagionSimulationService.start_simulation(sc.id, aid_setup["org"].id)

        with pytest.raises(ValueError, match="exceeds available"):
            MutualAidSimulationService.allocate_simulated_capacity(
                n1.id, n2.id, "recovery_capacity", 60.0, run.id, aid_setup["org"].id
            )


def test_calculate_allocation_score(app, aid_setup):
    """Test 4: Allocation score scales correctly."""
    score = MutualAidSimulationService.calculate_allocation_score(100.0, 50.0, 30.0, 80.0)
    assert 0.0 <= score <= 100.0


def test_estimate_recovery_gain(app, aid_setup):
    """Test 5: Estimate recovery gain metric."""
    gain = MutualAidSimulationService.estimate_recovery_gain(50.0, 30.0)
    assert gain >= 0.0


def test_validate_allocation_valid(app, aid_setup):
    """Test 6: Validates valid allocations successfully."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("DNS Provider", "coordination_center", None, None, "f", "r", aid_setup["org"].id, resilience_score=80.0)
        n2 = SystemicRiskGraphService.register_projection("DNS Recipient", "service", None, None, "f", "r", aid_setup["org"].id, resilience_score=30.0)
        sc = ContagionSimulationService.create_scenario("S", "T", "cloud_region_disruption", n1.id, "high", 80.0, 5, 0.5, 42, aid_setup["org"].id)
        run = ContagionSimulationService.start_simulation(sc.id, aid_setup["org"].id)

        aid = MutualAidSimulationService.allocate_simulated_capacity(
            n1.id, n2.id, "recovery_capacity", 30.0, run.id, aid_setup["org"].id
        )
        valid = MutualAidSimulationService.validate_allocation(aid.id, aid_setup["org"].id)
        assert valid is True


def test_approve_allocation_success(app, aid_setup):
    """Test 7: Approving allocation changes status and locks capacity."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("DNS Provider", "coordination_center", None, None, "f", "r", aid_setup["org"].id, resilience_score=80.0)
        n2 = SystemicRiskGraphService.register_projection("DNS Recipient", "service", None, None, "f", "r", aid_setup["org"].id, resilience_score=30.0)
        sc = ContagionSimulationService.create_scenario("S", "T", "cloud_region_disruption", n1.id, "high", 80.0, 5, 0.5, 42, aid_setup["org"].id)
        run = ContagionSimulationService.start_simulation(sc.id, aid_setup["org"].id)

        aid = MutualAidSimulationService.allocate_simulated_capacity(
            n1.id, n2.id, "recovery_capacity", 30.0, run.id, aid_setup["org"].id
        )
        approved = MutualAidSimulationService.approve_allocation(aid.id, aid_setup["org"].id)
        assert approved.approval_status == "approved"
        assert approved.status == "allocated_simulation"

        # Check provider remaining capacity
        rem = MutualAidSimulationService.calculate_available_capacity(n1.id, aid_setup["org"].id)
        assert rem == 50.0


def test_identify_recipients_service(app, aid_setup):
    """Test 8: Identify recipients involved in contagion runs."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("DNS Provider", "coordination_center", None, None, "f", "r", aid_setup["org"].id, resilience_score=80.0)
        recipients = MutualAidSimulationService.identify_recipients(1, aid_setup["org"].id)
        assert isinstance(recipients, list)


def test_allocation_summary(app, aid_setup):
    """Test 9: Summary lists simulated allocation counts."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("DNS Provider", "coordination_center", None, None, "f", "r", aid_setup["org"].id, resilience_score=80.0)
        n2 = SystemicRiskGraphService.register_projection("DNS Recipient", "service", None, None, "f", "r", aid_setup["org"].id, resilience_score=30.0)
        sc = ContagionSimulationService.create_scenario("S", "T", "cloud_region_disruption", n1.id, "high", 80.0, 5, 0.5, 42, aid_setup["org"].id)
        run = ContagionSimulationService.start_simulation(sc.id, aid_setup["org"].id)

        MutualAidSimulationService.allocate_simulated_capacity(
            n1.id, n2.id, "recovery_capacity", 30.0, run.id, aid_setup["org"].id
        )
        summary = MutualAidSimulationService.allocation_summary(aid_setup["org"].id)
        assert summary['total_simulations'] == 1


def test_available_capacity_never_negative(app, aid_setup):
    """Test 10: Available capacity is always >= 0."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("DNS Provider", "coordination_center", None, None, "f", "r", aid_setup["org"].id, resilience_score=-20.0)
        cap = MutualAidSimulationService.calculate_available_capacity(n1.id, aid_setup["org"].id)
        assert cap == 0.0
