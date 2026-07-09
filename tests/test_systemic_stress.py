"""
Unit and Integration tests for Systemic Stress.
Phase 39 — Systemic Cyber Risk, Collective Resilience & Federated Governance Fabric.
Contains 10 test cases.
"""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.systemic_risk_node import SystemicRiskNode
from app.models.systemic_dependency import SystemicDependency
from app.models.contagion_scenario import ContagionScenario
from app.models.contagion_simulation_run import ContagionSimulationRun
from app.services.systemic_risk_graph_service import SystemicRiskGraphService
from app.services.contagion_simulation_service import ContagionSimulationService
from app.services.systemic_stress_service import SystemicStressService


@pytest.fixture
def stress_setup(app):
    with app.app_context():
        db.session.query(ContagionSimulationRun).delete()
        db.session.query(ContagionScenario).delete()
        db.session.query(SystemicDependency).delete()
        db.session.query(SystemicRiskNode).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Tenant A", slug="tenant-a", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        yield {"org": org}


def test_correlated_stress_payload(app, stress_setup):
    """Test 1: Correlated stress calculation."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("N1", "service", None, None, "f", "r", stress_setup["org"].id)
        res = SystemicStressService.create_correlated_stress([n1.id], 0.7, stress_setup["org"].id)
        assert res['node_count'] == 1
        assert res['correlation_factor'] == 0.7


def test_correlated_stress_invalid_factor(app, stress_setup):
    """Test 2: Rejects invalid correlation factors."""
    with app.app_context():
        with pytest.raises(ValueError, match="correlation_factor must be"):
            SystemicStressService.create_correlated_stress([1], 1.5, stress_setup["org"].id)


def test_apply_multi_node_failure(app, stress_setup):
    """Test 3: Compute aggregate failure impact for multiple nodes."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("N1", "service", None, None, "f", "r", stress_setup["org"].id)
        n2 = SystemicRiskGraphService.register_projection("N2", "service", None, None, "f", "r", stress_setup["org"].id)
        res = SystemicStressService.apply_multi_node_failure([n1.id, n2.id], 80.0, stress_setup["org"].id)
        assert res['nodes_failed'] == 2
        assert res['aggregate_impact'] > 0.0


def test_calculate_aggregate_impact(app, stress_setup):
    """Test 4: Aggregate impact limits correctly."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("N1", "service", None, None, "f", "r", stress_setup["org"].id)
        impact = SystemicStressService.calculate_aggregate_impact([n1.id], 150.0, stress_setup["org"].id)
        assert impact <= 100.0


def test_calculate_sector_impact(app, stress_setup):
    """Test 5: Calculates correct impact for a specific sector."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("N1", "service", None, None, "financial", "r", stress_setup["org"].id)
        res = SystemicStressService.calculate_sector_impact("financial", 80.0, stress_setup["org"].id)
        assert res['sector'] == "financial"
        assert res['nodes'] == 1


def test_calculate_sector_impact_empty(app, stress_setup):
    """Test 6: Empty sector returns zero impact."""
    with app.app_context():
        res = SystemicStressService.calculate_sector_impact("health", 80.0, stress_setup["org"].id)
        assert res['nodes'] == 0
        assert res['impact'] == 0.0


def test_calculate_regional_impact(app, stress_setup):
    """Test 7: Calculates correct impact for a specific region."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("N1", "service", None, None, "f", "us-west", stress_setup["org"].id)
        res = SystemicStressService.calculate_regional_impact("us-west", 70.0, stress_setup["org"].id)
        assert res['region'] == "us-west"
        assert res['nodes'] == 1


def test_compare_stress_runs(app, stress_setup):
    """Test 8: Compares two contagion runs cleanly."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("N1", "service", None, None, "f", "r", stress_setup["org"].id)
        sc1 = ContagionSimulationService.create_scenario("S1", "T", "cloud_region_disruption", n1.id, "high", 80.0, 5, 0.5, 42, stress_setup["org"].id)
        run1 = ContagionSimulationService.start_simulation(sc1.id, stress_setup["org"].id)

        sc2 = ContagionSimulationService.create_scenario("S2", "T", "cloud_region_disruption", n1.id, "high", 40.0, 5, 0.5, 42, stress_setup["org"].id)
        run2 = ContagionSimulationService.start_simulation(sc2.id, stress_setup["org"].id)

        comp = SystemicStressService.compare_stress_runs(run1.id, run2.id, stress_setup["org"].id)
        assert 'impact_diff' in comp


def test_identify_concentration_failures(app, stress_setup):
    """Test 9: Identifies highly connected concentration failure nodes."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("N1", "service", None, None, "f", "r", stress_setup["org"].id)
        n2 = SystemicRiskGraphService.register_projection("N2", "service", None, None, "f", "r", stress_setup["org"].id)
        n3 = SystemicRiskGraphService.register_projection("N3", "service", None, None, "f", "r", stress_setup["org"].id)
        n4 = SystemicRiskGraphService.register_projection("N4", "service", None, None, "f", "r", stress_setup["org"].id)

        # N4 target gets 3 inbound edges
        SystemicRiskGraphService.add_dependency(n1.id, n4.id, "technical", 80.0, 50.0, 40.0, 0.5, 80.0, stress_setup["org"].id)
        SystemicRiskGraphService.add_dependency(n2.id, n4.id, "technical", 80.0, 50.0, 40.0, 0.5, 80.0, stress_setup["org"].id)
        SystemicRiskGraphService.add_dependency(n3.id, n4.id, "technical", 80.0, 50.0, 40.0, 0.5, 80.0, stress_setup["org"].id)

        con = SystemicStressService.identify_concentration_failures(stress_setup["org"].id, threshold=3)
        assert len(con) == 1
        assert con[0]['node_id'] == n4.id


def test_stress_summary(app, stress_setup):
    """Test 10: Stress summary contains all details."""
    with app.app_context():
        SystemicRiskGraphService.register_projection("N1", "service", None, None, "f", "r", stress_setup["org"].id)
        summary = SystemicStressService.stress_summary(stress_setup["org"].id)
        assert summary['total_nodes'] == 1
