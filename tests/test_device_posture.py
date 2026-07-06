"""
Unit and Integration tests for Device Posture.
Contains 10 test cases covering DevicePosture model, posture calculations, OS compliance status, and tenant boundary checks.
"""
import pytest
import json
import datetime
from app.extensions import db
from app.models.organization import Organization
from app.models.device_posture import DevicePosture
from app.services.device_posture_service import DevicePostureService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def dev_setup(app):
    """Fixture for device posture tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(DevicePosture).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="DOrg 1", slug="dorg-1", plan_type="enterprise")
        o2 = Organization(name="DOrg 2", slug="dorg-2", plan_type="enterprise")
        db.session.add_all([o1, o2])
        db.session.commit()

        try:
            UserRepository.create(
                username="dev_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Dev Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "dev_admin"}, secret)

        yield {
            "o1": o1,
            "o2": o2,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_device_posture_model_fields(app, dev_setup):
    """Test 1: DevicePosture model fields."""
    with app.app_context():
        dev = DevicePosture(
            device_name="Workstation-A",
            device_type="workstation",
            os_family="windows",
            patch_score=0.9,
            encryption_enabled=True,
            endpoint_protection_status="active",
            posture_score=95.0,
            compliance_status="compliant",
            organization_id=dev_setup["o1"].id
        )
        db.session.add(dev)
        db.session.commit()
        assert dev.id is not None
        assert dev.device_name == "Workstation-A"
        assert dev.encryption_enabled is True


def test_device_posture_repr(app, dev_setup):
    """Test 2: DevicePosture repr format."""
    with app.app_context():
        dev = DevicePosture(device_name="Mobile-1", posture_score=80.0, organization_id=dev_setup["o1"].id)
        assert "Mobile-1" in repr(dev)
        assert "80.0" in repr(dev)


def test_device_posture_to_dict(app, dev_setup):
    """Test 3: DevicePosture serialization."""
    with app.app_context():
        now = datetime.datetime.utcnow()
        dev = DevicePosture(
            device_name="Server-X",
            device_type="server",
            os_family="linux",
            patch_score=0.85,
            encryption_enabled=False,
            endpoint_protection_status="inactive",
            posture_score=40.0,
            compliance_status="non_compliant",
            last_assessed_at=now,
            organization_id=dev_setup["o1"].id
        )
        d = dev.to_dict()
        assert d["device_name"] == "Server-X"
        assert d["os_family"] == "linux"
        assert d["last_assessed_at"] == now.isoformat()


def test_register_device_service(app, dev_setup):
    """Test 4: Service registers simulated device, calculating posture score."""
    with app.app_context():
        dev = DevicePostureService.register_device("Laptop-B", "laptop", "macos", dev_setup["o1"].id, 1.0, True, "active")
        assert dev.id is not None
        assert dev.posture_score == 100.0
        assert dev.compliance_status == "compliant"


def test_calculate_posture_scores(app, dev_setup):
    """Test 5: Posture math correctly accounts for patch scores and encryption."""
    with app.app_context():
        # patch_score=0.8 -> 40 points. encryption=False -> 0 points. active protection -> no penalty.
        # Score = 40 + 0 = 40.0
        d1 = DevicePostureService.register_device("Dev1", "laptop", "windows", dev_setup["o1"].id, 0.8, False, "active")
        assert d1.posture_score == 40.0
        assert d1.compliance_status == "restricted"


def test_calculate_posture_endpoint_penalties(app, dev_setup):
    """Test 6: Posture score applies penalty for inactive or missing protection."""
    with app.app_context():
        # encryption=True -> 50. patch=1.0 -> 50. inactive protection -> -30. Score = 70.0
        d1 = DevicePostureService.register_device("Dev2", "laptop", "windows", dev_setup["o1"].id, 1.0, True, "inactive")
        assert d1.posture_score == 70.0

        # missing protection -> -50. Score = 50.0
        d2 = DevicePostureService.register_device("Dev3", "laptop", "windows", dev_setup["o1"].id, 1.0, True, "not_installed")
        assert d2.posture_score == 50.0


def test_device_compliance_assess(app, dev_setup):
    """Test 7: Assess function updates assessment timestamp and recalculates score."""
    with app.app_context():
        dev = DevicePostureService.register_device("Dev4", "mobile", "ios", dev_setup["o1"].id)
        assert dev.last_assessed_at is None
        
        assessed = DevicePostureService.assess(dev.id, dev_setup["o1"].id)
        assert assessed.last_assessed_at is not None


def test_device_posture_explain(app, dev_setup):
    """Test 8: Explain posture diagnostic details."""
    with app.app_context():
        dev = DevicePostureService.register_device("Dev5", "laptop", "linux", dev_setup["o1"].id, 0.5, False, "inactive")
        explanation = DevicePostureService.explain_posture(dev.id, dev_setup["o1"].id)
        assert "encryption is disabled" in explanation
        assert "patches are severely outdated" in explanation


def test_device_posture_tenant_isolation(app, dev_setup):
    """Test 9: Assess checks organization ownership boundary."""
    with app.app_context():
        dev = DevicePostureService.register_device("Dev6", "laptop", "linux", dev_setup["o1"].id)
        # Assess from Tenant 2 should fail (return None)
        assert DevicePostureService.assess(dev.id, dev_setup["o2"].id) is None


def test_api_get_devices(client, dev_setup):
    """Test 10: GET /api/v1/assurance/devices REST endpoint."""
    with client.application.app_context():
        DevicePostureService.register_device("API-Laptop", "laptop", "windows", dev_setup["o1"].id)

    resp = client.get(
        f'/api/v1/assurance/devices?org_id={dev_setup["o1"].id}',
        headers=dev_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) >= 1
    assert data[0]["device_name"] == "API-Laptop"
