import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.quantitative_risk_scenario import QuantitativeRiskScenario
from app.models.risk_appetite_profile import RiskAppetiteProfile
from app.models.risk_portfolio_metric import RiskPortfolioMetric
from app.models.security_investment import SecurityInvestment
from app.services.risk_portfolio_service import RiskPortfolioService
from app.services.risk_scenario_service import RiskScenarioService
from app.services.frequency_model_service import FrequencyModelService
from app.services.loss_model_service import LossModelService


@pytest.fixture
def port_setup(app):
    with app.app_context():
        db.session.query(RiskPortfolioMetric).delete()
        db.session.query(SecurityInvestment).delete()
        db.session.query(QuantitativeRiskScenario).delete()
        db.session.query(RiskAppetiteProfile).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        db.session.add(o1)
        db.session.commit()

        s1 = QuantitativeRiskScenario(
            name="S1", scenario_type="ransomware",
            inherent_risk_score=60.0, residual_risk_score=40.0, organization_id=o1.id
        )
        db.session.add(s1)
        db.session.commit()

        yield {"o1": o1, "s1": s1}


def test_calculate_inherent_risk_avg(app, port_setup):
    """Test 1: Computes average inherent risk correctly."""
    with app.app_context():
        val = RiskPortfolioService.calculate_inherent_risk(port_setup["o1"].id)
        assert val == 60.0


def test_calculate_residual_risk_avg(app, port_setup):
    """Test 2: Computes average residual risk correctly."""
    with app.app_context():
        val = RiskPortfolioService.calculate_residual_risk(port_setup["o1"].id)
        assert val == 40.0


def test_calculate_expected_annual_loss(app, port_setup):
    """Test 3: Computes composite EAL across scenarios."""
    with app.app_context():
        # Setup analytical EAL for s1
        FrequencyModelService.create_estimate(port_setup["s1"].id, "fixed", 1.0, 2.0, 3.0, 0.9, "history", port_setup["o1"].id)
        LossModelService.create_loss_estimate(port_setup["s1"].id, "response_cost", 1000.0, 5000.0, 10000.0, 0.9, port_setup["o1"].id)

        eal = RiskPortfolioService.calculate_expected_annual_loss(port_setup["o1"].id)
        # EAL = 2.0 * 5166.67 = 10333.34
        assert eal == 10333.34


def test_portfolio_efficiency_zero_cost(app, port_setup):
    """Test 4: Efficiency returns reduction value if cost is zero."""
    with app.app_context():
        inv = SecurityInvestment(
            title="MFA", investment_category="control", cost=0.0,
            expected_loss_reduction=15000.0, organization_id=port_setup["o1"].id
        )
        db.session.add(inv)
        db.session.commit()
        eff = RiskPortfolioService.calculate_portfolio_efficiency(port_setup["o1"].id)
        assert eff == 15000.0


def test_portfolio_efficiency_nonzero_cost(app, port_setup):
    """Test 5: Efficiency returns loss reduction per dollar cost."""
    with app.app_context():
        inv = SecurityInvestment(
            title="MFA", investment_category="control", cost=5000.0,
            expected_loss_reduction=15000.0, organization_id=port_setup["o1"].id
        )
        db.session.add(inv)
        db.session.commit()
        eff = RiskPortfolioService.calculate_portfolio_efficiency(port_setup["o1"].id)
        # 15000 / 5000 = 3.0
        assert eff == 3.0


def test_check_risk_appetite_pass(app, port_setup):
    """Test 6: Returns appetite passed if limits are not breached."""
    with app.app_context():
        # Appetite limit EAL = 50,000
        p = RiskAppetiteProfile(
            name="Conservative Profile", maximum_annualized_loss=50000.0,
            maximum_residual_risk_score=50.0, status='active', organization_id=port_setup["o1"].id
        )
        db.session.add(p)
        db.session.commit()

        # EAL = 10000.0, Max Residual = 40.0
        FrequencyModelService.create_estimate(port_setup["s1"].id, "fixed", 1.0, 2.0, 3.0, 0.9, "history", port_setup["o1"].id)
        LossModelService.create_loss_estimate(port_setup["s1"].id, "response_cost", 1000.0, 5000.0, 10000.0, 0.9, port_setup["o1"].id)

        res = RiskPortfolioService.check_risk_appetite(port_setup["o1"].id)
        assert res["appetite_breached"] is False


def test_check_risk_appetite_breach_eal(app, port_setup):
    """Test 7: Returns appetite breached if total EAL exceeds limit."""
    with app.app_context():
        # Appetite limit EAL = 5,000
        p = RiskAppetiteProfile(
            name="Aggressive Profile", maximum_annualized_loss=5000.0,
            maximum_residual_risk_score=50.0, status='active', organization_id=port_setup["o1"].id
        )
        db.session.add(p)
        db.session.commit()

        # EAL = 10000.0
        FrequencyModelService.create_estimate(port_setup["s1"].id, "fixed", 1.0, 2.0, 3.0, 0.9, "history", port_setup["o1"].id)
        LossModelService.create_loss_estimate(port_setup["s1"].id, "response_cost", 1000.0, 5000.0, 10000.0, 0.9, port_setup["o1"].id)

        res = RiskPortfolioService.check_risk_appetite(port_setup["o1"].id)
        assert res["appetite_breached"] is True
        assert res["eal_breached"] is True


def test_check_risk_appetite_breach_score(app, port_setup):
    """Test 8: Returns appetite breached if residual score exceeds limit."""
    with app.app_context():
        # Appetite limit max residual score = 30.0
        p = RiskAppetiteProfile(
            name="Conservative Profile", maximum_annualized_loss=500000.0,
            maximum_residual_risk_score=30.0, status='active', organization_id=port_setup["o1"].id
        )
        db.session.add(p)
        db.session.commit()

        # Max Residual = 40.0
        res = RiskPortfolioService.check_risk_appetite(port_setup["o1"].id)
        assert res["appetite_breached"] is True
        assert res["residual_risk_score_breached"] is True


def test_compare_portfolios(app, port_setup):
    """Test 9: Compare portfolio deltas correctly."""
    with app.app_context():
        m1 = RiskPortfolioMetric(metric_type='composite', expected_annual_loss=20000.0, portfolio_efficiency_score=2.0, organization_id=port_setup["o1"].id)
        m2 = RiskPortfolioMetric(metric_type='composite', expected_annual_loss=15000.0, portfolio_efficiency_score=3.5, organization_id=port_setup["o1"].id)
        db.session.add_all([m1, m2])
        db.session.commit()

        res = RiskPortfolioService.compare_portfolios(port_setup["o1"].id)
        # current(m2) - prev(m1)
        assert res["delta_eal"] == -5000.0
        assert res["delta_efficiency"] == 1.5


def test_portfolio_summary_saves_metric(app, port_setup):
    """Test 10: Portfolio summary executes successfully and writes history."""
    with app.app_context():
        summary = RiskPortfolioService.portfolio_summary(port_setup["o1"].id)
        assert summary["total_scenarios"] == 1
        metric = RiskPortfolioMetric.query.filter_by(organization_id=port_setup["o1"].id).first()
        assert metric is not None
