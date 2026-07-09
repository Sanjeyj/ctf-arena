import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.resilience_investment_plan import ResilienceInvestmentPlan
from app.models.investment_plan_item import InvestmentPlanItem
from app.models.security_investment import SecurityInvestment
from app.services.resilience_planning_service import ResiliencePlanningService
from app.research.routes import create_jwt


@pytest.fixture
def plan_setup(app):
    with app.app_context():
        db.session.query(InvestmentPlanItem).delete()
        db.session.query(ResilienceInvestmentPlan).delete()
        db.session.query(SecurityInvestment).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        o2 = Organization(name="Org 2", slug="org-2", plan_type="enterprise")
        db.session.add_all([o1, o2])
        db.session.commit()

        i1 = SecurityInvestment(
            title="MFA", investment_category="control", cost=10000.0,
            expected_loss_reduction=50000.0, expected_risk_reduction=40.0, organization_id=o1.id
        )
        db.session.add(i1)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "o1": o1,
            "o2": o2,
            "i1": i1,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_create_plan_valid(app, plan_setup):
    """Test 1: Create a valid resilience plan."""
    with app.app_context():
        p = ResiliencePlanningService.create_plan(
            "FY27 Resilience Plan", "Strategic funding", 150000.0, 12, 30.0, 85.0, plan_setup["o1"].id
        )
        assert p.id is not None
        assert p.status == "draft"


def test_create_plan_negative_budget(app, plan_setup):
    """Test 2: Negative budget limit throws ValueError."""
    with app.app_context():
        with pytest.raises(ValueError):
            ResiliencePlanningService.create_plan(
                "Plan", "Desc", -100.0, 12, 30.0, 85.0, plan_setup["o1"].id
            )


def test_add_candidate_valid(app, plan_setup):
    """Test 3: Add valid candidate to plan."""
    with app.app_context():
        p = ResiliencePlanningService.create_plan(
            "Plan", "Desc", 100000.0, 12, 30.0, 85.0, plan_setup["o1"].id
        )
        item = ResiliencePlanningService.add_candidate(p.id, plan_setup["i1"].id, 10000.0, plan_setup["o1"].id)
        assert item.id is not None
        assert item.status == "candidate"


def test_add_candidate_negative_allocation(app, plan_setup):
    """Test 4: Negative budget allocation throws ValueError."""
    with app.app_context():
        p = ResiliencePlanningService.create_plan(
            "Plan", "Desc", 100000.0, 12, 30.0, 85.0, plan_setup["o1"].id
        )
        with pytest.raises(ValueError):
            ResiliencePlanningService.add_candidate(p.id, plan_setup["i1"].id, -100.0, plan_setup["o1"].id)


def test_add_candidate_cross_tenant(app, plan_setup):
    """Test 5: Cross-tenant candidate validation throws ValueError."""
    with app.app_context():
        p = ResiliencePlanningService.create_plan(
            "Plan", "Desc", 100000.0, 12, 30.0, 85.0, plan_setup["o1"].id
        )
        # Attempt to add with different tenant ID
        with pytest.raises(ValueError):
            ResiliencePlanningService.add_candidate(p.id, plan_setup["i1"].id, 10000.0, plan_setup["o2"].id)


def test_evaluate_candidate(app, plan_setup):
    """Test 6: Evaluate candidate ROSI prioritizes rank."""
    with app.app_context():
        p = ResiliencePlanningService.create_plan(
            "Plan", "Desc", 100000.0, 12, 30.0, 85.0, plan_setup["o1"].id
        )
        item = ResiliencePlanningService.add_candidate(p.id, plan_setup["i1"].id, 10000.0, plan_setup["o1"].id)
        evaluated = ResiliencePlanningService.evaluate_candidate(item.id, plan_setup["o1"].id)
        assert evaluated.priority_rank > 0


def test_select_investments(app, plan_setup):
    """Test 7: Select investments selects candidate within budget limits."""
    with app.app_context():
        p = ResiliencePlanningService.create_plan(
            "Plan", "Desc", 5000.0, 12, 30.0, 85.0, plan_setup["o1"].id
        )
        # Candidate cost 10000 exceeds plan budget 5000
        ResiliencePlanningService.add_candidate(p.id, plan_setup["i1"].id, 10000.0, plan_setup["o1"].id)
        selected = ResiliencePlanningService.select_investments(p.id, plan_setup["o1"].id)
        # Should be empty since candidate exceeds budget limit
        assert len(selected) == 0


def test_approve_plan(app, plan_setup):
    """Test 8: Approve plan changes status and logs approver."""
    with app.app_context():
        p = ResiliencePlanningService.create_plan(
            "Plan", "Desc", 150000.0, 12, 30.0, 85.0, plan_setup["o1"].id
        )
        approved = ResiliencePlanningService.approve_plan(p.id, "exec_officer", plan_setup["o1"].id)
        assert approved.status == "approved"
        assert approved.approved_by == "exec_officer"


def test_api_plans_endpoint(app, client, plan_setup):
    """Test 9: REST API plans list endpoint."""
    res = client.get(
        f'/api/v1/strategic-resilience/plans?org_id={plan_setup["o1"].id}',
        headers=plan_setup["headers"]
    )
    assert res.status_code == 200


def test_api_approve_plan(app, client, plan_setup):
    """Test 10: REST API approve plan endpoint."""
    with app.app_context():
        p = ResiliencePlanningService.create_plan(
            "Plan", "Desc", 150000.0, 12, 30.0, 85.0, plan_setup["o1"].id
        )
        p_id = p.id
    res = client.post(
        f'/api/v1/strategic-resilience/plans/{p_id}/approve',
        json={"org_id": plan_setup["o1"].id, "approved_by": "exec"},
        headers=plan_setup["headers"]
    )
    assert res.status_code == 200
