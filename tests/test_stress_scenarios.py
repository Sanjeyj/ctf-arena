import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.stress_test_scenario import StressTestScenario
from app.services.stress_testing_service import StressTestingService
from app.research.routes import create_jwt


@pytest.fixture
def stress_setup(app):
    with app.app_context():
        db.session.query(StressTestScenario).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        o2 = Organization(name="Org 2", slug="org-2", plan_type="enterprise")
        db.session.add_all([o1, o2])
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "o1": o1,
            "o2": o2,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_scenario_creation_valid(app, stress_setup):
    """Test 1: Create a valid stress scenario."""
    with app.app_context():
        s = StressTestingService.create_scenario(
            "Cloud Outage", "Simulated region crash", "cloud_region_failure",
            "critical", 48.0, ["US-East"], 0.05, 2.5, stress_setup["o1"].id
        )
        assert s.id is not None
        assert s.status == "draft"


def test_scenario_creation_invalid_category(app, stress_setup):
    """Test 2: Invalid category triggers ValueError."""
    with app.app_context():
        with pytest.raises(ValueError):
            StressTestingService.create_scenario(
                "Cloud Outage", "Desc", "invalid_category",
                "critical", 48.0, ["US-East"], 0.05, 2.5, stress_setup["o1"].id
            )


def test_scenario_creation_invalid_probability(app, stress_setup):
    """Test 3: Probability outside 0-1 bounds triggers ValueError."""
    with app.app_context():
        with pytest.raises(ValueError):
            StressTestingService.create_scenario(
                "Cloud Outage", "Desc", "cloud_region_failure",
                "critical", 48.0, ["US-East"], 1.5, 2.5, stress_setup["o1"].id
            )


def test_scenario_creation_negative_duration(app, stress_setup):
    """Test 4: Negative duration triggers ValueError."""
    with app.app_context():
        with pytest.raises(ValueError):
            StressTestingService.create_scenario(
                "Cloud Outage", "Desc", "cloud_region_failure",
                "critical", -10.0, ["US-East"], 0.05, 2.5, stress_setup["o1"].id
            )


def test_validate_scenario_valid(app, stress_setup):
    """Test 5: Validation returns True for correct fields."""
    with app.app_context():
        s = StressTestScenario(
            name="Ransomware", scenario_category="ransomware_disruption",
            probability=0.1, duration_hours=24.0, organization_id=stress_setup["o1"].id
        )
        assert StressTestingService.validate_scenario(s) is True


def test_validate_scenario_invalid(app, stress_setup):
    """Test 6: Validation returns False for invalid fields."""
    with app.app_context():
        s = StressTestScenario(
            name="", scenario_category="ransomware_disruption",
            probability=1.5, duration_hours=-24.0, organization_id=stress_setup["o1"].id
        )
        assert StressTestingService.validate_scenario(s) is False


def test_api_list_stress_scenarios(app, client, stress_setup):
    """Test 7: REST API list stress scenarios endpoint."""
    res = client.get(
        f'/api/v1/strategic-resilience/stress-scenarios?org_id={stress_setup["o1"].id}',
        headers=stress_setup["headers"]
    )
    assert res.status_code == 200


def test_api_create_stress_scenario(app, client, stress_setup):
    """Test 8: REST API create stress scenario endpoint."""
    payload = {
        "org_id": stress_setup["o1"].id,
        "name": "Ransomware Stress Test",
        "scenario_category": "ransomware_disruption"
    }
    res = client.post(
        '/api/v1/strategic-resilience/stress-scenarios',
        json=payload,
        headers=stress_setup["headers"]
    )
    assert res.status_code == 201


def test_api_stress_scenarios_missing_org(app, client, stress_setup):
    """Test 9: Missing org_id parameter triggers error."""
    res = client.get('/api/v1/strategic-resilience/stress-scenarios', headers=stress_setup["headers"])
    assert res.status_code == 400


def test_scenario_to_dict(app, stress_setup):
    """Test 10: to_dict format correct."""
    with app.app_context():
        s = StressTestingService.create_scenario(
            "Cloud Outage", "Simulated region crash", "cloud_region_failure",
            "critical", 48.0, ["US-East"], 0.05, 2.5, stress_setup["o1"].id
        )
        d = s.to_dict()
        assert d["name"] == "Cloud Outage"
        assert "US-East" in d["affected_domains"]
