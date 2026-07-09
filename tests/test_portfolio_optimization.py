import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.resilience_investment_plan import ResilienceInvestmentPlan
from app.models.investment_plan_item import InvestmentPlanItem
from app.models.security_investment import SecurityInvestment
from app.services.resilience_planning_service import ResiliencePlanningService
from app.services.portfolio_optimization_service import PortfolioOptimizationService
from app.research.routes import create_jwt


@pytest.fixture
def opt_setup(app):
    with app.app_context():
        db.session.query(InvestmentPlanItem).delete()
        db.session.query(ResilienceInvestmentPlan).delete()
        db.session.query(SecurityInvestment).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        db.session.add(o1)
        db.session.commit()

        # Two investments:
        # i1: cost = 5000, reduction = 20000
        # i2: cost = 10000, reduction = 30000
        i1 = SecurityInvestment(
            title="I1", investment_category="control", cost=5000.0,
            expected_loss_reduction=20000.0, expected_risk_reduction=40.0, organization_id=o1.id
        )
        i2 = SecurityInvestment(
            title="I2", investment_category="control", cost=10000.0,
            expected_loss_reduction=30000.0, expected_risk_reduction=30.0, organization_id=o1.id
        )
        db.session.add_all([i1, i2])
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "o1": o1,
            "i1": i1,
            "i2": i2,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_optimize_budget_within_limit(app, opt_setup):
    """Test 1: Greedy knapsack picks most cost effective option first within budget."""
    with app.app_context():
        # Budget = 6000 (can only fit I1, cost 5000)
        p = ResiliencePlanningService.create_plan("Plan", "Desc", 6000.0, 12, 10.0, 80.0, opt_setup["o1"].id)
        ResiliencePlanningService.add_candidate(p.id, opt_setup["i1"].id, 5000.0, opt_setup["o1"].id)
        ResiliencePlanningService.add_candidate(p.id, opt_setup["i2"].id, 10000.0, opt_setup["o1"].id)

        selected = PortfolioOptimizationService.optimize_budget(p.id, opt_setup["o1"].id)
        assert len(selected) == 1
        assert selected[0].security_investment_id == opt_setup["i1"].id


def test_optimize_budget_both_fit(app, opt_setup):
    """Test 2: Picks both candidates if combined cost satisfies budget limit."""
    with app.app_context():
        # Budget = 20000
        p = ResiliencePlanningService.create_plan("Plan", "Desc", 20000.0, 12, 10.0, 80.0, opt_setup["o1"].id)
        ResiliencePlanningService.add_candidate(p.id, opt_setup["i1"].id, 5000.0, opt_setup["o1"].id)
        ResiliencePlanningService.add_candidate(p.id, opt_setup["i2"].id, 10000.0, opt_setup["o1"].id)

        selected = PortfolioOptimizationService.optimize_budget(p.id, opt_setup["o1"].id)
        assert len(selected) == 2


def test_rank_candidates(app, opt_setup):
    """Test 3: Ranks candidates by loss reduction per dollar."""
    with app.app_context():
        p = ResiliencePlanningService.create_plan("Plan", "Desc", 20000.0, 12, 10.0, 80.0, opt_setup["o1"].id)
        ResiliencePlanningService.add_candidate(p.id, opt_setup["i1"].id, 5000.0, opt_setup["o1"].id)
        ResiliencePlanningService.add_candidate(p.id, opt_setup["i2"].id, 10000.0, opt_setup["o1"].id)

        ranked = PortfolioOptimizationService.rank_candidates(p.id, opt_setup["o1"].id)
        # I1 ratio: (20000 + 8) / 5000 = 4.0016
        # I2 ratio: (30000 + 6) / 10000 = 3.0006
        assert ranked[0].security_investment_id == opt_setup["i1"].id


def test_calculate_efficiency(app, opt_setup):
    """Test 4: Efficiency returns correct composite ratio."""
    with app.app_context():
        p = ResiliencePlanningService.create_plan("Plan", "Desc", 20000.0, 12, 10.0, 80.0, opt_setup["o1"].id)
        ResiliencePlanningService.add_candidate(p.id, opt_setup["i1"].id, 5000.0, opt_setup["o1"].id)
        PortfolioOptimizationService.optimize_budget(p.id, opt_setup["o1"].id)

        eff = PortfolioOptimizationService.calculate_efficiency(p.id, opt_setup["o1"].id)
        # Cost: 5000. Benefit: 20000 + (8 * 1000) = 28000. Ratio = 28000/5000 = 5.6
        assert eff == 5.6


