"""Tests for Platform Readiness composite scoring."""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.platform_readiness_metric import PlatformReadinessMetric
from app.models.platform_capability import PlatformCapability
from app.services.platform_readiness_service import PlatformReadinessService
from app.services.capability_registry_service import CapabilityRegistryService


@pytest.fixture
def read_setup(app):
    with app.app_context():
        db.session.query(PlatformReadinessMetric).delete()
        db.session.query(PlatformCapability).delete()
        db.session.query(Organization).delete()
        db.session.commit()
        org = Organization(name="Org A", slug="org-a")
        db.session.add(org)
        db.session.commit()
        yield {"org": org}


def test_weight_assertions(app, read_setup):
    w_sec = PlatformReadinessMetric.WEIGHT_SECURITY
    w_rel = PlatformReadinessMetric.WEIGHT_RELIABILITY
    w_gov = PlatformReadinessMetric.WEIGHT_GOVERNANCE
    w_res = PlatformReadinessMetric.WEIGHT_RESILIENCE
    w_ass = PlatformReadinessMetric.WEIGHT_ASSURANCE
    w_ops = PlatformReadinessMetric.WEIGHT_OPERATIONS
    total = w_sec + w_rel + w_gov + w_res + w_ass + w_ops
    assert abs(total - 1.0) < 1e-9


def test_calculate_overall_readiness(app, read_setup):
    score = PlatformReadinessService.calculate_overall_readiness(
        security=100.0,
        reliability=100.0,
        governance=100.0,
        resilience=100.0,
        assurance=100.0,
        operations=100.0,
    )
    assert score == 100.0


def test_calculate_overall_readiness_partial(app, read_setup):
    score = PlatformReadinessService.calculate_overall_readiness(
        security=50.0,
        reliability=80.0,
        governance=70.0,
        resilience=90.0,
        assurance=60.0,
        operations=40.0,
    )
    # 50*0.2 + 80*0.15 + 70*0.15 + 90*0.2 + 60*0.15 + 40*0.15
    # = 10 + 12 + 10.5 + 18 + 9 + 6 = 65.5
    assert score == 65.5


def test_calculate_security_readiness_default(app, read_setup):
    with app.app_context():
        val = PlatformReadinessService.calculate_security_readiness(read_setup["org"].id)
        assert val == 75.0  # default fallback


def test_calculate_security_readiness_dynamic(app, read_setup):
    with app.app_context():
        CapabilityRegistryService.register_capability(
            read_setup["org"].id, "sec_cap", "Sec", 1, "security", maturity_score=90.0
        )
        val = PlatformReadinessService.calculate_security_readiness(read_setup["org"].id)
        assert val == 90.0


def test_calculate_reliability_readiness_default(app, read_setup):
    with app.app_context():
        val = PlatformReadinessService.calculate_reliability_readiness(read_setup["org"].id)
        assert val == 80.0  # default fallback


def test_calculate_governance_readiness_default(app, read_setup):
    with app.app_context():
        val = PlatformReadinessService.calculate_governance_readiness(read_setup["org"].id)
        assert val == 82.0


def test_save_metric_success(app, read_setup):
    with app.app_context():
        metric = PlatformReadinessService.save_metric(
            read_setup["org"].id, "on_demand", "Baseline measurement"
        )
        assert metric["id"] is not None
        assert metric["overall_readiness_score"] > 0.0


def test_save_metric_invalid_type(app, read_setup):
    with app.app_context():
        with pytest.raises(ValueError):
            PlatformReadinessService.save_metric(read_setup["org"].id, "bad_type")


def test_readiness_summary(app, read_setup):
    with app.app_context():
        PlatformReadinessService.save_metric(read_setup["org"].id)
        summary = PlatformReadinessService.readiness_summary(read_setup["org"].id)
        assert summary["total_measurements"] == 1
        assert summary["latest"] is not None
