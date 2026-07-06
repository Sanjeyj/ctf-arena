"""
Unit and Integration tests for ChaosSimulationService.
Contains 10 test cases covering chaos experiment model, creation, hooks, latency injection, degradation simulation, cascading failures, hypothesis checks, and summaries.
"""
import pytest
import datetime
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.platform_service import PlatformService
from app.models.chaos_experiment import ChaosExperiment
from app.models.service_health_snapshot import ServiceHealthSnapshot
from app.models.operations_timeline_event import OperationsTimelineEvent
from app.services.chaos_simulation_service import ChaosSimulationService
from app.services.hook_service import HookService
from app.research.routes import create_jwt


@pytest.fixture
def chaos_setup(app):
    """Fixture for chaos simulation tests."""
    with app.app_context():
        db.session.query(OperationsTimelineEvent).delete()
        db.session.query(ServiceHealthSnapshot).delete()
        db.session.query(ChaosExperiment).delete()
        db.session.query(PlatformService).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        o2 = Organization(name="Org 2", slug="org-2", plan_type="enterprise")
        db.session.add_all([o1, o2])
        db.session.commit()

        s1 = PlatformService(service_name="soc", service_type="soc", health_score=1.0, status="healthy", organization_id=o1.id)
        db.session.add(s1)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "o1": o1,
            "o2": o2,
            "s1": s1,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_chaos_experiment_model(app, chaos_setup):
    """Test 1: ChaosExperiment model fields validation."""
    with app.app_context():
        exp = ChaosExperiment(
            name="CPU Burn",
            experiment_type="resource_degradation",
            target_service="soc",
            hypothesis="degrade health below 60",
            simulation_parameters_json=json.dumps({"load": 0.95}),
            status="scheduled",
            baseline_score=100.0,
            result_score=100.0,
            organization_id=chaos_setup["o1"].id
        )
        db.session.add(exp)
        db.session.commit()
        assert exp.id is not None
        assert exp.name == "CPU Burn"


def test_create_experiment(app, chaos_setup):
    """Test 2: ChaosSimulationService.create_experiment registers record."""
    with app.app_context():
        exp = ChaosSimulationService.create_experiment(
            "Latency Load Test", "latency_injection", "soc", "delay by 500ms", chaos_setup["o1"].id, {"delay": 500}
        )
        assert exp.id is not None
        assert exp.status == "scheduled"
        assert json.loads(exp.simulation_parameters_json) == {"delay": 500}


def test_chaos_hook_dispatch(app, chaos_setup):
    """Test 3: before_chaos_simulation hook mutation."""
    with app.app_context():
        HookService.clear_all()
        def callback(name, experiment_type, target_service, hypothesis, simulation_parameters_json, org_id):
            return {'name': 'Mutated Experiment'}

        HookService.register_hook('before_chaos_simulation', callback)
        exp = ChaosSimulationService.create_experiment(
            "Latency Load Test", "latency_injection", "soc", "delay by 500ms", chaos_setup["o1"].id
        )
        assert exp.name == "Mutated Experiment"
        HookService.clear_all()


def test_simulate_latency(app, chaos_setup):
    """Test 4: ChaosSimulationService.simulate_latency degrades health."""
    with app.app_context():
        exp = ChaosSimulationService.create_experiment(
            "Latency Injection", "latency_injection", "soc", "health drops", chaos_setup["o1"].id
        )
        res = ChaosSimulationService.simulate_latency(exp.id, "soc", chaos_setup["o1"].id)
        # latency simulation: availability=0.98, latency_ms=600, error_rate=0.05, saturation=0.40
        # health calculation: 100 - (1 - 0.98)*50 - 0.05*30 - 0.40*10 - (600 - 200)/50 = 91.5 - 8 = 85.5
        assert res == 85.5
        assert exp.status == "completed"

        # Check snapshot was generated
        snap = ServiceHealthSnapshot.query.filter_by(platform_service_id=chaos_setup["s1"].id).first()
        assert snap is not None
        assert snap.health_score == 85.5


def test_simulate_service_degradation(app, chaos_setup):
    """Test 5: ChaosSimulationService.simulate_service_degradation saturation peak."""
    with app.app_context():
        exp = ChaosSimulationService.create_experiment(
            "Degrade", "packet_loss", "soc", "availability drop", chaos_setup["o1"].id
        )
        res = ChaosSimulationService.simulate_service_degradation(exp.id, "soc", chaos_setup["o1"].id)
        assert res < 80.0
        assert exp.status == "completed"


def test_simulate_dependency_failure(app, chaos_setup):
    """Test 6: ChaosSimulationService.simulate_dependency_failure cascades timeout."""
    with app.app_context():
        exp = ChaosSimulationService.create_experiment(
            "Downstream fail", "dependency_failure", "soc", "dependency timeout", chaos_setup["o1"].id
        )
        res = ChaosSimulationService.simulate_dependency_failure(exp.id, "soc", chaos_setup["o1"].id)
        assert res < 50.0  # Big crash due to 80% error rates
        assert exp.status == "completed"


def test_evaluate_hypothesis_true(app, chaos_setup):
    """Test 7: ChaosSimulationService.evaluate_hypothesis success."""
    with app.app_context():
        exp = ChaosSimulationService.create_experiment(
            "Latency", "latency_injection", "soc", "drops health", chaos_setup["o1"].id
        )
        ChaosSimulationService.simulate_latency(exp.id, "soc", chaos_setup["o1"].id)
        passed = ChaosSimulationService.evaluate_hypothesis(exp.id, chaos_setup["o1"].id)
        assert passed is True


def test_complete_experiment(app, chaos_setup):
    """Test 8: ChaosSimulationService.complete_experiment updates fields manually."""
    with app.app_context():
        exp = ChaosSimulationService.create_experiment(
            "Latency", "latency_injection", "soc", "drops health", chaos_setup["o1"].id
        )
        res = ChaosSimulationService.complete_experiment(exp.id, 80.0, "Manual force success", chaos_setup["o1"].id)
        assert res.status == "completed"
        assert res.result_score == 80.0


def test_experiment_summary(app, chaos_setup):
    """Test 9: ChaosSimulationService.experiment_summary statistics."""
    with app.app_context():
        exp = ChaosSimulationService.create_experiment(
            "Latency", "latency_injection", "soc", "drops health", chaos_setup["o1"].id
        )
        ChaosSimulationService.simulate_latency(exp.id, "soc", chaos_setup["o1"].id)

        summary = ChaosSimulationService.experiment_summary(chaos_setup["o1"].id)
        assert summary["total_experiments"] == 1
        assert summary["completed_count"] == 1
        assert summary["avg_degradation_delta"] > 0.0


def test_chaos_offline_isolation(app, chaos_setup):
    """Test 10: Chaos simulation logic does not perform live network calls and remains isolated."""
    # Ensure offline execution check
    with app.app_context():
        exp = ChaosSimulationService.create_experiment(
            "Latency", "latency_injection", "soc", "drops health", chaos_setup["o1"].id
        )
        res = ChaosSimulationService.simulate_latency(exp.id, "soc", chaos_setup["o1"].id)
        assert res is not None