def test_calculate_marginal_risk_reduction(app, opt_setup):
    """Test 5: Marginal risk reduction helper returns correct value."""
    with app.app_context():
        p = ResiliencePlanningService.create_plan("Plan", "Desc", 20000.0, 12, 10.0, 80.0, opt_setup["o1"].id)
        item = ResiliencePlanningService.add_candidate(p.id, opt_setup["i1"].id, 5000.0, opt_setup["o1"].id)
        val = PortfolioOptimizationService.calculate_marginal_risk_reduction(p.id, item.id, opt_setup["o1"].id)
        assert val == 20000.0


def test_calculate_resilience_gain(app, opt_setup):
    """Test 6: Resilience gain helper returns correct value."""
    with app.app_context():
        p = ResiliencePlanningService.create_plan("Plan", "Desc", 20000.0, 12, 10.0, 80.0, opt_setup["o1"].id)
        item = ResiliencePlanningService.add_candidate(p.id, opt_setup["i1"].id, 5000.0, opt_setup["o1"].id)
        val = PortfolioOptimizationService.calculate_resilience_gain(p.id, item.id, opt_setup["o1"].id)
        # 40.0 / 5.0 = 8.0
        assert val == 8.0


def test_compare_portfolios(app, opt_setup):
    """Test 7: Compare two optimized portfolios efficiency."""
    with app.app_context():
        p1 = ResiliencePlanningService.create_plan("Plan 1", "Desc", 20000.0, 12, 10.0, 80.0, opt_setup["o1"].id)
        p2 = ResiliencePlanningService.create_plan("Plan 2", "Desc", 20000.0, 12, 10.0, 80.0, opt_setup["o1"].id)
        ResiliencePlanningService.add_candidate(p1.id, opt_setup["i1"].id, 5000.0, opt_setup["o1"].id)
        ResiliencePlanningService.add_candidate(p2.id, opt_setup["i2"].id, 10000.0, opt_setup["o1"].id)

        PortfolioOptimizationService.optimize_budget(p1.id, opt_setup["o1"].id)
        PortfolioOptimizationService.optimize_budget(p2.id, opt_setup["o1"].id)

        res = PortfolioOptimizationService.compare_portfolios(p1.id, p2.id, opt_setup["o1"].id)
        assert res["plan1"]["efficiency"] > res["plan2"]["efficiency"]


def test_recommend_portfolio(app, opt_setup):
    """Test 8: Recommending sets plan status to recommended."""
    with app.app_context():
        p = ResiliencePlanningService.create_plan("Plan", "Desc", 20000.0, 12, 10.0, 80.0, opt_setup["o1"].id)
        ResiliencePlanningService.add_candidate(p.id, opt_setup["i1"].id, 5000.0, opt_setup["o1"].id)
        rec = PortfolioOptimizationService.recommend_portfolio(p.id, opt_setup["o1"].id)
        assert rec.status == "recommended"


def test_api_optimize_endpoint(app, client, opt_setup):
    """Test 9: REST API optimize plan endpoint."""
    with app.app_context():
        p = ResiliencePlanningService.create_plan("Plan", "Desc", 20000.0, 12, 10.0, 80.0, opt_setup["o1"].id)
        p_id = p.id
    res = client.post(
        f'/api/v1/strategic-resilience/plans/{p_id}/optimize',
        json={"org_id": opt_setup["o1"].id},
        headers=opt_setup["headers"]
    )
    assert res.status_code == 200


def test_api_optimize_missing_org(app, client, opt_setup):
    """Test 10: Optimize REST API missing parameters returns 400."""
    with app.app_context():
        p = ResiliencePlanningService.create_plan("Plan", "Desc", 20000.0, 12, 10.0, 80.0, opt_setup["o1"].id)
        p_id = p.id
    res = client.post(
        f'/api/v1/strategic-resilience/plans/{p_id}/optimize',
        json={},
        headers=opt_setup["headers"]
    )
    assert res.status_code == 400
