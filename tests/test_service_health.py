"""
Unit and Integration tests for HealthService.
Contains 10 test cases covering health snapshots, Golden Signals formulas, classifications, dependency cascading, and hooks.
"""
import pytest
import datetime
from app.extensions import db
from app.models.organization import Organization
from app.models.platform_service import PlatformService
from app.models.service_dependency import ServiceDependency
from app.models.service_health_snapshot import ServiceHealthSnapshot
from app.services.health_service import HealthService
from app.services.hook_service import HookService
from app.research.routes import create_jwt


@pytest.fixture
def health_setup(app):
    """Fixture for health service tests."""
    with app.app_context():
        db.session.query(ServiceHealthSnapshot).delete()
        db.session.query(ServiceDependency).delete()
        db.session.query(PlatformService).delete()
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
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_health_snapshot_model(app, health_setup):
    """Test 1: ServiceHealthSnapshot model instantiation and validation."""
    with app.app_context():
        srv = PlatformService(
            service_name="lms",
            service_type="lms",
            organization_id=health_setup["o1"].id
        )
        db.session.add(srv)
        db.session.commit()

        snapshot = ServiceHealthSnapshot(
            platform_service_id=srv.id,
            health_score=95.0,
            availability=0.99,
            latency_ms=120.0,
            error_rate=0.01,
            saturation=0.25,
            status="healthy",
            measured_at=datetime.datetime.utcnow(),
            organization_id=health_setup["o1"].id
        )
        db.session.add(snapshot)
        db.session.commit()
        assert snapshot.id is not None
        assert snapshot.health_score == 95.0


def test_record_snapshot(app, health_setup):
    """Test 2: HealthService.record_snapshot creates record and updates PlatformService."""
    with app.app_context():
        srv = PlatformService(
            service_name="soc",
            service_type="soc",
            organization_id=health_setup["o1"].id
        )
        db.session.add(srv)
        db.session.commit()

        snapshot = HealthService.record_snapshot(srv.id, 1.0, 50.0, 0.0, 0.1, health_setup["o1"].id)
        assert snapshot.id is not None
        assert snapshot.health_score == 99.0  # 100 - (0.1 * 10) = 99.0
        assert snapshot.status == "healthy"

        # PlatformService cache update check
        db.session.refresh(srv)
        assert srv.status == "healthy"
        assert srv.health_score == 0.99


def test_calculate_health_perfect(app, health_setup):
    """Test 3: HealthService.calculate_health perfect score."""
    score = HealthService.calculate_health(availability=1.0, latency_ms=100.0, error_rate=0.0, saturation=0.0)
    assert score == 100.0


def test_calculate_health_latency_penalty(app, health_setup):
    """Test 4: HealthService.calculate_health latency degradation."""
    score = HealthService.calculate_health(availability=1.0, latency_ms=450.0, error_rate=0.0, saturation=0.0)
    # latency > 200: (450 - 200) / 50 = 5.0 penalty -> 95.0 health
    assert score == 95.0


def test_calculate_health_multiple_degradations(app, health_setup):
    """Test 5: HealthService.calculate_health combined signals penalty."""
    score = HealthService.calculate_health(availability=0.95, latency_ms=300.0, error_rate=0.10, saturation=0.80)
    # availability: 100 - (1 - 0.95)*50 = 97.5
    # latency > 200: (300-200)/50 = 2.0 penalty -> 95.5
    # error_rate: 0.10 * 30 = 3.0 penalty -> 92.5
    # saturation: 0.80 * 10 = 8.0 penalty -> 84.5
    assert score == 84.5


def test_classify_health(app, health_setup):
    """Test 6: HealthService.classify_health boundaries."""
    assert HealthService.classify_health(92.5) == "healthy"
    assert HealthService.classify_health(82.0) == "warning"
    assert HealthService.classify_health(65.0) == "degraded"
    assert HealthService.classify_health(30.0) == "critical"


def test_dependency_health(app, health_setup):
    """Test 7: HealthService.dependency_health evaluates dependency health classification states."""
    with app.app_context():
        s1 = PlatformService(service_name="s1", service_type="soc", health_score=1.0, status="healthy", organization_id=health_setup["o1"].id)
        s2 = PlatformService(service_name="s2", service_type="db", health_score=0.4, status="unavailable", organization_id=health_setup["o1"].id)
        db.session.add_all([s1, s2])
        db.session.commit()

        dep = ServiceDependency(source_service_id=s1.id, target_service_id=s2.id, dependency_type="hard", criticality="high", organization_id=health_setup["o1"].id)
        db.session.add(dep)
        db.session.commit()

        deps_status = HealthService.dependency_health(s1.id, health_setup["o1"].id)
        assert len(deps_status["critical"]) == 1
        assert deps_status["critical"][0]["service_name"] == "s2"


def test_health_history(app, health_setup):
    """Test 8: HealthService.health_history query bounds."""
    with app.app_context():
        srv = PlatformService(service_name="s1", service_type="soc", organization_id=health_setup["o1"].id)
        db.session.add(srv)
        db.session.commit()

        for _ in range(5):
            HealthService.record_snapshot(srv.id, 1.0, 50.0, 0.0, 0.0, health_setup["o1"].id)

        history = HealthService.health_history(srv.id, 3, health_setup["o1"].id)
        assert len(history) == 3


def test_health_summary(app, health_setup):
    """Test 9: HealthService.health_summary aggregate calculation."""
    with app.app_context():
        s1 = PlatformService(service_name="s1", service_type="soc", health_score=0.98, status="healthy", organization_id=health_setup["o1"].id)
        s2 = PlatformService(service_name="s2", service_type="db", health_score=0.82, status="warning", organization_id=health_setup["o1"].id)
        db.session.add_all([s1, s2])
        db.session.commit()

        summary = HealthService.health_summary(health_setup["o1"].id)
        assert summary["total_services"] == 2
        assert summary["healthy_count"] == 1
        assert summary["warning_count"] == 1
        assert summary["avg_score"] == 90.0


def test_health_hook_mutation(app, health_setup):
    """Test 10: HealthService evaluates with parameter mutation in before_health_evaluation hook."""
    with app.app_context():
        HookService.clear_all()
        def callback(platform_service_id, availability, latency_ms, error_rate, saturation, org_id):
            return {'availability': 0.5}  # Force half availability

        HookService.register_hook('before_health_evaluation', callback)
        srv = PlatformService(service_name="s1", service_type="soc", organization_id=health_setup["o1"].id)
        db.session.add(srv)
        db.session.commit()

        snapshot = HealthService.record_snapshot(srv.id, 1.0, 100.0, 0.0, 0.0, health_setup["o1"].id)
        # availability 0.5 -> score starts at 100 - (1 - 0.5)*50 = 75.0
        assert snapshot.health_score == 75.0
        HookService.clear_all()
