"""
Unit and Integration tests for Step 5 Playbook Engine.
"""
import pytest
import json
from app.extensions import db
from app.models.playbook import Playbook
from app.models.playbook_execution import PlaybookExecution
from app.models.alert import Alert
from app.models.organization import Organization
from app.services.playbook_engine_service import PlaybookEngineService
from app.research.routes import create_jwt

@pytest.fixture
def playbook_setup(app):
    with app.app_context():
        # Clear tables
        db.session.query(PlaybookExecution).delete()
        db.session.query(Playbook).delete()
        db.session.query(Alert).delete()
        db.session.commit()

        org = Organization(name="Playbook Org", slug="playbook-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        alert = Alert(title="Suspicious activity alert", severity="medium", status="new", organization_id=org.id)
        db.session.add(alert)
        db.session.commit()

        playbook = PlaybookEngineService.create_playbook(
            name="Host Isolation Playbook",
            description="Isolate target host on detection triggers",
            trigger_type="alert_severity",
            steps=["investigate", "contain", "close"],
            org_id=org.id
        )

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "playbook_admin"}, secret)

        yield {
            "org": org,
            "alert": alert,
            "playbook": playbook,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }

def test_playbook_creation(app, playbook_setup):
    """Test playbook model configurations."""
    with app.app_context():
        org = playbook_setup['org']
        p = db.session.get(Playbook, playbook_setup['playbook'].id)
        assert p.name == "Host Isolation Playbook"
        assert p.trigger_type == "alert_severity"

def test_playbook_execution_flow(app, playbook_setup):
    """Test simulated playbook runs logging steps details."""
    with app.app_context():
        org = playbook_setup['org']
        alert = playbook_setup['alert']
        playbook = playbook_setup['playbook']

        execution = PlaybookEngineService.execute_playbook(playbook.id, alert.id, org_id=org.id)
        assert execution.id is not None
        assert execution.status == "completed"
        assert "Executed action: contain" in execution.logs
        assert execution.current_step == 3

def test_playbooks_api_endpoints(client, playbook_setup):
    """Test REST API trigger routes for playbooks."""
    headers = playbook_setup['headers']
    playbook = playbook_setup['playbook']
    alert = playbook_setup['alert']
    org = playbook_setup['org']

    # 1. Fetch playbooks
    resp = client.get('/api/v1/playbooks', headers=headers)
    assert resp.status_code == 200
    assert json.loads(resp.data)['count'] == 1

    resp = client.post('/api/v1/playbooks', data=json.dumps({
        "playbook_id": playbook.id,
        "alert_id": alert.id,
        "org_id": org.id
    }), content_type='application/json', headers=headers)
    assert resp.status_code == 201
    assert json.loads(resp.data)['execution']['status'] == "completed"


def test_playbook_list_empty(app):
    """Test retrieving playbooks returns empty list for invalid org."""
    with app.app_context():
        res = Playbook.query.filter_by(organization_id=9999).all()
        assert len(res) == 0


def test_playbook_trigger_missing(client, playbook_setup):
    """Test triggering non-existent playbook ID returns 404 error."""
    headers = playbook_setup['headers']
    resp = client.post('/api/v1/playbooks', data=json.dumps({
        "playbook_id": 9999
    }), content_type='application/json', headers=headers)
    assert resp.status_code == 404


def test_playbook_trigger_unauthorized(client, playbook_setup):
    """Test triggering playbook fails without Bearer token header."""
    playbook = playbook_setup['playbook']
    resp = client.post('/api/v1/playbooks', data=json.dumps({
        "playbook_id": playbook.id
    }), content_type='application/json')
    assert resp.status_code == 401


def test_playbook_engine_steps_serialization(app, playbook_setup):
    """Test steps serialization matches JSON list decoding."""
    with app.app_context():
        p = db.session.get(Playbook, playbook_setup['playbook'].id)
        steps = json.loads(p.steps_json)
        assert len(steps) == 3
        assert steps[1] == "contain"

