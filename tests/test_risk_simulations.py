import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.quantitative_risk_scenario import QuantitativeRiskScenario
from app.models.risk_simulation_run import RiskSimulationRun
from app.services.frequency_model_service import FrequencyModelService
from app.services.loss_model_service import LossModelService
from app.services.risk_simulation_service import RiskSimulationService


@pytest.fixture
def sim_setup(app):
    with app.app_context():
        db.session.query(RiskSimulationRun).delete()
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


def test_create_run_valid(app, sim_setup):
    """Test 1: Create a valid simulation run in DB."""
    with app.app_context():
        run = RiskSimulationService.create_run(sim_setup["s1"].id, "monte_carlo_simulation", 1000, 42, sim_setup["o1"].id)
        assert run.id is not None
        assert run.status == "pending"


def test_create_run_iterations_cap(app, sim_setup):
    """Test 2: Iteration count is capped at 100,000."""
    with app.app_context():
        run = RiskSimulationService.create_run(sim_setup["s1"].id, "monte_carlo_simulation", 150000, 42, sim_setup["o1"].id)
        assert run.iteration_count == 100000


def test_simulate_deterministic(app, sim_setup):
    """Test 3: Deterministic simulation computes analytical EAL."""
    with app.app_context():
        # Setup frequency and loss
        FrequencyModelService.create_estimate(sim_setup["s1"].id, "fixed", 1.0, 2.0, 3.0, 0.9, "history", sim_setup["o1"].id)
        LossModelService.create_loss_estimate(sim_setup["s1"].id, "response_cost", 1000.0, 5000.0, 10000.0, 0.9, sim_setup["o1"].id)

        run = RiskSimulationService.create_run(sim_setup["s1"].id, "deterministic", 100, 42, sim_setup["o1"].id)
        completed = RiskSimulationService.simulate_deterministic(run.id, sim_setup["o1"].id)

        assert completed.status == "completed"
        # EAL = 2.0 * 5166.67 = 10333.34
        assert completed.expected_loss == 10333.34


def test_simulate_monte_carlo(app, sim_setup):
    """Test 4: Monte Carlo simulation completes successfully."""
    with app.app_context():
        FrequencyModelService.create_estimate(sim_setup["s1"].id, "triangular", 1.0, 2.0, 3.0, 0.9, "history", sim_setup["o1"].id)
        LossModelService.create_loss_estimate(sim_setup["s1"].id, "response_cost", 1000.0, 5000.0, 10000.0, 0.9, sim_setup["o1"].id)

        run = RiskSimulationService.create_run(sim_setup["s1"].id, "monte_carlo_simulation", 500, 42, sim_setup["o1"].id)
        completed = RiskSimulationService.simulate_monte_carlo(run.id, sim_setup["o1"].id)

        assert completed.status == "completed"
        assert completed.expected_loss > 0.0


def test_calculate_percentiles(sim_setup):
    """Test 5: Calculates correct percentiles from sorted list."""
    losses = [10.0, 20.0, 30.0, 40.0, 50.0]
    p50 = RiskSimulationService.calculate_percentiles(losses, 50)
    assert p50 == 30.0


def test_calculate_percentiles_empty(sim_setup):
    """Test 6: Percentile calculation for empty list returns 0."""
    assert RiskSimulationService.calculate_percentiles([], 50) == 0.0


def test_calculate_expected_annual_loss_fallback(app, sim_setup):
    """Test 7: Fallback calculation returns estimate based on analytical means."""
    with app.app_context():
        FrequencyModelService.create_estimate(sim_setup["s1"].id, "fixed", 1.0, 2.0, 3.0, 0.9, "history", sim_setup["o1"].id)
        LossModelService.create_loss_estimate(sim_setup["s1"].id, "response_cost", 1000.0, 5000.0, 10000.0, 0.9, sim_setup["o1"].id)
        eal = RiskSimulationService.calculate_expected_annual_loss(sim_setup["s1"].id, sim_setup["o1"].id)
        assert eal == 10333.34


def test_simulation_determinism_seed(app, sim_setup):
    """Test 8: Same seed returns exactly the same Monte Carlo results."""
    with app.app_context():
        FrequencyModelService.create_estimate(sim_setup["s1"].id, "triangular", 1.0, 2.0, 3.0, 0.9, "history", sim_setup["o1"].id)
        LossModelService.create_loss_estimate(sim_setup["s1"].id, "response_cost", 1000.0, 5000.0, 10000.0, 0.9, sim_setup["o1"].id)

        run1 = RiskSimulationService.create_run(sim_setup["s1"].id, "monte_carlo_simulation", 100, 42, sim_setup["o1"].id)
        r1 = RiskSimulationService.simulate_monte_carlo(run1.id, sim_setup["o1"].id)

        run2 = RiskSimulationService.create_run(sim_setup["s1"].id, "monte_carlo_simulation", 100, 42, sim_setup["o1"].id)
        r2 = RiskSimulationService.simulate_monte_carlo(run2.id, sim_setup["o1"].id)

        assert r1.expected_loss == r2.expected_loss


def test_simulation_variance_seed(app, sim_setup):
    """Test 9: Different seeds produce variance."""
    with app.app_context():
        FrequencyModelService.create_estimate(sim_setup["s1"].id, "triangular", 1.0, 2.0, 3.0, 0.9, "history", sim_setup["o1"].id)
        LossModelService.create_loss_estimate(sim_setup["s1"].id, "response_cost", 1000.0, 5000.0, 10000.0, 0.9, sim_setup["o1"].id)

        run1 = RiskSimulationService.create_run(sim_setup["s1"].id, "monte_carlo_simulation", 100, 42, sim_setup["o1"].id)
        r1 = RiskSimulationService.simulate_monte_carlo(run1.id, sim_setup["o1"].id)

        run2 = RiskSimulationService.create_run(sim_setup["s1"].id, "monte_carlo_simulation", 100, 99, sim_setup["o1"].id)
        r2 = RiskSimulationService.simulate_monte_carlo(run2.id, sim_setup["o1"].id)

        assert r1.expected_loss != r2.expected_loss


def test_complete_run_manual(app, sim_setup):
    """Test 10: Complete run updates fields directly."""
    with app.app_context():
        run = RiskSimulationService.create_run(sim_setup["s1"].id, "monte_carlo_simulation", 100, 42, sim_setup["o1"].id)
        completed = RiskSimulationService.complete_run(run.id, 5000.0, 4000.0, 6000.0, 7000.0, 8000.0, sim_setup["o1"].id)
        assert completed.status == "completed"
        assert completed.expected_loss == 5000.0
