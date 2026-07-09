import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.stress_test_scenario import StressTestScenario
from app.models.stress_test_run import StressTestRun
from app.services.stress_testing_service import StressTestingService
from app.research.routes import create_jwt


@pytest.fixture
def sim_setup(app):
    with app.app_context():
        db.session.query(StressTestRun).delete()
        db.session.query(StressTestScenario).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        db.session.add(o1)
        db.session.commit()

        s1 = StressTestingService.create_scenario(
            "Cloud Outage", "Simulated region crash", "cloud_region_failure",
            "critical", 48.0, ["US-East"], 0.05, 2.0, o1.id
        )

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "o1": o1,
            "s1": s1,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_create_run_valid(app, sim_setup):
    """Test 1: Create stress run in pending status."""
    with app.app_context():
        run = StressTestingService.create_run(sim_setup["s1"].id, 100, 42, sim_setup["o1"].id)
        assert run.id is not None
        assert run.status == "pending"


def test_simulate_stress_computes_loss(app, sim_setup):
    """Test 2: Simulation updates loss and resilience indexes."""
    with app.app_context():
        run = StressTestingService.create_run(sim_setup["s1"].id, 100, 42, sim_setup["o1"].id)
        completed = StressTestingService.simulate_stress(run.id, sim_setup["o1"].id)
        assert completed.status == "completed"
        assert completed.stressed_loss > completed.baseline_loss
        assert completed.stressed_resilience < completed.baseline_resilience


def test_simulate_stress_determinism_seed(app, sim_setup):
    """Test 3: Same seed yields exactly identical results."""
    with app.app_context():
        run1 = StressTestingService.create_run(sim_setup["s1"].id, 100, 42, sim_setup["o1"].id)
        r1 = StressTestingService.simulate_stress(run1.id, sim_setup["o1"].id)

        run2 = StressTestingService.create_run(sim_setup["s1"].id, 100, 42, sim_setup["o1"].id)
        r2 = StressTestingService.simulate_stress(run2.id, sim_setup["o1"].id)

        assert r1.stressed_loss == r2.stressed_loss
        assert r1.stressed_resilience == r2.stressed_resilience


def test_simulate_stress_variance_seed(app, sim_setup):
    """Test 4: Different seeds yields variance."""
    with app.app_context():
        run1 = StressTestingService.create_run(sim_setup["s1"].id, 100, 42, sim_setup["o1"].id)
        r1 = StressTestingService.simulate_stress(run1.id, sim_setup["o1"].id)

        run2 = StressTestingService.create_run(sim_setup["s1"].id, 100, 99, sim_setup["o1"].id)
        r2 = StressTestingService.simulate_stress(run2.id, sim_setup["o1"].id)

        assert r1.stressed_loss != r2.stressed_loss


def test_calculate_stressed_loss(app, sim_setup):
    """Test 5: Calculates stressed loss helper."""
    with app.app_context():
        run = StressTestingService.create_run(sim_setup["s1"].id, 100, 42, sim_setup["o1"].id)
        StressTestingService.simulate_stress(run.id, sim_setup["o1"].id)
        val = StressTestingService.calculate_stressed_loss(run.id, sim_setup["o1"].id)
        assert val > 0.0


def test_calculate_resilience_degradation(app, sim_setup):
    """Test 6: Calculates degradation delta helper."""
    with app.app_context():
        run = StressTestingService.create_run(sim_setup["s1"].id, 100, 42, sim_setup["o1"].id)
        StressTestingService.simulate_stress(run.id, sim_setup["o1"].id)
        deg = StressTestingService.calculate_resilience_degradation(run.id, sim_setup["o1"].id)
        assert deg > 0.0


def test_calculate_recovery_time(app, sim_setup):
    """Test 7: Calculates recovery duration hours helper."""
    with app.app_context():
        run = StressTestingService.create_run(sim_setup["s1"].id, 100, 42, sim_setup["o1"].id)
        StressTestingService.simulate_stress(run.id, sim_setup["o1"].id)
        rec = StressTestingService.calculate_recovery_time(run.id, sim_setup["o1"].id)
        # 48.0 * 2.0 = 96.0
        assert rec == 96.0


def test_check_appetite_breach(app, sim_setup):
    """Test 8: Evaluates if appetite profile limit was breached."""
    with app.app_context():
        run = StressTestingService.create_run(sim_setup["s1"].id, 100, 42, sim_setup["o1"].id)
        StressTestingService.simulate_stress(run.id, sim_setup["o1"].id)
        assert StressTestingService.check_appetite_breach(run.id, sim_setup["o1"].id) in [True, False]


def test_api_simulate_stress(app, client, sim_setup):
    """Test 9: REST API post simulate stress runs successfully."""
    payload = {"org_id": sim_setup["o1"].id, "random_seed": 42, "iteration_count": 100}
    res = client.post(
        f'/api/v1/strategic-resilience/stress-scenarios/{sim_setup["s1"].id}/simulate',
        json=payload,
        headers=sim_setup["headers"]
    )
    assert res.status_code == 200


def test_api_get_run_details(app, client, sim_setup):
    """Test 10: REST API get stress runs endpoints details."""
    with app.app_context():
        run = StressTestingService.create_run(sim_setup["s1"].id, 100, 42, sim_setup["o1"].id)
        StressTestingService.simulate_stress(run.id, sim_setup["o1"].id)
    res = client.get(
        f'/api/v1/strategic-resilience/stress-runs/{run.id}?org_id={sim_setup["o1"].id}',
        headers=sim_setup["headers"]
    )
    assert res.status_code == 200
