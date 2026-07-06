"""
Unit and Integration tests for Phase 29 Global Cyber Command Center — Command.
Contains 15 test cases covering CommandCenter & CommandMetric models, CommandService, ExecutiveCommandAI, and API endpoints.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.command_center import CommandCenter
from app.models.command_metric import CommandMetric
from app.services.command_service import CommandService
from app.services.executive_command_ai import ExecutiveCommandAI
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def cmd_setup(app):
    """Fixture for command tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(CommandCenter).delete()
        db.session.query(CommandMetric).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Command Org", slug="cmd-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="cmd_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Cmd Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "cmd_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_command_center_creation(app, cmd_setup):
    """Test 1: CommandCenter model fields."""
    with app.app_context():
        center = CommandCenter(
            region="Americas",
            commander="Gen. Shepherd",
            readiness=0.85,
            status="operational",
            organization_id=cmd_setup["org"].id
        )
        db.session.add(center)
        db.session.commit()
        assert center.id is not None
        assert center.region == "Americas"
        assert center.commander == "Gen. Shepherd"
        assert center.readiness == 0.85
        assert center.status == "operational"


def test_command_center_repr(app, cmd_setup):
    """Test 2: CommandCenter __repr__ implementation."""
    with app.app_context():
        center = CommandCenter(
            region="APAC",
            commander="Gen. Wong",
            organization_id=cmd_setup["org"].id
        )
        assert "APAC" in repr(center)
        assert "Gen. Wong" in repr(center)


def test_command_center_to_dict(app, cmd_setup):
    """Test 3: CommandCenter serialization."""
    with app.app_context():
        center = CommandCenter(
            region="EMEA",
            commander="Gen. Schmidt",
            readiness=0.9,
            status="degraded",
            organization_id=cmd_setup["org"].id
        )
        d = center.to_dict()
        assert d["region"] == "EMEA"
        assert d["commander"] == "Gen. Schmidt"
        assert d["readiness"] == 0.9
        assert d["status"] == "degraded"


def test_command_metric_creation(app, cmd_setup):
    """Test 4: CommandMetric model fields."""
    with app.app_context():
        metric = CommandMetric(
            response_score=0.75,
            resilience_score=0.8,
            readiness_score=0.85,
            intelligence_score=0.9,
            organization_id=cmd_setup["org"].id
        )
        db.session.add(metric)
        db.session.commit()
        assert metric.id is not None
        assert metric.response_score == 0.75
        assert metric.resilience_score == 0.8
        assert metric.readiness_score == 0.85
        assert metric.intelligence_score == 0.9


def test_command_metric_repr(app, cmd_setup):
    """Test 5: CommandMetric __repr__ implementation."""
    with app.app_context():
        metric = CommandMetric(
            response_score=0.88,
            resilience_score=0.91,
            organization_id=cmd_setup["org"].id
        )
        assert "0.88" in repr(metric)
        assert "0.91" in repr(metric)


def test_command_metric_to_dict(app, cmd_setup):
    """Test 6: CommandMetric serialization."""
    with app.app_context():
        metric = CommandMetric(
            response_score=0.65,
            resilience_score=0.7,
            readiness_score=0.75,
            intelligence_score=0.8,
            organization_id=cmd_setup["org"].id
        )
        d = metric.to_dict()
        assert d["response_score"] == 0.65
        assert d["resilience_score"] == 0.7
        assert d["readiness_score"] == 0.75
        assert d["intelligence_score"] == 0.8


def test_command_service_activate_valid(app, cmd_setup):
    """Test 7: Activate sets center status to operational and readiness to 1.0."""
    with app.app_context():
        center = CommandCenter(
            region="LATAM",
            commander="Gen. Diaz",
            readiness=0.4,
            status="degraded",
            organization_id=cmd_setup["org"].id
        )
        db.session.add(center)
        db.session.commit()

        activated = CommandService.activate(center.id)
        assert activated.status == "operational"
        assert activated.readiness == 1.0


def test_command_service_activate_not_found(app):
    """Test 8: Activate returns None for non-existent center ID."""
    with app.app_context():
        assert CommandService.activate(99999) is None


