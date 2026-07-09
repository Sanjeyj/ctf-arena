import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.quantitative_risk_scenario import QuantitativeRiskScenario
from app.models.risk_frequency_estimate import RiskFrequencyEstimate
from app.services.frequency_model_service import FrequencyModelService


@pytest.fixture
def freq_setup(app):
    with app.app_context():
        db.session.query(RiskFrequencyEstimate).delete()
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


def test_validate_distribution_valid(freq_setup):
    """Test 1: Valid bounds validation returns True."""
    assert FrequencyModelService.validate_distribution(1.0, 2.0, 5.0) is True


def test_validate_distribution_negative(freq_setup):
    """Test 2: Negative bounds trigger ValueError."""
    with pytest.raises(ValueError):
        FrequencyModelService.validate_distribution(-1.0, 2.0, 5.0)


def test_validate_distribution_invalid_order(freq_setup):
    """Test 3: Incorrect min <= mode <= max order triggers ValueError."""
    with pytest.raises(ValueError):
        FrequencyModelService.validate_distribution(2.0, 1.0, 5.0)


def test_create_estimate_valid(app, freq_setup):
    """Test 4: Create valid frequency estimate updates DB."""
    with app.app_context():
        est = FrequencyModelService.create_estimate(
            freq_setup["s1"].id, "pert", 0.5, 1.0, 3.0, 0.9, "history", freq_setup["o1"].id
        )
        assert est.id is not None
        assert est.annual_rate > 0.0


def test_create_estimate_invalid_type(app, freq_setup):
    """Test 5: Creating with unsupported type triggers ValueError."""
    with app.app_context():
        with pytest.raises(ValueError):
            FrequencyModelService.create_estimate(
                freq_setup["s1"].id, "invalid_type", 0.5, 1.0, 3.0, 0.9, "history", freq_setup["o1"].id
            )


def test_calculate_annual_rate_pert(app, freq_setup):
    """Test 6: PERT calculation correct mean."""
    with app.app_context():
        est = RiskFrequencyEstimate(frequency_type="pert", minimum_frequency=1, most_likely_frequency=2, maximum_frequency=9)
        rate = FrequencyModelService.calculate_annual_rate(est)
        # (1 + 4*2 + 9) / 6 = 18 / 6 = 3.0
        assert rate == 3.0


def test_calculate_annual_rate_triangular(app, freq_setup):
    """Test 7: Triangular calculation correct mean."""
    with app.app_context():
        est = RiskFrequencyEstimate(frequency_type="triangular", minimum_frequency=1, most_likely_frequency=2, maximum_frequency=9)
        rate = FrequencyModelService.calculate_annual_rate(est)
        # (1 + 2 + 9) / 3 = 12 / 3 = 4.0
        assert rate == 4.0


def test_sample_frequency_fixed(app, freq_setup):
    """Test 8: Fixed frequency sampling returns most likely value."""
    with app.app_context():
        est = RiskFrequencyEstimate(frequency_type="fixed", minimum_frequency=1, most_likely_frequency=5.0, maximum_frequency=9)
        assert FrequencyModelService.sample_frequency(est) == 5.0


def test_sample_frequency_triangular(app, freq_setup):
    """Test 9: Triangular sampling determinism with seed."""
    with app.app_context():
        est = RiskFrequencyEstimate(frequency_type="triangular", minimum_frequency=1, most_likely_frequency=2, maximum_frequency=9)
        s1 = FrequencyModelService.sample_frequency(est, seed=42)
        s2 = FrequencyModelService.sample_frequency(est, seed=42)
        assert s1 == s2


def test_frequency_summary_empty(app, freq_setup):
    """Test 10: Empty registry returns defaults."""
    with app.app_context():
        # Clear database to test empty summary
        db.session.query(RiskFrequencyEstimate).delete()
        db.session.commit()
        summary = FrequencyModelService.frequency_summary(freq_setup["o1"].id)
        assert summary["total_estimates"] == 0
        assert summary["avg_annual_rate"] == 0.0
