import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.quantitative_risk_scenario import QuantitativeRiskScenario
from app.models.loss_magnitude_estimate import LossMagnitudeEstimate
from app.services.loss_model_service import LossModelService


@pytest.fixture
def loss_setup(app):
    with app.app_context():
        db.session.query(LossMagnitudeEstimate).delete()
        db.session.query(QuantitativeRiskScenario).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        db.session.add(o1)
        db.session.commit()

        s1 = QuantitativeRiskScenario(name="Ransomware Scenario", scenario_type="ransomware", organization_id=o1.id)
        db.session.add(s1)
        db.session.commit()

        yield {"o1": o1, "s1": s1}


def test_validate_loss_range_valid(loss_setup):
    """Test 1: Valid bounds validation returns True."""
    assert LossModelService.validate_loss_range(100.0, 500.0, 1000.0) is True


def test_validate_loss_range_negative(loss_setup):
    """Test 2: Negative bounds trigger ValueError."""
    with pytest.raises(ValueError):
        LossModelService.validate_loss_range(-10.0, 500.0, 1000.0)


def test_validate_loss_range_invalid_order(loss_setup):
    """Test 3: Incorrect order triggers ValueError."""
    with pytest.raises(ValueError):
        LossModelService.validate_loss_range(500.0, 100.0, 1000.0)


def test_create_loss_estimate_valid(app, loss_setup):
    """Test 4: Create valid loss estimate updates DB."""
    with app.app_context():
        est = LossModelService.create_loss_estimate(
            loss_setup["s1"].id, "response_cost", 1000.0, 5000.0, 10000.0, 0.9, loss_setup["o1"].id
        )
        assert est.id is not None


def test_create_loss_estimate_invalid_type(app, loss_setup):
    """Test 5: Unsupported loss category triggers ValueError."""
    with app.app_context():
        with pytest.raises(ValueError):
            LossModelService.create_loss_estimate(
                loss_setup["s1"].id, "invalid_loss_category", 1000.0, 5000.0, 10000.0, 0.9, loss_setup["o1"].id
            )


def test_calculate_expected_loss_pert(app, loss_setup):
    """Test 6: Correct PERT expectation calculation."""
    with app.app_context():
        est = LossMagnitudeEstimate(minimum_loss=1000, most_likely_loss=4000, maximum_loss=7000)
        expected = LossModelService.calculate_expected_loss(est)
        # (1000 + 4*4000 + 7000) / 6 = 24000 / 6 = 4000.0
        assert expected == 4000.0


def test_calculate_loss_components_empty(app, loss_setup):
    """Test 7: Empty loss categories return empty dict."""
    with app.app_context():
        components = LossModelService.calculate_loss_components(loss_setup["s1"].id, loss_setup["o1"].id)
        assert components == {}


def test_calculate_loss_components_filled(app, loss_setup):
    """Test 8: Filled loss categories populated."""
    with app.app_context():
        LossModelService.create_loss_estimate(
            loss_setup["s1"].id, "response_cost", 1000.0, 5000.0, 10000.0, 0.9, loss_setup["o1"].id
        )
        components = LossModelService.calculate_loss_components(loss_setup["s1"].id, loss_setup["o1"].id)
        assert "response_cost" in components


def test_compare_loss_profiles_valid(app, loss_setup):
    """Test 9: Compare two scenarios profiles expected loss."""
    with app.app_context():
        s2 = QuantitativeRiskScenario(name="Ransomware 2", scenario_type="ransomware", organization_id=loss_setup["o1"].id)
        db.session.add(s2)
        db.session.commit()

        # Add loss to s1
        LossModelService.create_loss_estimate(
            loss_setup["s1"].id, "response_cost", 1000.0, 5000.0, 10000.0, 0.9, loss_setup["o1"].id
        )

        res = LossModelService.compare_loss_profiles(loss_setup["s1"].id, s2.id, loss_setup["o1"].id)
        assert res["scenario1"]["expected_loss"] > res["scenario2"]["expected_loss"]


def test_loss_summary_empty(app, loss_setup):
    """Test 10: Empty summary defaults."""
    with app.app_context():
        # Clear database to test empty summary
        db.session.query(LossMagnitudeEstimate).delete()
        db.session.commit()
        summary = LossModelService.loss_summary(loss_setup["o1"].id)
        assert summary["total_estimates"] == 0
        assert summary["avg_expected_loss"] == 0.0
