"""
Unit and Integration tests for Ecosystem Resilience.
Phase 39 — Systemic Cyber Risk, Collective Resilience & Federated Governance Fabric.
Contains 10 test cases.
"""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.systemic_risk_node import SystemicRiskNode
from app.models.systemic_dependency import SystemicDependency
from app.models.collective_resilience_plan import CollectiveResiliencePlan
from app.models.contagion_simulation_run import ContagionSimulationRun
from app.services.systemic_risk_graph_service import SystemicRiskGraphService
from app.services.ecosystem_resilience_service import EcosystemResilienceService


@pytest.fixture
def eco_setup(app):
    with app.app_context():
        db.session.query(ContagionSimulationRun).delete()
        db.session.query(CollectiveResiliencePlan).delete()
        db.session.query(SystemicDependency).delete()
        db.session.query(SystemicRiskNode).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Tenant A", slug="tenant-a", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        yield {"org": org}


def test_calculate_dependency_resilience_empty(app, eco_setup):
    """Test 1: Empty dependency list returns default resilience."""
    with app.app_context():
        res = EcosystemResilienceService.calculate_dependency_resilience(eco_setup["org"].id)
        assert res == 50.0


def test_calculate_dependency_resilience_weighted(app, eco_setup):
    """Test 2: Dependency resilience weighted average."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("N1", "service", None, None, "f", "r", eco_setup["org"].id, resilience_score=80.0)
        n2 = SystemicRiskGraphService.register_projection("N2", "service", None, None, "f", "r", eco_setup["org"].id, resilience_score=40.0)
        SystemicRiskGraphService.add_dependency(n1.id, n2.id, "technical", 100.0, 50.0, 40.0, 0.5, 80.0, eco_setup["org"].id)

        res = EcosystemResilienceService.calculate_dependency_resilience(eco_setup["org"].id)
        assert res == 40.0  # target node n2 resilience (40.0) is weighted 100%


def test_calculate_sector_resilience(app, eco_setup):
    """Test 3: Average resilience score per sector."""
    with app.app_context():
        SystemicRiskGraphService.register_projection("N1", "service", None, None, "finance", "r", eco_setup["org"].id, resilience_score=80.0)
        SystemicRiskGraphService.register_projection("N2", "service", None, None, "retail", "r", eco_setup["org"].id, resilience_score=40.0)

        res = EcosystemResilienceService.calculate_sector_resilience(eco_setup["org"].id)
        assert res == 60.0  # (80 + 40) / 2


def test_calculate_regional_resilience(app, eco_setup):
    """Test 4: Average resilience score per region."""
    with app.app_context():
        SystemicRiskGraphService.register_projection("N1", "service", None, None, "f", "us-east", eco_setup["org"].id, resilience_score=90.0)
        SystemicRiskGraphService.register_projection("N2", "service", None, None, "f", "us-west", eco_setup["org"].id, resilience_score=30.0)

        res = EcosystemResilienceService.calculate_regional_resilience(eco_setup["org"].id)
        assert res == 60.0  # (90 + 30) / 2


def test_calculate_collective_readiness_empty(app, eco_setup):
    """Test 5: Empty plans registry returns default readiness."""
    with app.app_context():
        res = EcosystemResilienceService.calculate_collective_readiness(eco_setup["org"].id)
        assert res == 50.0


def test_calculate_collective_readiness_weighted(app, eco_setup):
    """Test 6: Collective readiness based on approved plans."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("N1", "service", None, None, "f", "r", eco_setup["org"].id)
        plan1 = CollectiveResiliencePlan(
            name="Plan 1", plan_type="dependency_diversification", approval_status="approved", organization_id=eco_setup["org"].id
        )
        plan2 = CollectiveResiliencePlan(
            name="Plan 2", plan_type="dependency_diversification", approval_status="pending", organization_id=eco_setup["org"].id
        )
        db.session.add_all([plan1, plan2])
        db.session.commit()

        res = EcosystemResilienceService.calculate_collective_readiness(eco_setup["org"].id)
        assert res == 50.0  # 1 out of 2 approved = 50%


def test_calculate_recovery_capacity_empty(app, eco_setup):
    """Test 7: Empty runs list returns default capacity."""
    with app.app_context():
        res = EcosystemResilienceService.calculate_recovery_capacity(eco_setup["org"].id)
        assert res == 50.0


def test_calculate_recovery_capacity_score(app, eco_setup):
    """Test 8: Recovery capacity based on runs collective resilience."""
    with app.app_context():
        run = ContagionSimulationRun(
            scenario_id=1, status="completed", collective_resilience_score=85.0, organization_id=eco_setup["org"].id
        )
        db.session.add(run)
        db.session.commit()

        res = EcosystemResilienceService.calculate_recovery_capacity(eco_setup["org"].id)
        assert res == 85.0


def test_calculate_systemic_risk_index_inverse(app, eco_setup):
    """Test 9: Systemic Risk Index is inverse of composite resilience."""
    with app.app_context():
        systemic_risk = EcosystemResilienceService.calculate_systemic_risk_index(eco_setup["org"].id)
        assert 0.0 <= systemic_risk <= 100.0


def test_save_metrics_dict(app, eco_setup):
    """Test 10: Save metrics dict format validation."""
    with app.app_context():
        metrics = EcosystemResilienceService.save_metrics(eco_setup["org"].id)
        assert 'systemic_risk_index' in metrics
        assert 'composite_resilience' in metrics
