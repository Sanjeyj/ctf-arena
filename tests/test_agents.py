"""
Unit and Integration tests for Step 1 AI SOC Analyst.
"""
import pytest
import json
from app.extensions import db
from app.models.soc_agent import SocAgent
from app.models.alert import Alert
from app.models.organization import Organization
from app.services.soc_agent_service import SocAgentService
from app.research.routes import create_jwt

@pytest.fixture
def agent_setup(app):
    with app.app_context():
        # Clear tables
        db.session.query(SocAgent).delete()
        db.session.query(Alert).delete()
        db.session.commit()

        org = Organization(name="Agent Org", slug="agent-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        alert = Alert(
            title="Brute force attack detected on endpoints",
            severity="high",
            status="new",
            organization_id=org.id
        )
        db.session.add(alert)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "agent_admin"}, secret)

        yield {
            "org": org,
            "alert": alert,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }

def test_soc_agent_creation(app, agent_setup):
    """Test creating AI SocAgent configurations."""
    with app.app_context():
        org = agent_setup['org']
        agent = SocAgentService.create_agent(
            name="SOC_Analyst_Alpha", role="analyst", confidence=0.88, org_id=org.id
        )
        assert agent.id is not None
        assert agent.name == "SOC_Analyst_Alpha"
        assert agent.role == "analyst"

def test_alert_triage_simulation(app, agent_setup):
    """Test AI alert triage severity estimation and TTP mappings."""
    with app.app_context():
        org = agent_setup['org']
        alert = agent_setup['alert']
        agent = SocAgentService.create_agent("TriageAgent", org_id=org.id)

        triage = SocAgentService.run_alert_triage(agent.id, alert.id)
        assert triage['alert_id'] == alert.id
        assert triage['predicted_severity'] == "critical"
        assert len(triage['mitre_techniques']) >= 1

def test_agents_api_endpoints(client, agent_setup):
    """Test listing and registering AI SOC agents REST endpoints."""
    headers = agent_setup['headers']
    org = agent_setup['org']

    resp = client.get('/api/v1/agents', headers=headers)
    assert resp.status_code == 200
    assert json.loads(resp.data)['count'] == 0

    resp = client.post('/api/v1/agents', data=json.dumps({
        "name": "SOC_Analyst_Beta", "role": "threat_hunter", "confidence": 0.90, "org_id": org.id
    }), content_type='application/json', headers=headers)
    assert resp.status_code == 201

    resp = client.get('/api/v1/agents', headers=headers)
    assert resp.status_code == 200
    assert json.loads(resp.data)['count'] == 1


def test_soc_agent_list_empty(app):
    """Test listing agents returns empty list when none registered."""
    with app.app_context():
        res = SocAgentService.list_agents(org_id=999)
        assert len(res) == 0


def test_soc_agent_triage_missing_alert(app, agent_setup):
    """Test running triage on non-existent alert ID raises ValueError."""
    with app.app_context():
        org = agent_setup['org']
        agent = SocAgentService.create_agent("AgentMissingAlert", org_id=org.id)
        with pytest.raises(ValueError):
            SocAgentService.run_alert_triage(agent.id, 9999)


def test_soc_agent_triage_missing_agent(app, agent_setup):
    """Test running triage on non-existent agent ID raises ValueError."""
    with app.app_context():
        alert = agent_setup['alert']
        with pytest.raises(ValueError):
            SocAgentService.run_alert_triage(9999, alert.id)


def test_soc_agent_triage_custom_model(app, agent_setup):
    """Test creating agent stores model settings successfully."""
    with app.app_context():
        org = agent_setup['org']
        agent = SocAgentService.create_agent("AgentModel", model="custom-gpt", org_id=org.id)
        assert agent.model == "custom-gpt"


def test_ai_copilot_explain_alert(app, agent_setup):
    """Test AI SOC Copilot explains alert content correctly."""
    with app.app_context():
        from app.services.ai_soc_copilot import AISocCopilot
        alert = agent_setup['alert']
        explanation = AISocCopilot.explain_alert(alert.id)
        assert "Alert" in explanation
        assert alert.title in explanation


def test_ai_copilot_mitigation(app, agent_setup):
    """Test AI SOC Copilot mitigation recommendations output structure."""
    with app.app_context():
        from app.services.ai_soc_copilot import AISocCopilot
        alert = agent_setup['alert']
        mitigations = AISocCopilot.recommend_mitigation(alert.id)
        assert "Isolate" in mitigations
        assert "firewall" in mitigations

