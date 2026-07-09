import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.security_investment import SecurityInvestment
from app.services.security_investment_service import SecurityInvestmentService


@pytest.fixture
def inv_setup(app):
    with app.app_context():
        db.session.query(SecurityInvestment).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        db.session.add(o1)
        db.session.commit()

        yield {"o1": o1}


def test_create_investment_valid(app, inv_setup):
    """Test 1: Create a valid security investment."""
    with app.app_context():
        i = SecurityInvestmentService.create_investment(
            "MFA Deployment", "control", 10000.0, 2000.0, 50000.0, 60.0, inv_setup["o1"].id
        )
        assert i.id is not None
        assert i.status == "proposed"


def test_create_investment_invalid_category(app, inv_setup):
    """Test 2: Invalid category triggers ValueError."""
    with app.app_context():
        with pytest.raises(ValueError):
            SecurityInvestmentService.create_investment(
                "MFA Deployment", "invalid_cat", 10000.0, 2000.0, 50000.0, 60.0, inv_setup["o1"].id
            )


def test_calculate_roi(inv_setup):
    """Test 3: ROI expectation calculation is correct."""
    i = SecurityInvestment(cost=10000.0, expected_loss_reduction=50000.0)
    # 50000 / 10000 * 100 = 500.0
    assert SecurityInvestmentService.calculate_roi(i) == 500.0


def test_calculate_roi_zero_cost(inv_setup):
    """Test 4: ROI for zero cost returns expected loss reduction directly."""
    i = SecurityInvestment(cost=0.0, expected_loss_reduction=50000.0)
    assert SecurityInvestmentService.calculate_roi(i) == 50000.0


def test_calculate_rosi(inv_setup):
    """Test 5: ROSI expectation calculation is correct."""
    i = SecurityInvestment(cost=8000.0, annual_operating_cost=2000.0, expected_loss_reduction=50000.0)
    # total cost = 10000. (50000 - 10000) / 10000 * 100 = 400.0
    assert SecurityInvestmentService.calculate_rosi(i) == 400.0


def test_calculate_rosi_zero_cost(inv_setup):
    """Test 6: ROSI for zero cost returns expected loss reduction directly."""
    i = SecurityInvestment(cost=0.0, annual_operating_cost=0.0, expected_loss_reduction=50000.0)
    assert SecurityInvestmentService.calculate_rosi(i) == 50000.0


def test_calculate_priority_score(inv_setup):
    """Test 7: Dynamic priority score correctly weighted."""
    i = SecurityInvestment(rosi_score=100.0, expected_risk_reduction=50.0)
    # (100 * 0.6) + (50 * 0.4) = 60 + 20 = 80.0
    assert SecurityInvestmentService.calculate_priority(i) == 80.0


def test_calculate_priority_score_negative_rosi(inv_setup):
    """Test 8: Priority score handles negative ROSI as 0."""
    i = SecurityInvestment(rosi_score=-50.0, expected_risk_reduction=50.0)
    # (0 * 0.6) + (50 * 0.4) = 20.0
    assert SecurityInvestmentService.calculate_priority(i) == 20.0


def test_rank_investments(app, inv_setup):
    """Test 9: Rank investments sorts descending by ROSI."""
    with app.app_context():
        SecurityInvestmentService.create_investment(
            "Inv 1", "control", 10000.0, 0.0, 20000.0, 30.0, inv_setup["o1"].id
        )
        SecurityInvestmentService.create_investment(
            "Inv 2", "control", 5000.0, 0.0, 30000.0, 30.0, inv_setup["o1"].id
        )
        ranked = SecurityInvestmentService.rank_investments(inv_setup["o1"].id)
        assert ranked[0].title == "Inv 2"


def test_portfolio_summary_empty(app, inv_setup):
    """Test 10: Empty investment portfolio summary returns zero defaults."""
    with app.app_context():
        db.session.query(SecurityInvestment).delete()
        db.session.commit()
        summary = SecurityInvestmentService.portfolio_summary(inv_setup["o1"].id)
        assert summary["total_cost"] == 0.0
        assert summary["expected_savings"] == 0.0
        assert summary["avg_rosi"] == 0.0
