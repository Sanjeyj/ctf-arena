"""Tests for Platform Certification Service."""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.platform_certification_run import PlatformCertificationRun
from app.models.certification_check import CertificationCheck
from app.services.platform_certification_service import PlatformCertificationService


@pytest.fixture
def cert_setup(app):
    with app.app_context():
        db.session.query(CertificationCheck).delete()
        db.session.query(PlatformCertificationRun).delete()
        db.session.query(Organization).delete()
        db.session.commit()
        org = Organization(name="Org A", slug="org-a")
        db.session.add(org)
        db.session.commit()
        yield {"org": org}


def test_create_run_success(app, cert_setup):
    with app.app_context():
        run = PlatformCertificationService.create_run(
            cert_setup["org"].id, "Sprint 1 Audit", "release_candidate"
        )
        assert run["id"] is not None
        assert run["status"] == "running"


def test_create_run_invalid_type(app, cert_setup):
    with app.app_context():
        with pytest.raises(ValueError):
            PlatformCertificationService.create_run(
                cert_setup["org"].id, "Sprint 1 Audit", "bad_type"
            )


def test_execute_check_success(app, cert_setup):
    with app.app_context():
        run = PlatformCertificationService.create_run(cert_setup["org"].id, "Audit")
        check = PlatformCertificationService.execute_check(
            cert_setup["org"].id, run["id"], "security", "JWT check", "pass", "pass"
        )
        assert check["id"] is not None
        assert check["status"] == "passed"


def test_execute_check_invalid_run(app, cert_setup):
    with app.app_context():
        with pytest.raises(ValueError):
            PlatformCertificationService.execute_check(
                cert_setup["org"].id, 9999, "security", "JWT check"
            )


def test_execute_check_invalid_status(app, cert_setup):
    with app.app_context():
        run = PlatformCertificationService.create_run(cert_setup["org"].id, "Audit")
        with pytest.raises(ValueError):
            PlatformCertificationService.execute_check(
                cert_setup["org"].id, run["id"], "security", "JWT check", status="invalid"
            )


def test_calculate_category_scores(app, cert_setup):
    with app.app_context():
        run = PlatformCertificationService.create_run(cert_setup["org"].id, "Audit")
        PlatformCertificationService.execute_check(
            cert_setup["org"].id, run["id"], "security", "Check 1", status="passed"
        )
        PlatformCertificationService.execute_check(
            cert_setup["org"].id, run["id"], "security", "Check 2", status="failed"
        )
        scores = PlatformCertificationService.calculate_category_scores(
            cert_setup["org"].id, run["id"]
        )
        assert scores["security"] == 50.0


def test_calculate_overall_score(app, cert_setup):
    with app.app_context():
        scores = {"security": 90.0, "tenant_isolation": 80.0}
        overall = PlatformCertificationService.calculate_overall_score(scores)
        assert overall == 85.0


def test_complete_run(app, cert_setup):
    with app.app_context():
        run = PlatformCertificationService.create_run(cert_setup["org"].id, "Audit")
        PlatformCertificationService.execute_check(
            cert_setup["org"].id, run["id"], "security", "C1", status="passed"
        )
        res = PlatformCertificationService.complete_run(cert_setup["org"].id, run["id"])
        assert res["status"] == "completed"
        assert res["overall_score"] == 100.0


def test_identify_failures(app, cert_setup):
    with app.app_context():
        run = PlatformCertificationService.create_run(cert_setup["org"].id, "Audit")
        PlatformCertificationService.execute_check(
            cert_setup["org"].id, run["id"], "security", "C1", status="failed"
        )
        failures = PlatformCertificationService.identify_failures(
            cert_setup["org"].id, run["id"]
        )
        assert len(failures) == 1
        assert failures[0]["check_name"] == "C1"


def test_certification_summary(app, cert_setup):
    with app.app_context():
        run = PlatformCertificationService.create_run(cert_setup["org"].id, "Audit")
        PlatformCertificationService.execute_check(
            cert_setup["org"].id, run["id"], "security", "C1", status="passed"
        )
        PlatformCertificationService.complete_run(cert_setup["org"].id, run["id"])
        summary = PlatformCertificationService.certification_summary(cert_setup["org"].id)
        assert summary["total_runs"] == 1
        assert summary["completed_runs"] == 1
