"""
Unit and Integration tests for FindingService.
Contains 10 test cases covering findings creation, source validation, risk calculations, status updates, deduplication, and hooks.
"""
import pytest
import datetime
from app.extensions import db
from app.models.organization import Organization
from app.models.exposure_asset import ExposureAsset
from app.models.exposure_finding import ExposureFinding
from app.services.finding_service import FindingService
from app.services.hook_service import HookService
from app.research.routes import create_jwt


@pytest.fixture
def finding_setup(app):
    with app.app_context():
        db.session.query(ExposureFinding).delete()
        db.session.query(ExposureAsset).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        db.session.add(o1)
        db.session.commit()

        asset = ExposureAsset(
            asset_reference_type="asset",
            asset_reference_id=1,
            display_name="DB Main",
            organization_id=o1.id
        )
        db.session.add(asset)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "o1": o1,
            "asset": asset,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_exposure_finding_model(app, finding_setup):
    """Test 1: ExposureFinding model fields validation."""
    with app.app_context():
        f = ExposureFinding(
            exposure_asset_id=finding_setup["asset"].id,
            finding_type="vulnerability",
            title="CVE-2024-0001",
            severity="high",
            likelihood=0.7,
            impact_score=8.0,
            confidence=0.9,
            status="open",
            source_type="simulation",
            organization_id=finding_setup["o1"].id
        )
        db.session.add(f)
        db.session.commit()
        assert f.id is not None
        assert f.title == "CVE-2024-0001"


def test_validate_source_allowed(app, finding_setup):
    """Test 2: validate_source allows simulation sources."""
    assert FindingService.validate_source("simulation") is True
    assert FindingService.validate_source("control_gap") is True


def test_validate_source_prohibited(app, finding_setup):
    """Test 3: validate_source rejects prohibited scanner tools."""
    with pytest.raises(ValueError, match="Live action or scanning source type"):
        FindingService.validate_source("nmap")

    with pytest.raises(ValueError, match="Live action or scanning source type"):
        FindingService.validate_source("nessus")


def test_create_finding_service(app, finding_setup):
    """Test 4: FindingService.create_finding."""
    with app.app_context():
        f = FindingService.create_finding(
            finding_setup["asset"].id, "misconfiguration", "Open Port 22", "high",
            0.9, 7.0, 1.0, "open", "simulation", "{}", finding_setup["o1"].id
        )
        assert f.id is not None
        assert f.title == "Open Port 22"


def test_create_finding_hook_mutation(app, finding_setup):
    """Test 5: before_exposure_evaluation hook controlled parameter mutation."""
    with app.app_context():
        HookService.clear_all()
        def callback(exposure_asset_id, finding_type, title, severity, likelihood, impact_score, confidence, status, source_type, org_id):
            return {'title': 'Mutated Title', 'severity': 'critical', 'likelihood': 1.0}

        HookService.register_hook('before_exposure_evaluation', callback)
        f = FindingService.create_finding(
            finding_setup["asset"].id, "misconfiguration", "Original Title", "low",
            0.1, 7.0, 1.0, "open", "simulation", "{}", finding_setup["o1"].id
        )
        assert f.title == "Mutated Title"
        assert f.severity == "critical"
        assert f.likelihood == 1.0
        HookService.clear_all()


def test_calculate_risk(app, finding_setup):
    """Test 6: calculate_risk formula evaluation."""
    with app.app_context():
        f = FindingService.create_finding(
            finding_setup["asset"].id, "misconfiguration", "Open Port 22", "high",
            0.5, 8.0, 1.0, "open", "simulation", "{}", finding_setup["o1"].id
        )
        risk = FindingService.calculate_risk(f.id, finding_setup["o1"].id)
        assert risk == 4.0  # 8.0 * 0.5


def test_update_status(app, finding_setup):
    """Test 7: update_status updates status and last_seen_at."""
    with app.app_context():
        f = FindingService.create_finding(
            finding_setup["asset"].id, "misconfiguration", "Open Port 22", "high",
            0.5, 8.0, 1.0, "open", "simulation", "{}", finding_setup["o1"].id
        )
        updated = FindingService.update_status(f.id, "mitigated", finding_setup["o1"].id)
        assert updated.status == "mitigated"


def test_deduplicate_no_duplicates(app, finding_setup):
    """Test 8: deduplicate does not delete unique findings."""
    with app.app_context():
        FindingService.create_finding(finding_setup["asset"].id, "vulnerability", "CVE-1", "high", 0.5, 8.0, 1.0, "open", "simulation", "{}", finding_setup["o1"].id)
        FindingService.create_finding(finding_setup["asset"].id, "vulnerability", "CVE-2", "high", 0.5, 8.0, 1.0, "open", "simulation", "{}", finding_setup["o1"].id)

        deleted = FindingService.deduplicate(finding_setup["o1"].id)
        assert deleted == 0


def test_deduplicate_with_duplicates(app, finding_setup):
    """Test 9: deduplicate removes redundant duplicate records."""
    with app.app_context():
        FindingService.create_finding(finding_setup["asset"].id, "vulnerability", "CVE-1", "high", 0.5, 8.0, 1.0, "open", "simulation", "{}", finding_setup["o1"].id)
        FindingService.create_finding(finding_setup["asset"].id, "vulnerability", "CVE-1", "high", 0.5, 8.0, 1.0, "open", "simulation", "{}", finding_setup["o1"].id)

        deleted = FindingService.deduplicate(finding_setup["o1"].id)
        assert deleted == 1


def test_finding_summary(app, finding_setup):
    """Test 10: finding_summary severity counts."""
    with app.app_context():
        FindingService.create_finding(finding_setup["asset"].id, "vulnerability", "CVE-1", "critical", 0.5, 8.0, 1.0, "open", "simulation", "{}", finding_setup["o1"].id)
        FindingService.create_finding(finding_setup["asset"].id, "vulnerability", "CVE-2", "low", 0.5, 8.0, 1.0, "open", "simulation", "{}", finding_setup["o1"].id)

        summary = FindingService.finding_summary(finding_setup["o1"].id)
        assert summary["critical"] == 1
        assert summary["low"] == 1
        assert summary["total"] == 2
