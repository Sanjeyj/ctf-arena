"""
Unit and Integration tests for Phase 27 Global Security Intelligence Network — Observatory.
Contains 10 test cases covering observatory nodes, monitoring services, alerts, and APIs.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.observatory_node import ObservatoryNode
from app.services.observatory_service import ObservatoryService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def obs_setup(app):
    """Fixture for observatory tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(ObservatoryNode).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Obs Org", slug="obs-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="obs_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Obs Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "obs_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_observatory_node_creation(app, obs_setup):
    """Test 1: ObservatoryNode model fields."""
    with app.app_context():
        node = ObservatoryNode(
            region="us-east",
            node_type="threat",
            status="online",
            health=0.95,
            organization_id=obs_setup["org"].id
        )
        db.session.add(node)
        db.session.commit()
        assert node.id is not None
        assert node.region == "us-east"
        assert node.node_type == "threat"
        assert node.health == 0.95


def test_observatory_node_to_dict(app, obs_setup):
    """Test 2: ObservatoryNode serialization."""
    with app.app_context():
        node = ObservatoryNode(
            region="eu-west",
            node_type="resilience",
            status="degraded",
            health=0.6,
            organization_id=obs_setup["org"].id
        )
        db.session.add(node)
        db.session.commit()
        d = node.to_dict()
        assert d["region"] == "eu-west"
        assert d["node_type"] == "resilience"
        assert d["health"] == 0.6


def test_observatory_service_monitor(app, obs_setup):
    """Test 3: Monitor returns health status list."""
    with app.app_context():
        n1 = ObservatoryNode(region="asia-south", node_type="compliance", status="online", health=0.98, organization_id=obs_setup["org"].id)
        n2 = ObservatoryNode(region="us-east", node_type="threat", status="offline", health=0.1, organization_id=obs_setup["org"].id)
        db.session.add_all([n1, n2])
        db.session.commit()

        status_list = ObservatoryService.monitor(org_id=obs_setup["org"].id)
        assert len(status_list) == 2
        assert status_list[0]["region"] == "asia-south"
        assert status_list[1]["status"] == "offline"


def test_observatory_service_aggregate_empty(app):
    """Test 4: Aggregation with no registered nodes."""
    with app.app_context():
        res = ObservatoryService.aggregate("private-cloud")
        assert res["node_count"] == 0
        assert res["avg_health"] is None
        assert res["status"] == "no_data"


def test_observatory_service_aggregate_with_nodes(app, obs_setup):
    """Test 5: Aggregation average health scoring."""
    with app.app_context():
        n1 = ObservatoryNode(region="eu-west", node_type="threat", status="online", health=0.8, organization_id=obs_setup["org"].id)
        n2 = ObservatoryNode(region="eu-west", node_type="compliance", status="online", health=0.9, organization_id=obs_setup["org"].id)
        db.session.add_all([n1, n2])
        db.session.commit()

        res = ObservatoryService.aggregate("eu-west")
        assert res["node_count"] == 2
        assert res["avg_health"] == 0.85
        assert res["status"] == "healthy"


def test_observatory_service_alert_no_trigger(app, obs_setup):
    """Test 6: Node status passes health checks, no alert."""
    with app.app_context():
        node = ObservatoryNode(region="us-east", node_type="threat", status="online", health=0.9, organization_id=obs_setup["org"].id)
        db.session.add(node)
        db.session.commit()

        res = ObservatoryService.alert(node.id)
        assert res["alert"] is False
        assert res["status"] == "online"


def test_observatory_service_alert_trigger(app, obs_setup):
    """Test 7: Node health below threshold triggers alert and status change."""
    with app.app_context():
        node = ObservatoryNode(region="us-east", node_type="threat", status="online", health=0.4, organization_id=obs_setup["org"].id)
        db.session.add(node)
        db.session.commit()

        res = ObservatoryService.alert(node.id)
        assert res["alert"] is True
        assert res["status"] == "degraded"


def test_observatory_service_alert_not_found(app):
    """Test 8: Alert checking non-existent node ID."""
    with app.app_context():
        res = ObservatoryService.alert(99999)
        assert res["alert"] is False
        assert "not found" in res["reason"]


def test_api_get_observatory(client, obs_setup):
    """Test 9: GET /api/v1/observatory endpoint."""
    with client.application.app_context():
        node = ObservatoryNode(
            region="global-mesh",
            node_type="enterprise",
            status="online",
            health=0.99,
            organization_id=obs_setup["org"].id
        )
        db.session.add(node)
        db.session.commit()

    resp = client.get(
        f'/api/v1/observatory?org_id={obs_setup["org"].id}',
        headers=obs_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) >= 1
    assert data[0]["region"] == "global-mesh"


def test_observatory_custom_threshold_alert(app, obs_setup):
    """Test 10: Alert checking with a customized trigger threshold."""
    with app.app_context():
        node = ObservatoryNode(region="us-east", node_type="resilience", status="online", health=0.65, organization_id=obs_setup["org"].id)
        db.session.add(node)
        db.session.commit()

        # Healthy under default (0.5), degraded under custom 0.7 threshold
        res1 = ObservatoryService.alert(node.id, threshold=0.5)
        assert res1["alert"] is False

        res2 = ObservatoryService.alert(node.id, threshold=0.7)
        assert res2["alert"] is True
