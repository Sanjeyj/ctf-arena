"""
Unit and Integration tests for RemediationPrioritizationService.
Contains 10 test cases covering remediation plans, creation, priority formulas, approvals, closures, and hook mutation.
"""
import pytest
import datetime
from app.extensions import db
from app.models.organization import Organization
from app.models.exposure_asset import ExposureAsset
from app.models.exposure_finding import ExposureFinding
from app.models.remediation_plan import RemediationPlan
from app.services.remediation_prioritization_service import RemediationPrioritizationService
from app.services.hook_service import HookService
from app.research.routes import create_jwt


@pytest.fixture
def rem_setup(app):
    with app.app_context():
        db.session.query(RemediationPlan).delete()
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
            display_name="DB",
            organization_id=o1.id
        )
        db.session.add(asset)
        db.session.commit()

        f = ExposureFinding(
            exposure_asset_id=asset.id,
            finding_type="vulnerability",
            title="CVE-2024",
            severity="high",
            likelihood=0.8,
            impact_score=6.0,
            confidence=1.0,
            status="open",
            organization_id=o1.id
        )
        db.session.add(f)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "o1": o1,
            "f": f,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_remediation_plan_model(app, rem_setup):
    """Test 1: RemediationPlan model fields initialization."""
    with app.app_context():
        p = RemediationPlan(
            title="Apply Patch",
            finding_id=rem_setup["f"].id,
            priority_score=18.0,
            recommended_action="Upgrade software",
            approval_status="draft",
            status="planned",
            organization_id=rem_setup["o1"].id
        )
        db.session.add(p)
        db.session.commit()
        assert p.id is not None
        assert p.title == "Apply Patch"


def test_create_plan_service(app, rem_setup):
    """Test 2: RemediationPrioritizationService.create_plan."""
    with app.app_context():
        p = RemediationPrioritizationService.create_plan(
            "Fix CVE-2024", rem_setup["f"].id, "Apply upgrade", None, rem_setup["o1"].id
        )
        assert p.id is not None
        # High finding -> mult=3.0. impact_score=6.0. Priority = 18.0
        assert p.priority_score == 18.0
        assert p.approval_status == "draft"


def test_create_plan_hook_mutation(app, rem_setup):
    """Test 3: before_remediation_prioritization hook mutation."""
    with app.app_context():
        HookService.clear_all()
        def callback(title, finding_id, recommended_action, priority_score, org_id):
            return {'priority_score': 99.0}

        HookService.register_hook('before_remediation_prioritization', callback)
        p = RemediationPrioritizationService.create_plan(
            "Fix CVE-2024", rem_setup["f"].id, "Apply upgrade", None, rem_setup["o1"].id
        )
        assert p.priority_score == 99.0
        HookService.clear_all()


def test_calculate_priority(app, rem_setup):
    """Test 4: calculate_priority recalculation check."""
    with app.app_context():
        p = RemediationPrioritizationService.create_plan(
            "Fix CVE-2024", rem_setup["f"].id, "Apply upgrade", None, rem_setup["o1"].id
        )
        # Manually alter priority score
        p.priority_score = 1.0
        db.session.commit()

        score = RemediationPrioritizationService.calculate_priority(p.id, rem_setup["o1"].id)
        assert score == 18.0


def test_recommend_compensating_controls_vuln(app, rem_setup):
    """Test 5: recommend_compensating_controls for vulnerability finding."""
    with app.app_context():
        p = RemediationPrioritizationService.create_plan("Fix", rem_setup["f"].id, "Action", None, rem_setup["o1"].id)
        recs = RemediationPrioritizationService.recommend_compensating_controls(p.id, rem_setup["o1"].id)
        assert "VULN-PATCH-01" in recs


def test_recommend_compensating_controls_misc(app, rem_setup):
    """Test 6: recommend_compensating_controls for misconfiguration finding."""
    with app.app_context():
        f = ExposureFinding(
            exposure_asset_id=rem_setup["f"].exposure_asset_id,
            finding_type="misconfiguration",
            title="Open Ports",
            organization_id=rem_setup["o1"].id
        )
        db.session.add(f)
        db.session.commit()

        p = RemediationPrioritizationService.create_plan("Fix Misc", f.id, "Action", None, rem_setup["o1"].id)
        recs = RemediationPrioritizationService.recommend_compensating_controls(p.id, rem_setup["o1"].id)
        assert "CONF-AUDIT-03" in recs


def test_recommend_compensating_controls_creds(app, rem_setup):
    """Test 7: recommend_compensating_controls for credentials findings."""
    with app.app_context():
        f = ExposureFinding(
            exposure_asset_id=rem_setup["f"].exposure_asset_id,
            finding_type="credentials_leak",
            title="Leaked Private Key",
            organization_id=rem_setup["o1"].id
        )
        db.session.add(f)
        db.session.commit()

        p = RemediationPrioritizationService.create_plan("Fix Creds", f.id, "Action", None, rem_setup["o1"].id)
        recs = RemediationPrioritizationService.recommend_compensating_controls(p.id, rem_setup["o1"].id)
        assert "AUTH-MFA-05" in recs


def test_approve_plan(app, rem_setup):
    """Test 8: approve_plan transitions approval_status to approved."""
    with app.app_context():
        p = RemediationPrioritizationService.create_plan("Fix", rem_setup["f"].id, "Action", None, rem_setup["o1"].id)
        approved = RemediationPrioritizationService.approve_plan(p.id, rem_setup["o1"].id)
        assert approved.approval_status == "approved"


def test_close_plan(app, rem_setup):
    """Test 9: close_plan updates plan status."""
    with app.app_context():
        p = RemediationPrioritizationService.create_plan("Fix", rem_setup["f"].id, "Action", None, rem_setup["o1"].id)
        closed = RemediationPrioritizationService.close_plan(p.id, "completed", rem_setup["o1"].id)
        assert closed.status == "completed"


def test_remediation_summary(app, rem_setup):
    """Test 10: remediation_summary aggregates."""
    with app.app_context():
        p1 = RemediationPrioritizationService.create_plan("P1", rem_setup["f"].id, "Action", None, rem_setup["o1"].id)
        RemediationPrioritizationService.approve_plan(p1.id, rem_setup["o1"].id)
        RemediationPrioritizationService.close_plan(p1.id, "completed", rem_setup["o1"].id)

        summary = RemediationPrioritizationService.remediation_summary(rem_setup["o1"].id)
        assert summary["total_plans"] == 1
        assert summary["approved_plans"] == 1
        assert summary["completed_plans"] == 1
