"""
Unit and Integration tests for Phase 31 — Reliability Engineering.
Contains 10 test cases covering ReliabilityObjective model verification, SLIs/SLOs evaluation, budget calculations, and divisions by zero clamping.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.platform_service import PlatformService
from app.models.reliability_objective import ReliabilityObjective
from app.services.platform_registry_service import PlatformRegistryService
from app.services.reliability_service import ReliabilityService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def re_setup(app):
    """Fixture for reliability engineering tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(ReliabilityObjective).delete()
        db.session.query(PlatformService).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="RE Org", slug="re-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        srv = PlatformRegistryService.register_service("RE Service", "soc", org.id)

        try:
            UserRepository.create(
                username="re_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="RE Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "re_admin"}, secret)

        yield {
            "org": org,
            "srv": srv,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_reliability_objective_creation(app, re_setup):
    """Test 1: ReliabilityObjective model fields."""
    with app.app_context():
        obj = ReliabilityObjective(
            service_id=re_setup["srv"].id,
            metric_name="availability",
            target_value=0.99,
            current_value=0.995,
            measurement_window="30d",
            error_budget=0.5,
            status="compliant",
            organization_id=re_setup["org"].id
        )
        db.session.add(obj)
        db.session.commit()
        assert obj.id is not None
        assert obj.metric_name == "availability"
        assert obj.target_value == 0.99


def test_reliability_objective_repr(app, re_setup):
    """Test 2: ReliabilityObjective repr format."""
    with app.app_context():
        obj = ReliabilityObjective(metric_name="latency", status="breaching", organization_id=re_setup["org"].id)
        assert "latency" in repr(obj)
        assert "breaching" in repr(obj)


def test_reliability_objective_to_dict(app, re_setup):
    """Test 3: ReliabilityObjective serialization."""
    with app.app_context():
        obj = ReliabilityObjective(
            service_id=re_setup["srv"].id,
            metric_name="success_rate",
            target_value=0.95,
            current_value=0.94,
            error_budget=0.0,
            status="breaching",
            organization_id=re_setup["org"].id
        )
        d = obj.to_dict()
        assert d["metric_name"] == "success_rate"
        assert d["target_value"] == 0.95
        assert d["status"] == "breaching"


def test_reliability_service_create(app, re_setup):
    """Test 4: Service creates objective successfully."""
    with app.app_context():
        obj = ReliabilityService.create_objective(re_setup["srv"].id, "ingestion_success", 0.999, re_setup["org"].id)
        assert obj.id is not None
        assert obj.metric_name == "ingestion_success"
        assert obj.target_value == 0.999


def test_reliability_service_evaluate_compliant(app, re_setup):
    """Test 5: Evaluate compliant objective calculates budget correctly."""
    with app.app_context():
        # Target SLO = 0.90. Current = 0.95.
        # Error budget: (0.95 - 0.90)/(1.0 - 0.90) = 0.05/0.10 = 50%
        obj = ReliabilityService.create_objective(re_setup["srv"].id, "availability", 0.90, re_setup["org"].id)
        evaluated = ReliabilityService.evaluate_objective(obj.id, 0.95, re_setup["org"].id)
        assert evaluated.status == "compliant"
        assert evaluated.error_budget == 0.50


def test_reliability_service_evaluate_breaching(app, re_setup):
    """Test 6: Evaluate breaching objective marks status breaching."""
    with app.app_context():
        obj = ReliabilityService.create_objective(re_setup["srv"].id, "availability", 0.99, re_setup["org"].id)
        evaluated = ReliabilityService.evaluate_objective(obj.id, 0.98, re_setup["org"].id)
        assert evaluated.status == "breaching"
        assert evaluated.error_budget == 0.0  # Clamped to 0.0 since it is breaching


def test_reliability_service_division_by_zero_handling(app, re_setup):
    """Test 7: Division by zero SLO edge cases handles gracefully."""
    with app.app_context():
        # Target SLO = 1.0. Denominator = 1.0 - 1.0 = 0.
        obj = ReliabilityService.create_objective(re_setup["srv"].id, "availability", 1.0, re_setup["org"].id)
        
        # Current = 1.0 -> budget is 1.0
        ev1 = ReliabilityService.evaluate_objective(obj.id, 1.0, re_setup["org"].id)
        assert ev1.error_budget == 1.0
        
        # Current = 0.99 -> budget is 0.0
        ev2 = ReliabilityService.evaluate_objective(obj.id, 0.99, re_setup["org"].id)
        assert ev2.error_budget == 0.0


def test_reliability_service_detect_breach(app, re_setup):
    """Test 8: Breach detection finds all breaching targets."""
    with app.app_context():
        o1 = ReliabilityService.create_objective(re_setup["srv"].id, "metric1", 0.95, re_setup["org"].id)
        o2 = ReliabilityService.create_objective(re_setup["srv"].id, "metric2", 0.99, re_setup["org"].id)
        
        ReliabilityService.evaluate_objective(o1.id, 0.90, re_setup["org"].id)  # Breaches
        ReliabilityService.evaluate_objective(o2.id, 0.995, re_setup["org"].id) # Compliant

        breaches = ReliabilityService.detect_breach(re_setup["org"].id)
        assert len(breaches) == 1
        assert breaches[0].id == o1.id


def test_reliability_service_summary(app, re_setup):
    """Test 9: Summary lists statistics correctly."""
    with app.app_context():
        o1 = ReliabilityService.create_objective(re_setup["srv"].id, "metric1", 0.90, re_setup["org"].id)
        o2 = ReliabilityService.create_objective(re_setup["srv"].id, "metric2", 0.90, re_setup["org"].id)
        
        # Budget = 0.5
        ReliabilityService.evaluate_objective(o1.id, 0.95, re_setup["org"].id)
        # Budget = 0.0 (breaching)
        ReliabilityService.evaluate_objective(o2.id, 0.85, re_setup["org"].id)

        res = ReliabilityService.reliability_summary(re_setup["org"].id)
        assert res["total_objectives"] == 2
        assert res["breach_count"] == 1
        assert res["avg_budget"] == 0.25


def test_api_get_reliability(client, re_setup):
    """Test 10: GET /api/v1/control-plane/reliability REST endpoint."""
    with client.application.app_context():
        ReliabilityService.create_objective(re_setup["srv"].id, "API Metric", 0.99, re_setup["org"].id)

    resp = client.get(
        f'/api/v1/control-plane/reliability?org_id={re_setup["org"].id}',
        headers=re_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) >= 1
    assert data[0]["metric_name"] == "API Metric"
