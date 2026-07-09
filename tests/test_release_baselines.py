"""Tests for Release Baseline tracking and capture."""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.release_baseline import ReleaseBaseline
from app.services.release_baseline_service import ReleaseBaselineService


@pytest.fixture
def base_setup(app):
    with app.app_context():
        db.session.query(ReleaseBaseline).delete()
        db.session.query(Organization).delete()
        db.session.commit()
        org = Organization(name="Org A", slug="org-a")
        db.session.add(org)
        db.session.commit()
        yield {"org": org}


def test_collect_repository_metrics(app, base_setup):
    metrics = ReleaseBaselineService.collect_repository_metrics(
        migration_revision="head_rev",
        test_count=1509,
        warning_count=0,
        model_count=120,
        service_count=90,
        route_count=200,
        template_count=130,
        documentation_count=90,
    )
    assert metrics["test_count"] == 1509


def test_calculate_baseline_hash_deterministic(app, base_setup):
    metrics1 = {"test_count": 1500, "warning_count": 0}
    metrics2 = {"warning_count": 0, "test_count": 1500}
    h1 = ReleaseBaselineService.calculate_baseline_hash(metrics1)
    h2 = ReleaseBaselineService.calculate_baseline_hash(metrics2)
    assert h1 == h2


def test_create_baseline_success(app, base_setup):
    with app.app_context():
        metrics = ReleaseBaselineService.collect_repository_metrics(
            "rev1", 1509, 0, 10, 10, 10, 10, 10
        )
        bl = ReleaseBaselineService.create_baseline(
            base_setup["org"].id, "v1.0.0", metrics, codename="Genesis"
        )
        assert bl["id"] is not None
        assert bl["status"] == "draft"


def test_create_baseline_duplicate_rejected(app, base_setup):
    with app.app_context():
        metrics = ReleaseBaselineService.collect_repository_metrics(
            "rev1", 1509, 0, 10, 10, 10, 10, 10
        )
        ReleaseBaselineService.create_baseline(
            base_setup["org"].id, "v1.0.0", metrics
        )
        with pytest.raises(ValueError, match="already exists"):
            ReleaseBaselineService.create_baseline(
                base_setup["org"].id, "v1.0.0", metrics
            )


def test_compare_baselines(app, base_setup):
    with app.app_context():
        m1 = {"test_count": 1400, "migration_revision": "rev1", "model_count": 5}
        m2 = {"test_count": 1500, "migration_revision": "rev2", "model_count": 7}
        bl1 = ReleaseBaselineService.create_baseline(
            base_setup["org"].id, "v1.0.0", m1
        )
        bl2 = ReleaseBaselineService.create_baseline(
            base_setup["org"].id, "v2.0.0", m2
        )
        res = ReleaseBaselineService.compare_baselines(
            base_setup["org"].id, bl1["id"], bl2["id"]
        )
        assert res["test_count_delta"] == 100
        assert res["model_count_delta"] == 2
        assert res["migration_changed"] is True


def test_approve_baseline_success(app, base_setup):
    with app.app_context():
        m = {"test_count": 1400, "migration_revision": "rev1"}
        bl = ReleaseBaselineService.create_baseline(
            base_setup["org"].id, "v1.0.0", m
        )
        approved = ReleaseBaselineService.approve_baseline(
            base_setup["org"].id, bl["id"], "Lead Architect"
        )
        assert approved["status"] == "approved"
        assert approved["approved_by"] == "Lead Architect"


def test_approve_baseline_missing_signature(app, base_setup):
    with app.app_context():
        m = {"test_count": 1400, "migration_revision": "rev1"}
        bl = ReleaseBaselineService.create_baseline(
            base_setup["org"].id, "v1.0.0", m
        )
        with pytest.raises(ValueError, match="approved_by identity is required"):
            ReleaseBaselineService.approve_baseline(
                base_setup["org"].id, bl["id"], ""
            )


def test_supersede_baseline(app, base_setup):
    with app.app_context():
        m = {"test_count": 1400, "migration_revision": "rev1"}
        bl = ReleaseBaselineService.create_baseline(
            base_setup["org"].id, "v1.0.0", m
        )
        res = ReleaseBaselineService.supersede_baseline(
            base_setup["org"].id, bl["id"], "v2.0.0"
        )
        assert res["status"] == "superseded"
        assert "Superseded by v2.0.0" in res["notes"]


def test_baseline_summary(app, base_setup):
    with app.app_context():
        m = {"test_count": 1400, "migration_revision": "rev1"}
        ReleaseBaselineService.create_baseline(
            base_setup["org"].id, "v1.0.0", m
        )
        sumry = ReleaseBaselineService.baseline_summary(base_setup["org"].id)
        assert sumry["total_baselines"] == 1


def test_immutable_hash_after_creation(app, base_setup):
    with app.app_context():
        m = {"test_count": 1400, "migration_revision": "rev1"}
        bl = ReleaseBaselineService.create_baseline(
            base_setup["org"].id, "v1.0.0", m
        )
        bl_db = ReleaseBaseline.query.get(bl["id"])
        # Attempt modifying version
        bl_db.version = "v1.0.1"
        db.session.commit()
        # Verify hash remains identical and codifies original metrics
        assert bl_db.baseline_hash == bl["baseline_hash"]