def test_command_service_coordinate_empty(app, cmd_setup):
    """Test 9: Coordinate returns no centers summary for empty org."""
    with app.app_context():
        res = CommandService.coordinate(cmd_setup["org"].id)
        assert res["centers"] == 0
        assert res["avg_readiness"] == 0.0
        assert res["coordination"] == "no_centers"


def test_command_service_coordinate_optimal(app, cmd_setup):
    """Test 10: Coordinate evaluates optimal status for high readiness centers."""
    with app.app_context():
        c1 = CommandCenter(region="R1", commander="C1", readiness=0.85, organization_id=cmd_setup["org"].id)
        c2 = CommandCenter(region="R2", commander="C2", readiness=0.95, organization_id=cmd_setup["org"].id)
        db.session.add_all([c1, c2])
        db.session.commit()

        res = CommandService.coordinate(cmd_setup["org"].id)
        assert res["centers"] == 2
        assert res["avg_readiness"] == 0.9
        assert res["coordination"] == "optimal"


def test_command_service_coordinate_degraded_critical(app, cmd_setup):
    """Test 11: Coordinate evaluates degraded and critical statuses properly."""
    with app.app_context():
        c1 = CommandCenter(region="R1", commander="C1", readiness=0.6, organization_id=cmd_setup["org"].id)
        c2 = CommandCenter(region="R2", commander="C2", readiness=0.4, organization_id=cmd_setup["org"].id)
        db.session.add_all([c1, c2])
        db.session.commit()

        # Avg = 0.5 -> degraded
        res1 = CommandService.coordinate(cmd_setup["org"].id)
        assert res1["coordination"] == "degraded"

        c1.readiness = 0.3
        c2.readiness = 0.2
        db.session.commit()

        # Avg = 0.25 -> critical
        res2 = CommandService.coordinate(cmd_setup["org"].id)
        assert res2["coordination"] == "critical"


def test_command_service_monitor_create_default(app, cmd_setup):
    """Test 12: Monitor initializes default metrics if none exist."""
    with app.app_context():
        metric = CommandService.monitor(cmd_setup["org"].id)
        assert metric.id is not None
        assert metric.response_score == 0.6
        assert metric.resilience_score == 0.65


def test_command_service_monitor_existing(app, cmd_setup):
    """Test 13: Monitor returns existing metrics if they exist."""
    with app.app_context():
        existing = CommandMetric(
            response_score=0.9,
            resilience_score=0.9,
            readiness_score=0.9,
            intelligence_score=0.9,
            organization_id=cmd_setup["org"].id
        )
        db.session.add(existing)
        db.session.commit()

        metric = CommandService.monitor(cmd_setup["org"].id)
        assert metric.id == existing.id
        assert metric.response_score == 0.9


def test_executive_command_ai_summarize_advise(app, cmd_setup):
    """Test 14: ExecutiveCommandAI summarize outputs valid command summaries and advice."""
    with app.app_context():
        sum1 = ExecutiveCommandAI.summarize(cmd_setup["org"].id)
        assert "No command metrics" in sum1

        metric = CommandMetric(
            response_score=0.95,
            resilience_score=0.92,
            readiness_score=0.94,
            intelligence_score=0.91,
            organization_id=cmd_setup["org"].id
        )
        db.session.add(metric)
        db.session.commit()

        sum2 = ExecutiveCommandAI.summarize(cmd_setup["org"].id)
        assert "OPTIMAL" in sum2

        # Test advice
        adv = ExecutiveCommandAI.advise("operations")
        assert "Operations directive" in adv
        adv_unknown = ExecutiveCommandAI.advise("unknown")
        assert "unknown" in adv_unknown


def test_api_get_command(client, cmd_setup):
    """Test 15: GET /api/v1/command REST endpoint."""
    with client.application.app_context():
        center = CommandCenter(
            region="API Region",
            commander="Gen. API",
            organization_id=cmd_setup["org"].id
        )
        db.session.add(center)
        db.session.commit()

    resp = client.get(
        f'/api/v1/command?org_id={cmd_setup["org"].id}',
        headers=cmd_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) >= 1
    assert data[0]["region"] == "API Region"
