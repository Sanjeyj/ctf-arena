"""
Unit and Integration tests for Phase 31 — Platform Control Plane.
Contains 10 test cases covering PlatformService registry, status updates, dependencies tracking, and API endpoints.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.platform_service import PlatformService
from app.models.service_dependency import ServiceDependency
from app.services.platform_registry_service import PlatformRegistryService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def cp_setup(app):
    """Fixture for control plane tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(ServiceDependency).delete()
        db.session.query(PlatformService).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="CP Org", slug="cp-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="cp_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="CP Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "cp_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_platform_service_creation(app, cp_setup):
    """Test 1: PlatformService model fields."""
    with app.app_context():
        srv = PlatformService(
            service_name="SOC Ingest",
            service_type="soc",
            version="1.0.0",
            status="healthy",
            health_score=0.95,
            criticality="high",
            owner="Alice",
            organization_id=cp_setup["org"].id
        )
        db.session.add(srv)
        db.session.commit()
        assert srv.id is not None
        assert srv.service_name == "SOC Ingest"
        assert srv.health_score == 0.95


def test_platform_service_repr(app, cp_setup):
    """Test 2: PlatformService repr format."""
    with app.app_context():
        srv = PlatformService(service_name="LMS Auth", status="degraded", organization_id=cp_setup["org"].id)
        assert "LMS Auth" in repr(srv)
        assert "degraded" in repr(srv)


def test_platform_service_to_dict(app, cp_setup):
    """Test 3: PlatformService serialization."""
    with app.app_context():
        srv = PlatformService(
            service_name="Cloud Mesh",
            service_type="cloud",
            status="maintenance",
            health_score=0.5,
            criticality="critical",
            organization_id=cp_setup["org"].id
        )
        d = srv.to_dict()
        assert d["service_name"] == "Cloud Mesh"
        assert d["status"] == "maintenance"
        assert d["health_score"] == 0.5


def test_service_dependency_creation(app, cp_setup):
    """Test 4: ServiceDependency model fields."""
    with app.app_context():
        s1 = PlatformRegistryService.register_service("S1", "ai", cp_setup["org"].id)
        s2 = PlatformRegistryService.register_service("S2", "ai", cp_setup["org"].id)
        dep = ServiceDependency(
            source_service_id=s1.id,
            target_service_id=s2.id,
            dependency_type="ai",
            criticality="high",
            health_impact=0.4,
            status="active",
            organization_id=cp_setup["org"].id
        )
        db.session.add(dep)
        db.session.commit()
        assert dep.id is not None
        assert dep.dependency_type == "ai"
        assert dep.health_impact == 0.4


def test_service_dependency_repr(app, cp_setup):
    """Test 5: ServiceDependency repr format."""
    with app.app_context():
        dep = ServiceDependency(source_service_id=1, target_service_id=2, dependency_type="data", organization_id=cp_setup["org"].id)
        assert "1->2" in repr(dep)


def test_registry_service_register(app, cp_setup):
    """Test 6: Service registers capability node."""
    with app.app_context():
        srv = PlatformRegistryService.register_service("CTI Aggregator", "cti", cp_setup["org"].id, owner="Bob")
        assert srv.id is not None
        assert srv.service_name == "CTI Aggregator"
        assert srv.owner == "Bob"


def test_registry_service_update_health(app, cp_setup):
    """Test 7: Service health update updates scores."""
    with app.app_context():
        srv = PlatformRegistryService.register_service("SOC Core", "soc", cp_setup["org"].id)
        updated = PlatformRegistryService.update_health(srv.id, 0.45, "degraded", cp_setup["org"].id)
        assert updated.health_score == 0.45
        assert updated.status == "degraded"


def test_registry_service_heartbeat(app, cp_setup):
    """Test 8: Service heartbeat updates timestamp."""
    with app.app_context():
        srv = PlatformRegistryService.register_service("LMS Portal", "lms", cp_setup["org"].id)
        hb = PlatformRegistryService.heartbeat(srv.id, cp_setup["org"].id)
        assert hb.last_heartbeat is not None


def test_registry_service_list_summary(app, cp_setup):
    """Test 9: Service summary compiles health stats."""
    with app.app_context():
        PlatformRegistryService.register_service("S1", "soc", cp_setup["org"].id)
        s2 = PlatformRegistryService.register_service("S2", "cti", cp_setup["org"].id)
        PlatformRegistryService.update_health(s2.id, 0.5, "degraded", cp_setup["org"].id)

        summary = PlatformRegistryService.platform_summary(cp_setup["org"].id)
        assert summary["total_services"] == 2
        assert summary["overall_health"] == 0.75
        assert summary["degraded_count"] == 1


def test_api_get_services(client, cp_setup):
    """Test 10: GET /api/v1/control-plane/services REST endpoint."""
    with client.application.app_context():
        PlatformRegistryService.register_service("API service", "soc", cp_setup["org"].id)

    resp = client.get(
        f'/api/v1/control-plane/services?org_id={cp_setup["org"].id}',
        headers=cp_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) >= 1
    assert data[0]["service_name"] == "API service"
