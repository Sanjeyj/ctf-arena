"""
Unit and Integration tests for Phase 26 Autonomous Cyber Enterprise — Workflows.
Contains 10 test cases covering security workflows, triggers, and orchestration mesh logic.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.security_workflow import SecurityWorkflow
from app.models.autonomous_agent import AutonomousAgent
from app.models.agent_task import AgentTask
from app.services.orchestration_service import OrchestrationService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def workflow_setup(app):
    """Fixture for workflow orchestration tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(SecurityWorkflow).delete()
        db.session.query(AgentTask).delete()
        db.session.query(AutonomousAgent).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Workflow Org", slug="workflow-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="workflow_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Workflow Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "workflow_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_security_workflow_creation(app, workflow_setup):
    """Test 1: SecurityWorkflow model fields."""
    with app.app_context():
        wf = SecurityWorkflow(
            workflow_name="Auto Containment",
            trigger="on_incident",
            steps=json.dumps(["isolate_node", "notify_secops"]),
            status="active",
            organization_id=workflow_setup['org'].id
        )
        db.session.add(wf)
        db.session.commit()
        assert wf.workflow_name == "Auto Containment"
        assert wf.trigger == "on_incident"
        assert "Auto Containment" in repr(wf)


def test_security_workflow_to_dict(app, workflow_setup):
    """Test 2: SecurityWorkflow dict serialization."""
    with app.app_context():
        wf = SecurityWorkflow(
            workflow_name="Compliance Audit Checks",
            trigger="on_compliance_drift",
            organization_id=workflow_setup['org'].id
        )
        db.session.add(wf)
        db.session.commit()
        d = wf.to_dict()
        assert d['workflow_name'] == "Compliance Audit Checks"
        assert d['trigger'] == "on_compliance_drift"


def test_orchestration_service_run_workflow(app, workflow_setup):
    """Test 3: OrchestrationService.run_workflow creates a record."""
    with app.app_context():
        wf = OrchestrationService.run_workflow(
            workflow_name="Incident Response Playbook",
            trigger="on_incident",
            steps=["quarantine", "alert"],
            organization_id=workflow_setup['org'].id
        )
        assert wf.id is not None
        assert wf.workflow_name == "Incident Response Playbook"


def test_orchestration_service_trigger_agents_soc(app, workflow_setup):
    """Test 4: OrchestrationService.trigger_agents triggers SOC Agent."""
    with app.app_context():
        org_id = workflow_setup['org'].id
        agent = AutonomousAgent(name="SOC-AI", role="SOC Agent", organization_id=org_id)
        db.session.add(agent)
        db.session.commit()

        triggered = OrchestrationService.trigger_agents("on_incident", org_id)
        assert len(triggered) == 1
        assert "Auto-Triggered Response: on_incident" in triggered[0].task_type


def test_orchestration_service_trigger_agents_compliance(app, workflow_setup):
    """Test 5: OrchestrationService.trigger_agents triggers Compliance Agent."""
    with app.app_context():
        org_id = workflow_setup['org'].id
        agent = AutonomousAgent(name="Compliance-AI", role="Compliance Agent", organization_id=org_id)
        db.session.add(agent)
        db.session.commit()

        triggered = OrchestrationService.trigger_agents("on_compliance_drift", org_id)
        assert len(triggered) == 1
        assert "on_compliance_drift" in triggered[0].task_type


def test_orchestration_service_trigger_agents_cti(app, workflow_setup):
    """Test 6: OrchestrationService.trigger_agents triggers CTI Agent."""
    with app.app_context():
        org_id = workflow_setup['org'].id
        agent = AutonomousAgent(name="CTI-AI", role="CTI Agent", organization_id=org_id)
        db.session.add(agent)
        db.session.commit()

        triggered = OrchestrationService.trigger_agents("on_threat_intel", org_id)
        assert len(triggered) == 1
        assert "on_threat_intel" in triggered[0].task_type


def test_orchestration_service_coordinate_tasks(app, workflow_setup):
    """Test 7: OrchestrationService.coordinate_tasks reports status."""
    with app.app_context():
        wf = SecurityWorkflow(
            workflow_name="Drill 1",
            trigger="manual",
            steps=json.dumps(["step1"]),
            organization_id=workflow_setup['org'].id
        )
        db.session.add(wf)
        db.session.commit()

        report = OrchestrationService.coordinate_tasks(wf.id)
        assert report['name'] == "Drill 1"
        assert report['steps_count'] == 1
        assert report['orchestration_status'] == 'orchestrated_successfully'


def test_api_get_workflows(client, workflow_setup):
    """Test 8: GET /api/v1/workflows lists workflows."""
    resp = client.get(
        f'/api/v1/workflows?org_id={workflow_setup["org"].id}',
        headers=workflow_setup['headers']
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert isinstance(data, list)


def test_api_get_goals(client, workflow_setup):
    """Test 9: GET /api/v1/goals lists goals."""
    resp = client.get(
        f'/api/v1/goals?org_id={workflow_setup["org"].id}',
        headers=workflow_setup['headers']
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert isinstance(data, list)


def test_api_post_task_jwt(client, workflow_setup):
    """Test 10: POST /api/v1/tasks queues a task via API."""
    with client.application.app_context():
        agent = AutonomousAgent(name="SOC-Bot", role="SOC Agent", organization_id=workflow_setup['org'].id)
        db.session.add(agent)
        db.session.commit()
        agent_id = agent.id

    resp = client.post(
        '/api/v1/tasks',
        json={
            'agent_id': agent_id,
            'task_type': 'IP Ban',
            'priority': 'high',
            'organization_id': workflow_setup['org'].id
        },
        headers=workflow_setup['headers']
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data['agent_id'] == agent_id
    assert data['task_type'] == 'IP Ban'
