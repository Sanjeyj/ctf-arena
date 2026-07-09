"""
Unit and Integration tests for Collective Resilience.
Phase 39 — Systemic Cyber Risk, Collective Resilience & Federated Governance Fabric.
Contains 10 test cases.
"""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.systemic_risk_node import SystemicRiskNode
from app.models.collective_resilience_plan import CollectiveResiliencePlan
from app.services.systemic_risk_graph_service import SystemicRiskGraphService
from app.services.collective_resilience_service import CollectiveResilienceService


@pytest.fixture
def plan_setup(app):
    with app.app_context():
        db.session.query(CollectiveResiliencePlan).delete()
        db.session.query(SystemicRiskNode).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Tenant A", slug="tenant-a", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        yield {"org": org}


def test_create_plan_success(app, plan_setup):
    """Test 1: Plan creation registers plan details."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("N1", "service", None, None, "f", "r", plan_setup["org"].id)
        plan = CollectiveResilienceService.create_plan(
            "Diversify DNS", "Global DNS", "dependency_diversification", [n1.id],
            1500.0, plan_setup["org"].id
        )
        assert plan.id is not None
        assert plan.status == "draft"
        assert plan.approval_status == "pending"


def test_create_plan_invalid_type(app, plan_setup):
    """Test 2: Plan creation rejects unknown type."""
    with app.app_context():
        with pytest.raises(ValueError, match="Invalid plan_type"):
            CollectiveResilienceService.create_plan(
                "DNS", "scope", "bad_type", [], 1000.0, plan_setup["org"].id
            )


def test_calculate_baseline(app, plan_setup):
    """Test 3: Plan baseline score computed correctly."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection(
            "N1", "service", None, None, "f", "r", plan_setup["org"].id, resilience_score=60.0
        )
        plan = CollectiveResilienceService.create_plan(
            "DNS", "scope", "dependency_diversification", [n1.id], 1000.0, plan_setup["org"].id
        )
        baseline = CollectiveResilienceService.calculate_baseline(plan.id, plan_setup["org"].id)
        assert baseline == 60.0


def test_calculate_target(app, plan_setup):
    """Test 4: Plan target score computed correctly and capped."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection(
            "N1", "service", None, None, "f", "r", plan_setup["org"].id, resilience_score=60.0
        )
        plan = CollectiveResilienceService.create_plan(
            "DNS", "scope", "dependency_diversification", [n1.id], 1000.0, plan_setup["org"].id
        )
        CollectiveResilienceService.calculate_baseline(plan.id, plan_setup["org"].id)
        target = CollectiveResilienceService.calculate_target(plan.id, 0.5, plan_setup["org"].id)
        assert target == 90.0


def test_estimate_risk_reduction(app, plan_setup):
    """Test 5: Risk reduction estimate is positive and bounded."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection(
            "N1", "service", None, None, "f", "r", plan_setup["org"].id, resilience_score=50.0
        )
        plan = CollectiveResilienceService.create_plan(
            "DNS", "scope", "dependency_diversification", [n1.id], 1000.0, plan_setup["org"].id
        )
        CollectiveResilienceService.evaluate_plan(plan.id, 0.5, plan_setup["org"].id)
        reduction = CollectiveResilienceService.estimate_risk_reduction(plan.id, plan_setup["org"].id)
        assert reduction > 0.0


def test_rank_plans(app, plan_setup):
    """Test 6: Resilience plans are ranked by priority desc."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("N1", "service", None, None, "f", "r", plan_setup["org"].id)
        p1 = CollectiveResilienceService.create_plan("P1", "s", "dependency_diversification", [n1.id], 5000.0, plan_setup["org"].id)
        p2 = CollectiveResilienceService.create_plan("P2", "s", "dependency_diversification", [n1.id], 100.0, plan_setup["org"].id)

        CollectiveResilienceService.evaluate_plan(p1.id, 0.5, plan_setup["org"].id)
        CollectiveResilienceService.evaluate_plan(p2.id, 0.5, plan_setup["org"].id)

        ranked = CollectiveResilienceService.rank_plans(plan_setup["org"].id)
        assert ranked[0].priority_score >= ranked[-1].priority_score


def test_approve_plan_success(app, plan_setup):
    """Test 7: Plan approval updates approval status and triggers state transition."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("N1", "service", None, None, "f", "r", plan_setup["org"].id)
        plan = CollectiveResilienceService.create_plan("P", "s", "dependency_diversification", [n1.id], 100.0, plan_setup["org"].id)
        approved = CollectiveResilienceService.approve_plan(plan.id, "CISO Joe", plan_setup["org"].id)
        assert approved.approval_status == "approved"
        assert approved.status == "active"


def test_approve_plan_missing_signature(app, plan_setup):
    """Test 8: Rejects plan approval with missing signature."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("N1", "service", None, None, "f", "r", plan_setup["org"].id)
        plan = CollectiveResilienceService.create_plan("P", "s", "dependency_diversification", [n1.id], 100.0, plan_setup["org"].id)
        with pytest.raises(ValueError, match="approved_by is required"):
            CollectiveResilienceService.approve_plan(plan.id, "", plan_setup["org"].id)


def test_collective_resilience_summary(app, plan_setup):
    """Test 9: Summary displays plans data."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection("N1", "service", None, None, "f", "r", plan_setup["org"].id)
        CollectiveResilienceService.create_plan("P", "s", "dependency_diversification", [n1.id], 100.0, plan_setup["org"].id)
        summary = CollectiveResilienceService.collective_resilience_summary(plan_setup["org"].id)
        assert summary['total_plans'] == 1


def test_resilience_score_bounds(app, plan_setup):
    """Test 10: Targets and baseline scores are clamped [0, 100]."""
    with app.app_context():
        n1 = SystemicRiskGraphService.register_projection(
            "N1", "service", None, None, "f", "r", plan_setup["org"].id, resilience_score=150.0
        )
        plan = CollectiveResilienceService.create_plan("P", "s", "dependency_diversification", [n1.id], 100.0, plan_setup["org"].id)
        baseline = CollectiveResilienceService.calculate_baseline(plan.id, plan_setup["org"].id)
        assert baseline <= 100.0
        target = CollectiveResilienceService.calculate_target(plan.id, 0.8, plan_setup["org"].id)
        assert target <= 100.0
