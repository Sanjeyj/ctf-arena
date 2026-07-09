import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.control_investment_option import ControlInvestmentOption
from app.services.control_investment_service import ControlInvestmentService
from app.research.routes import create_jwt


@pytest.fixture
def ctrl_setup(app):
    with app.app_context():
        db.session.query(ControlInvestmentOption).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        db.session.add(o1)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "o1": o1,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_create_option_valid(app, ctrl_setup):
    """Test 1: Create valid control investment option."""
    with app.app_context():
        opt = ControlInvestmentService.create_option(
            "PR.AC-1", "MFA Enforcement", 5000.0, 1000.0, 40.0, 50.0, 20.0, 60, [], ctrl_setup["o1"].id
        )
        assert opt.id is not None
        assert opt.status == "proposed"


def test_calculate_control_gain(app, ctrl_setup):
    """Test 2: Control gain matches expected improvement."""
    with app.app_context():
        opt = ControlInvestmentService.create_option(
            "PR.AC-1", "MFA", 5000.0, 1000.0, 40.0, 50.0, 20.0, 60, [], ctrl_setup["o1"].id
        )
        val = ControlInvestmentService.calculate_control_gain(opt.id, ctrl_setup["o1"].id)
        assert val == 40.0


def test_calculate_risk_reduction(app, ctrl_setup):
    """Test 3: Risk reduction matches expected value."""
    with app.app_context():
        opt = ControlInvestmentService.create_option(
            "PR.AC-1", "MFA", 5000.0, 1000.0, 40.0, 50.0, 20.0, 60, [], ctrl_setup["o1"].id
        )
        val = ControlInvestmentService.calculate_risk_reduction(opt.id, ctrl_setup["o1"].id)
        assert val == 50.0


def test_calculate_resilience_gain(app, ctrl_setup):
    """Test 4: Resilience gain matches expected value."""
    with app.app_context():
        opt = ControlInvestmentService.create_option(
            "PR.AC-1", "MFA", 5000.0, 1000.0, 40.0, 50.0, 20.0, 60, [], ctrl_setup["o1"].id
        )
        val = ControlInvestmentService.calculate_resilience_gain(opt.id, ctrl_setup["o1"].id)
        assert val == 20.0


def test_evaluate_dependencies_empty(app, ctrl_setup):
    """Test 5: Evaluates empty dependencies list as resolved."""
    with app.app_context():
        opt = ControlInvestmentService.create_option(
            "PR.AC-1", "MFA", 5000.0, 1000.0, 40.0, 50.0, 20.0, 60, [], ctrl_setup["o1"].id
        )
        unresolved = ControlInvestmentService.evaluate_dependencies(opt.id, ctrl_setup["o1"].id)
        assert len(unresolved) == 0


def test_evaluate_dependencies_unresolved(app, ctrl_setup):
    """Test 6: Returns list of unresolved prerequisite control references."""
    with app.app_context():
        opt = ControlInvestmentService.create_option(
            "PR.AC-2", "MFA Enforce", 5000.0, 1000.0, 40.0, 50.0, 20.0, 60, ["PR.AC-1"], ctrl_setup["o1"].id
        )
        unresolved = ControlInvestmentService.evaluate_dependencies(opt.id, ctrl_setup["o1"].id)
        assert "PR.AC-1" in unresolved


def test_evaluate_dependencies_resolved(app, ctrl_setup):
    """Test 7: Prerequisite is resolved if its option is approved."""
    with app.app_context():
        # Create prerequisite option and set status to approved
        p = ControlInvestmentService.create_option(
            "PR.AC-1", "Prereq", 2000.0, 0.0, 10.0, 10.0, 5.0, 30, [], ctrl_setup["o1"].id
        )
        p.status = 'approved'
        db.session.commit()

        opt = ControlInvestmentService.create_option(
            "PR.AC-2", "MFA Enforce", 5000.0, 1000.0, 40.0, 50.0, 20.0, 60, ["PR.AC-1"], ctrl_setup["o1"].id
        )
        unresolved = ControlInvestmentService.evaluate_dependencies(opt.id, ctrl_setup["o1"].id)
        assert len(unresolved) == 0


def test_rank_options(app, ctrl_setup):
    """Test 8: Ranks options by reduction per implementation cost."""
    with app.app_context():
        ControlInvestmentService.create_option(
            "PR.AC-1", "O1", 10000.0, 0.0, 30.0, 30.0, 10.0, 30, [], ctrl_setup["o1"].id
        )
        ControlInvestmentService.create_option(
            "PR.AC-2", "O2", 2000.0, 0.0, 20.0, 20.0, 10.0, 30, [], ctrl_setup["o1"].id
        )
        ranked = ControlInvestmentService.rank_options(ctrl_setup["o1"].id)
        assert ranked[0].title == "O2"


def test_control_investment_summary(app, ctrl_setup):
    """Test 9: Summary returns aggregates metrics."""
    with app.app_context():
        ControlInvestmentService.create_option(
            "PR.AC-1", "O1", 5000.0, 0.0, 30.0, 30.0, 10.0, 30, [], ctrl_setup["o1"].id
        )
        summary = ControlInvestmentService.control_investment_summary(ctrl_setup["o1"].id)
        assert summary["total_options"] == 1
        assert summary["total_implementation_cost"] == 5000.0


def test_api_get_control_options(app, client, ctrl_setup):
    """Test 10: REST API list control options endpoint."""
    res = client.get(
        f'/api/v1/strategic-resilience/control-options?org_id={ctrl_setup["o1"].id}',
        headers=ctrl_setup["headers"]
    )
    assert res.status_code == 200
