"""Tests for Release Gating logic and human approvals."""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.release_baseline import ReleaseBaseline
from app.models.release_gate_decision import ReleaseGateDecision
from app.services.release_baseline_service import ReleaseBaselineService
from app.services.release_gate_service import ReleaseGateService


@pytest.fixture
def gate_setup(app):
    with app.app_context():
        db.session.query(ReleaseGateDecision).delete()
        db.session.query(ReleaseBaseline).delete()
        db.session.query(Organization).delete()
        db.session.commit()
        org = Organization(name="Org A", slug="org-a")
        db.session.add(org)
        db.session.commit()
        m = {"test_count": 1509, "warning_count": 0, "documentation_count": 10}
        bl = ReleaseBaselineService.create_baseline(org.id, "v1.0.0", m)
        yield {"org": org, "bl": bl}


def test_evaluate_test_gate_pass(app, gate_setup):
    with app.app_context():
        res = ReleaseGateService.evaluate_test_gate(
            gate_setup["org"].id, gate_setup["bl"]["id"]
        )
        assert res["decision"] == "pass"
        assert res["actual_score"] == 100.0


def test_evaluate_test_gate_fail(app, gate_setup):
    with app.app_context():
        # Create baseline with 0 tests
        bl2 = ReleaseBaselineService.create_baseline(
            gate_setup["org"].id, "v2.0.0", {"test_count": 0}
        )
        res = ReleaseGateService.evaluate_test_gate(
            gate_setup["org"].id, bl2["id"]
        )
        assert res["decision"] == "fail"
        assert res["actual_score"] == 0.0


def test_evaluate_security_gate_pass(app, gate_setup):
    with app.app_context():
        res = ReleaseGateService.evaluate_security_gate(
            gate_setup["org"].id, gate_setup["bl"]["id"]
        )
        assert res["decision"] == "pass"


def test_evaluate_security_gate_fail(app, gate_setup):
    with app.app_context():
        # Create baseline with 20 warnings
        bl2 = ReleaseBaselineService.create_baseline(
            gate_setup["org"].id, "v2.0.0", {"warning_count": 20}
        )
        res = ReleaseGateService.evaluate_security_gate(
            gate_setup["org"].id, bl2["id"]
        )
        assert res["decision"] == "fail"


def test_evaluate_tenant_gate(app, gate_setup):
    with app.app_context():
        res = ReleaseGateService.evaluate_tenant_gate(
            gate_setup["org"].id, gate_setup["bl"]["id"]
        )
        assert res["decision"] == "pass"


def test_evaluate_ai_safety_gate(app, gate_setup):
    with app.app_context():
        res = ReleaseGateService.evaluate_ai_safety_gate(
            gate_setup["org"].id, gate_setup["bl"]["id"]
        )
        assert res["decision"] == "pass"


def test_evaluate_migration_gate(app, gate_setup):
    with app.app_context():
        res = ReleaseGateService.evaluate_migration_gate(
            gate_setup["org"].id, gate_setup["bl"]["id"]
        )
        assert res["decision"] == "pass"


def test_approve_release_gate_success(app, gate_setup):
    with app.app_context():
        res = ReleaseGateService.evaluate_test_gate(
            gate_setup["org"].id, gate_setup["bl"]["id"]
        )
        approved = ReleaseGateService.approve_release(
            gate_setup["org"].id, res["id"], "Lead Auditor"
        )
        assert approved["approved_by"] == "Lead Auditor"


def test_approve_release_gate_missing_signature(app, gate_setup):
    with app.app_context():
        res = ReleaseGateService.evaluate_test_gate(
            gate_setup["org"].id, gate_setup["bl"]["id"]
        )
        with pytest.raises(ValueError, match="signature required"):
            ReleaseGateService.approve_release(
                gate_setup["org"].id, res["id"], ""
            )


def test_release_gate_summary(app, gate_setup):
    with app.app_context():
        ReleaseGateService.evaluate_test_gate(
            gate_setup["org"].id, gate_setup["bl"]["id"]
        )
        sumry = ReleaseGateService.release_gate_summary(
            gate_setup["org"].id, gate_setup["bl"]["id"]
        )
        assert sumry["gates_evaluated"] == 1
        assert sumry["overall_status"] == "pass"
