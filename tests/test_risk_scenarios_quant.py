import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.quantitative_risk_scenario import QuantitativeRiskScenario
from app.models.business_process import BusinessProcess
from app.services.risk_scenario_service import RiskScenarioService
from app.research.routes import create_jwt


@pytest.fixture
def risk_setup(app):
    with app.app_context():
        db.session.query(QuantitativeRiskScenario).delete()
        db.session.query(BusinessProcess).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        o2 = Organization(name="Org 2", slug="org-2", plan_type="enterprise")
        db.session.add_all([o1, o2])
        db.session.commit()

        bp1 = BusinessProcess(name="Payment processing", criticality="critical", organization_id=o1.id)
        db.session.add(bp1)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "o1": o1,
            "o2": o2,
            "bp1": bp1,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_scenario_creation_valid(app, risk_setup):
    """Test 1: Create a valid scenario."""
    with app.app_context():
        s = RiskScenarioService.create_scenario(
            "Ransomware threat", "Ransomware disrupting payments", "ransomware",
            "server", 1, risk_setup["bp1"].id, "cyber_crime", risk_setup["o1"].id
        )
        assert s.id is not None
        assert s.status == "draft"


def test_scenario_creation_invalid_type(app, risk_setup):
    """Test 2: Create scenario with invalid type throws error."""
    with app.app_context():
        with pytest.raises(ValueError):
            RiskScenarioService.create_scenario(
                "Ransomware threat", "Description", "invalid_type",
                "server", 1, risk_setup["bp1"].id, "cyber_crime", risk_setup["o1"].id
            )


def test_scenario_creation_cross_tenant_bp(app, risk_setup):
    """Test 3: Assign cross-tenant business process throws error."""
    with app.app_context():
        with pytest.raises(ValueError):
            RiskScenarioService.create_scenario(
                "Ransomware threat", "Description", "ransomware",
                "server", 1, risk_setup["bp1"].id, "cyber_crime", risk_setup["o2"].id
            )


def test_scenario_activation(app, risk_setup):
    """Test 4: Activate scenario updates status."""
    with app.app_context():
        s = RiskScenarioService.create_scenario(
            "Ransomware threat", "Description", "ransomware",
            "server", 1, risk_setup["bp1"].id, "cyber_crime", risk_setup["o1"].id
        )
        activated = RiskScenarioService.activate_scenario(s.id, risk_setup["o1"].id)
        assert activated.status == "active"


def test_scenario_link_asset(app, risk_setup):
    """Test 5: Link asset updates fields."""
    with app.app_context():
        s = RiskScenarioService.create_scenario(
            "Ransomware threat", "Description", "ransomware",
            None, None, risk_setup["bp1"].id, "cyber_crime", risk_setup["o1"].id
        )
        linked = RiskScenarioService.link_asset(s.id, "database", 42, risk_setup["o1"].id)
        assert linked.asset_reference_type == "database"
        assert linked.asset_reference_id == 42


def test_scenario_cross_tenant_view_rejection(app, risk_setup):
    """Test 6: Cross-tenant view returns None."""
    with app.app_context():
        s = RiskScenarioService.create_scenario(
            "Ransomware threat", "Description", "ransomware",
            "server", 1, risk_setup["bp1"].id, "cyber_crime", risk_setup["o1"].id
        )
        summary = RiskScenarioService.scenario_summary(s.id, risk_setup["o2"].id)
        assert summary is None


def test_scenario_summary_format(app, risk_setup):
    """Test 7: Summary returns correct dictionary structure."""
    with app.app_context():
        s = RiskScenarioService.create_scenario(
            "Ransomware threat", "Description", "ransomware",
            "server", 1, risk_setup["bp1"].id, "cyber_crime", risk_setup["o1"].id
        )
        summary = RiskScenarioService.scenario_summary(s.id, risk_setup["o1"].id)
        assert summary["name"] == "Ransomware threat"
        assert summary["scenario_type"] == "ransomware"


def test_api_list_scenarios(app, client, risk_setup):
    """Test 8: REST API list scenarios endpoint."""
    res = client.get(
        f'/api/v1/risk-quantification/scenarios?org_id={risk_setup["o1"].id}',
        headers=risk_setup["headers"]
    )
    assert res.status_code == 200


def test_api_create_scenario(app, client, risk_setup):
    """Test 9: REST API create scenario endpoint."""
    payload = {
        "org_id": risk_setup["o1"].id,
        "name": "Cloud Outage",
        "scenario_type": "cloud_outage",
        "business_process_id": risk_setup["bp1"].id
    }
    res = client.post(
        '/api/v1/risk-quantification/scenarios',
        json=payload,
        headers=risk_setup["headers"]
    )
    assert res.status_code == 201


def test_api_scenarios_missing_org(app, client, risk_setup):
    """Test 10: Missing org_id parameter triggers error."""
    res = client.get('/api/v1/risk-quantification/scenarios', headers=risk_setup["headers"])
    assert res.status_code == 400
