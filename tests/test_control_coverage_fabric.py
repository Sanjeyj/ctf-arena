"""
Unit and Integration tests for ControlCoverageService.
Contains 10 test cases covering coverage maps, calculations, validation links, gaps, and hook executions.
"""
import pytest
import datetime
from app.extensions import db
from app.models.organization import Organization
from app.models.control_coverage_map import ControlCoverageMap
from app.models.control_validation import ControlValidation
from app.services.control_coverage_service import ControlCoverageService
from app.services.hook_service import HookService
from app.research.routes import create_jwt


@pytest.fixture
def cov_setup(app):
    with app.app_context():
        db.session.query(ControlCoverageMap).delete()
        db.session.query(ControlValidation).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="Org 1", slug="org-1", plan_type="enterprise")
        db.session.add(o1)
        db.session.commit()

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "admin"}, secret)

        yield {
            "o1": o1,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_control_coverage_model(app, cov_setup):
    """Test 1: ControlCoverageMap model initialization."""
    with app.app_context():
        cc = ControlCoverageMap(
            control_reference="CTRL-001",
            resource_type="asset",
            resource_id=1,
            coverage_score=0.8,
            effectiveness_score=0.9,
            validation_status="valid",
            organization_id=cov_setup["o1"].id
        )
        db.session.add(cc)
        db.session.commit()
        assert cc.id is not None
        assert cc.control_reference == "CTRL-001"


def test_map_control_service(app, cov_setup):
    """Test 2: ControlCoverageService.map_control."""
    with app.app_context():
        cc = ControlCoverageService.map_control("CTRL-001", "asset", 1, 0.7, 0.8, "unvalidated", cov_setup["o1"].id)
        assert cc.id is not None
        assert cc.coverage_score == 0.7


def test_map_control_hook_mutation(app, cov_setup):
    """Test 3: before_control_coverage_evaluation hook parameter mutation."""
    with app.app_context():
        HookService.clear_all()
        def callback(control_ref, resource_type, resource_id, coverage_score, effectiveness_score, status, org_id):
            return {'coverage_score': 0.99, 'effectiveness_score': 0.95}

        HookService.register_hook('before_control_coverage_evaluation', callback)
        cc = ControlCoverageService.map_control("CTRL-001", "asset", 1, 0.1, 0.1, "unvalidated", cov_setup["o1"].id)
        assert cc.coverage_score == 0.99
        assert cc.effectiveness_score == 0.95
        HookService.clear_all()


def test_calculate_coverage_none(app, cov_setup):
    """Test 4: calculate_coverage returns 0 when no validations exist."""
    with app.app_context():
        cov = ControlCoverageService.calculate_coverage("CTRL-001", cov_setup["o1"].id)
        assert cov == 0.0


def test_calculate_coverage_mix(app, cov_setup):
    """Test 5: calculate_coverage correct valid/invalid ratio."""
    with app.app_context():
        v1 = ControlValidation(
            control_reference="CTRL-001",
            status="passed",
            validation_type="automated",
            expected_result="passed",
            actual_result="passed",
            tested_at=datetime.datetime.utcnow(),
            effectiveness_score=1.0,
            organization_id=cov_setup["o1"].id
        )
        v2 = ControlValidation(
            control_reference="CTRL-001",
            status="failed",
            validation_type="automated",
            expected_result="passed",
            actual_result="failed",
            tested_at=datetime.datetime.utcnow(),
            effectiveness_score=0.0,
            organization_id=cov_setup["o1"].id
        )
        db.session.add_all([v1, v2])
        db.session.commit()

        cov = ControlCoverageService.calculate_coverage("CTRL-001", cov_setup["o1"].id)
        assert cov == 0.5


def test_calculate_effectiveness_none(app, cov_setup):
    """Test 6: calculate_effectiveness fallback value."""
    with app.app_context():
        eff = ControlCoverageService.calculate_effectiveness("CTRL-001", cov_setup["o1"].id)
        assert eff == 0.0


def test_calculate_effectiveness_average(app, cov_setup):
    """Test 7: calculate_effectiveness average normalized score."""
    with app.app_context():
        v1 = ControlValidation(
            control_reference="CTRL-001",
            status="passed",
            validation_type="automated",
            expected_result="passed",
            actual_result="passed",
            tested_at=datetime.datetime.utcnow(),
            effectiveness_score=0.9,
            organization_id=cov_setup["o1"].id
        )
        v2 = ControlValidation(
            control_reference="CTRL-001",
            status="passed",
            validation_type="automated",
            expected_result="passed",
            actual_result="passed",
            tested_at=datetime.datetime.utcnow(),
            effectiveness_score=0.8,
            organization_id=cov_setup["o1"].id
        )
        db.session.add_all([v1, v2])
        db.session.commit()

        eff = ControlCoverageService.calculate_effectiveness("CTRL-001", cov_setup["o1"].id)
        assert eff == 0.85  # average score 85 -> normalized to 0.85


def test_find_coverage_gaps(app, cov_setup):
    """Test 8: find_coverage_gaps identifies weak controls."""
    with app.app_context():
        ControlCoverageService.map_control("CTRL-001", "asset", 1, 0.4, 0.8, "unvalidated", cov_setup["o1"].id)
        ControlCoverageService.map_control("CTRL-002", "asset", 1, 0.9, 0.9, "valid", cov_setup["o1"].id)

        gaps = ControlCoverageService.find_coverage_gaps(cov_setup["o1"].id)
        assert len(gaps) == 1
        assert gaps[0]["control_reference"] == "CTRL-001"


def test_apply_validation_result(app, cov_setup):
    """Test 9: apply_validation_result creates or updates maps."""
    with app.app_context():
        cc = ControlCoverageService.apply_validation_result("CTRL-001", "asset", 1, "valid", 95.0, cov_setup["o1"].id)
        assert cc.validation_status == "valid"
        assert cc.effectiveness_score == 0.95
        assert cc.coverage_score == 1.0


def test_coverage_summary(app, cov_setup):
    """Test 10: coverage_summary statistics."""
    with app.app_context():
        ControlCoverageService.map_control("CTRL-001", "asset", 1, 0.8, 0.8, "valid", cov_setup["o1"].id)
        ControlCoverageService.map_control("CTRL-002", "asset", 1, 0.6, 0.6, "valid", cov_setup["o1"].id)

        summary = ControlCoverageService.coverage_summary(cov_setup["o1"].id)
        assert summary["total_mapped"] == 2
        assert summary["avg_coverage"] == 0.7
        assert summary["avg_effectiveness"] == 0.7
