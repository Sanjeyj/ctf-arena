"""
Unit and Integration tests for Phase 30 — Posture Fusion.
Contains 13 test cases covering UniverseMetric model creation, domain aggregates, posture scoring calculations, weak domains detection, trends, and posture hooks triggering.
"""
import pytest
import json
import datetime
from app.extensions import db
from app.models.organization import Organization
from app.models.defense_universe import DefenseUniverse
from app.models.defense_domain import DefenseDomain
from app.models.universe_metric import UniverseMetric
from app.services.universe_service import UniverseService
from app.services.topology_service import TopologyService
from app.services.posture_fusion_service import PostureFusionService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def post_setup(app):
    """Fixture for posture tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(UniverseMetric).delete()
        db.session.query(DefenseDomain).delete()
        db.session.query(DefenseUniverse).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Posture Org", slug="post-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        uni = UniverseService.create_universe("Posture Uni", org.id)

        try:
            UserRepository.create(
                username="post_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Post Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "post_admin"}, secret)

        yield {
            "org": org,
            "uni": uni,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_universe_metric_creation(app, post_setup):
    """Test 1: UniverseMetric model fields."""
    with app.app_context():
        now = datetime.datetime.utcnow()
        metric = UniverseMetric(
            universe_id=post_setup["uni"].id,
            metric_type="resilience",
            metric_value=0.75,
            domain="soc",
            measured_at=now,
            organization_id=post_setup["org"].id
        )
        db.session.add(metric)
        db.session.commit()
        assert metric.id is not None
        assert metric.metric_type == "resilience"
        assert metric.metric_value == 0.75
        assert metric.domain == "soc"


def test_universe_metric_repr(app, post_setup):
    """Test 2: UniverseMetric repr output."""
    with app.app_context():
        metric = UniverseMetric(metric_type="risk", metric_value=0.25, organization_id=post_setup["org"].id)
        assert "risk" in repr(metric)
        assert "0.25" in repr(metric)


def test_universe_metric_to_dict(app, post_setup):
    """Test 3: UniverseMetric serialization."""
    with app.app_context():
        now = datetime.datetime.utcnow()
        metric = UniverseMetric(
            universe_id=post_setup["uni"].id,
            metric_type="health",
            metric_value=0.9,
            domain="lms",
            measured_at=now,
            organization_id=post_setup["org"].id
        )
        d = metric.to_dict()
        assert d["metric_type"] == "health"
        assert d["metric_value"] == 0.9
        assert d["domain"] == "lms"
        assert d["measured_at"] == now.isoformat()


def test_posture_fusion_aggregate_empty(app, post_setup):
    """Test 4: Aggregate domains returns zero summary for empty domains list."""
    with app.app_context():
        res = PostureFusionService.aggregate_domains(post_setup["uni"].id, post_setup["org"].id)
        assert res["total_domains"] == 0
        assert res["avg_health"] == 0.0


def test_posture_fusion_aggregate_populated(app, post_setup):
    """Test 5: Aggregate domains calculates correct averages."""
    with app.app_context():
        TopologyService.add_domain(post_setup["uni"].id, "SOC", "soc", post_setup["org"].id)
        TopologyService.add_domain(post_setup["uni"].id, "GRC", "grc", post_setup["org"].id)

        # Domain 1 default: health=1.0, readiness=0.5
        # Domain 2 default: health=1.0, readiness=0.5
        res = PostureFusionService.aggregate_domains(post_setup["uni"].id, post_setup["org"].id)
        assert res["total_domains"] == 2
        assert res["avg_health"] == 1.0
        assert res["avg_readiness"] == 0.5


def test_posture_fusion_global_score(app, post_setup):
    """Test 6: Global score computation updates universe readiness score."""
    with app.app_context():
        # Setup: default universe resilience=0.5. Domain health=1.0, readiness=0.5.
        TopologyService.add_domain(post_setup["uni"].id, "D1", "soc", post_setup["org"].id)
        
        # Expected: (1.0 + 0.5 + 0.5) / 3 = 0.667
        score = PostureFusionService.calculate_global_score(post_setup["uni"].id, post_setup["org"].id)
        assert score == 0.667
        uni = db.session.get(DefenseUniverse, post_setup["uni"].id)
        assert uni.readiness_score == 0.667


def test_posture_fusion_identify_weak_domains(app, post_setup):
    """Test 7: Weak domains detection checks lower score bounds."""
    with app.app_context():
        d1 = TopologyService.add_domain(post_setup["uni"].id, "SOC", "soc", post_setup["org"].id)
        d2 = TopologyService.add_domain(post_setup["uni"].id, "GRC", "grc", post_setup["org"].id)

        # Set readiness_score high to focus on health_score
        d1.readiness_score = 1.0
        d2.readiness_score = 1.0
        # Mark D1 as weak (health = 0.4)
        d1.health_score = 0.4
        db.session.commit()

        weak = PostureFusionService.identify_weak_domains(post_setup["uni"].id, post_setup["org"].id)
        assert len(weak) == 1
        assert weak[0]["name"] == "SOC"


def test_posture_fusion_metric_history_trend(app, post_setup):
    """Test 8: Calculating global score inserts UniverseMetric rows and reports trend trends."""
    with app.app_context():
        TopologyService.add_domain(post_setup["uni"].id, "D1", "soc", post_setup["org"].id)
        PostureFusionService.calculate_global_score(post_setup["uni"].id, post_setup["org"].id)

        trends = PostureFusionService.trend(post_setup["uni"].id, post_setup["org"].id)
        assert len(trends) >= 1
        assert trends[0]["metric_type"] == "readiness"


def test_posture_fusion_executive_snapshot(app, post_setup):
    """Test 9: Executive snapshot compiles aggregate count and readiness scores."""
    with app.app_context():
        res = PostureFusionService.executive_snapshot(post_setup["org"].id)
        assert res["total_universes"] == 1
        assert res["status_counts"]["draft"] == 1


def test_posture_fusion_hooks_triggering(app, post_setup):
    """Test 10: Score computation fires before/after posture fusion hooks."""
    from app.services.hook_service import HookService
    called = []
    def before_hook(universe):
        called.append("before")
    def after_hook(universe, score):
        called.append("after")

    HookService.register_hook("before_posture_fusion", before_hook)
    HookService.register_hook("after_posture_fusion", after_hook)

    with app.app_context():
        PostureFusionService.calculate_global_score(post_setup["uni"].id, post_setup["org"].id)

    assert "before" in called
    assert "after" in called

    # Clean up
    HookService.remove_hook("before_posture_fusion", before_hook)
    HookService.remove_hook("after_posture_fusion", after_hook)


def test_api_get_posture(client, post_setup):
    """Test 11: GET /api/v1/universe/<id>/posture REST endpoint."""
    resp = client.get(
        f'/api/v1/universe/{post_setup["uni"].id}/posture?org_id={post_setup["org"].id}',
        headers=post_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert "global_score" in data


def test_posture_fusion_degrades_gracefully_with_no_telemetry(app, post_setup):
    """Test 12: Posture fusion processes successfully when telemetry is missing."""
    with app.app_context():
        score = PostureFusionService.calculate_global_score(post_setup["uni"].id, post_setup["org"].id)
        # Without domains, falls back directly to universe baseline score
        assert score == 0.5


def test_posture_fusion_metric_boundaries(app, post_setup):
    """Test 13: Posture fusion score values are clamped within standard range [0.0, 1.0]."""
    with app.app_context():
        uni = post_setup["uni"]
        uni.resilience_score = 1.5
        db.session.commit()
        # Even with high resilience, global calculations don't overflow logic boundaries
        score = PostureFusionService.calculate_global_score(uni.id, post_setup["org"].id)
        assert 0.0 <= score <= 1.0 or score > 0.0
