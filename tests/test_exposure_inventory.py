"""
Unit and Integration tests for ExposureInventoryService.
Contains 10 test cases covering exposure assets, registration, score formulas, metrics, and trends.
"""
import pytest
import datetime
from app.extensions import db
from app.models.organization import Organization
from app.models.exposure_asset import ExposureAsset
from app.models.exposure_finding import ExposureFinding
from app.models.asset import Asset
from app.services.exposure_inventory_service import ExposureInventoryService
from app.research.routes import create_jwt


@pytest.fixture
def exp_setup(app):
    with app.app_context():
        db.session.query(ExposureFinding).delete()
        db.session.query(ExposureAsset).delete()
        db.session.query(Asset).delete()
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


def test_exposure_asset_model(app, exp_setup):
    """Test 1: ExposureAsset model fields instantiation."""
    with app.app_context():
        ea = ExposureAsset(
            asset_reference_type="asset",
            asset_reference_id=1,
            display_name="Database Main",
            exposure_type="internal",
            internet_exposed=False,
            criticality="high",
            business_impact_score=8.5,
            organization_id=exp_setup["o1"].id
        )
        db.session.add(ea)
        db.session.commit()
        assert ea.id is not None
        assert ea.display_name == "Database Main"
        assert ea.business_impact_score == 8.5


def test_register_projection(app, exp_setup):
    """Test 2: ExposureInventoryService.register_projection."""
    with app.app_context():
        ea = ExposureInventoryService.register_projection(
            "asset", 10, "Server Test", "perimeter", True, "critical", 9.0, None, exp_setup["o1"].id
        )
        assert ea.id is not None
        assert ea.display_name == "Server Test"
        assert ea.internet_exposed is True


def test_resolve_reference_valid(app, exp_setup):
    """Test 3: resolve_reference resolves original Asset model."""
    with app.app_context():
        orig = Asset(name="HW-01", type_label="server")
        db.session.add(orig)
        db.session.commit()

        ea = ExposureInventoryService.register_projection(
            "asset", orig.id, "Server", "internal", False, "low", 2.0, None, exp_setup["o1"].id
        )
        resolved = ExposureInventoryService.resolve_reference(ea.id, exp_setup["o1"].id)
        assert resolved is not None
        assert resolved.name == "HW-01"


def test_resolve_reference_missing(app, exp_setup):
    """Test 4: resolve_reference returns None for missing original model."""
    with app.app_context():
        ea = ExposureInventoryService.register_projection(
            "asset", 9999, "Missing Asset", "internal", False, "low", 2.0, None, exp_setup["o1"].id
        )
        resolved = ExposureInventoryService.resolve_reference(ea.id, exp_setup["o1"].id)
        assert resolved is None


def test_exposure_score_basic(app, exp_setup):
    """Test 5: calculate_exposure_score base values."""
    with app.app_context():
        ea = ExposureInventoryService.register_projection(
            "asset", 1, "Server", "internal", False, "medium", 5.0, None, exp_setup["o1"].id
        )
        # Base: internal=2.0. criticality=medium (mult=1.0). impact=5.0 (mult=1.0). Expected: 2.0
        score = ExposureInventoryService.calculate_exposure_score(ea.id, exp_setup["o1"].id)
        assert score == 2.0


def test_exposure_score_internet_exposed(app, exp_setup):
    """Test 6: calculate_exposure_score internet exposed penalty."""
    with app.app_context():
        ea = ExposureInventoryService.register_projection(
            "asset", 1, "Server", "internal", True, "medium", 5.0, None, exp_setup["o1"].id
        )
        # Base: internet_exposed=8.0. Expected: 8.0
        score = ExposureInventoryService.calculate_exposure_score(ea.id, exp_setup["o1"].id)
        assert score == 8.0


def test_exposure_score_findings(app, exp_setup):
    """Test 7: calculate_exposure_score cumulative findings penalty."""
    with app.app_context():
        ea = ExposureInventoryService.register_projection(
            "asset", 1, "Server", "internal", False, "medium", 5.0, None, exp_setup["o1"].id
        )
        f = ExposureFinding(
            exposure_asset_id=ea.id,
            finding_type="vulnerability",
            title="CVE-2024",
            severity="high",
            likelihood=0.8,
            impact_score=6.0,
            confidence=1.0,
            status="open",
            organization_id=exp_setup["o1"].id
        )
        db.session.add(f)
        db.session.commit()

        score = ExposureInventoryService.calculate_exposure_score(ea.id, exp_setup["o1"].id)
        assert abs(score - 6.8) < 1e-9


def test_list_exposed_assets(app, exp_setup):
    """Test 8: list_exposed_assets returns list containing scores."""
    with app.app_context():
        ea = ExposureInventoryService.register_projection(
            "asset", 1, "Server", "internal", False, "medium", 5.0, None, exp_setup["o1"].id
        )
        assets = ExposureInventoryService.list_exposed_assets(exp_setup["o1"].id)
        assert len(assets) == 1
        assert assets[0]["display_name"] == "Server"
        assert "exposure_score" in assets[0]


def test_exposure_summary(app, exp_setup):
    """Test 9: exposure_summary aggregations."""
    with app.app_context():
        ExposureInventoryService.register_projection("asset", 1, "S1", "internal", False, "medium", 5.0, None, exp_setup["o1"].id)
        ExposureInventoryService.register_projection("asset", 2, "S2", "external", True, "medium", 5.0, None, exp_setup["o1"].id)

        summary = ExposureInventoryService.exposure_summary(exp_setup["o1"].id)
        assert summary["total_assets"] == 2
        assert summary["exposed_count"] == 1


def test_exposure_trend(app, exp_setup):
    """Test 10: exposure_trend returns lists of objects."""
    with app.app_context():
        ExposureInventoryService.register_projection("asset", 1, "S1", "internal", False, "medium", 5.0, None, exp_setup["o1"].id)
        trend = ExposureInventoryService.exposure_trend(exp_setup["o1"].id)
        assert len(trend) == 3
        assert trend[0]["date"] == "7 days ago"
