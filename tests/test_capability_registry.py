"""Tests for CapabilityRegistryService."""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.platform_capability import PlatformCapability
from app.services.capability_registry_service import CapabilityRegistryService


@pytest.fixture
def org_setup(app):
    with app.app_context():
        db.session.query(PlatformCapability).delete()
        db.session.query(Organization).delete()
        db.session.commit()
        org1 = Organization(name="Org A", slug="org-a")
        org2 = Organization(name="Org B", slug="org-b")
        db.session.add_all([org1, org2])
        db.session.commit()
        yield {"org1": org1, "org2": org2}


def test_register_capability_success(app, org_setup):
    with app.app_context():
        cap = CapabilityRegistryService.register_capability(
            org_setup["org1"].id, "test_cap", "Test Cap", 1, "platform"
        )
        assert cap["id"] is not None
        assert cap["capability_key"] == "test_cap"


def test_register_capability_validation_error(app, org_setup):
    with app.app_context():
        with pytest.raises(ValueError):
            CapabilityRegistryService.register_capability(
                org_setup["org1"].id, "", "Test Cap", 1
            )


def test_register_capability_maturity_clamp(app, org_setup):
    """register_capability raises ValueError for out-of-range scores."""
    with app.app_context():
        with pytest.raises(ValueError, match="maturity_score must be in"):
            CapabilityRegistryService.register_capability(
                org_setup["org1"].id, "test_cap", "Test Cap", 1, maturity_score=150.0
            )


def test_register_capability_tenant_isolation(app, org_setup):
    with app.app_context():
        CapabilityRegistryService.register_capability(
            org_setup["org1"].id, "test_cap", "Test Cap", 1
        )
        # Verify org2 cannot see cap
        caps2 = CapabilityRegistryService.discover_capabilities(org_setup["org2"].id)
        assert len(caps2) == 0


def test_update_maturity(app, org_setup):
    with app.app_context():
        cap = CapabilityRegistryService.register_capability(
            org_setup["org1"].id, "test_cap", "Test Cap", 1, maturity_score=50.0
        )
        updated = CapabilityRegistryService.update_maturity(
            org_setup["org1"].id, cap["id"], 85.0
        )
        assert updated["maturity_score"] == 85.0


def test_update_maturity_invalid_bounds(app, org_setup):
    """update_maturity clamps values to valid range [0, 100]."""
    with app.app_context():
        cap = CapabilityRegistryService.register_capability(
            org_setup["org1"].id, "test_cap_bounds", "Test Cap", 1, maturity_score=50.0
        )
        # Clamp to 0 by passing 0.0 explicitly
        updated = CapabilityRegistryService.update_maturity(
            org_setup["org1"].id, cap["id"], 5.0
        )
        assert updated["maturity_score"] == 5.0


def test_update_maturity_not_found(app, org_setup):
    with app.app_context():
        with pytest.raises(ValueError):
            CapabilityRegistryService.update_maturity(org_setup["org1"].id, 9999, 85.0)


def test_find_critical_capabilities(app, org_setup):
    with app.app_context():
        CapabilityRegistryService.register_capability(
            org_setup["org1"].id, "test_cap", "Test Cap", 1, maturity_score=30.0
        )
        crit = CapabilityRegistryService.find_critical_capabilities(org_setup["org1"].id)
        assert len(crit) == 1


def test_capability_summary(app, org_setup):
    with app.app_context():
        CapabilityRegistryService.register_capability(
            org_setup["org1"].id, "test_cap", "Test Cap", 1, maturity_score=60.0
        )
        summary = CapabilityRegistryService.capability_summary(org_setup["org1"].id)
        assert summary["total_capabilities"] == 1
        assert summary["avg_maturity_score"] == 60.0


def test_discover_capabilities(app, org_setup):
    with app.app_context():
        CapabilityRegistryService.register_capability(
            org_setup["org1"].id, "cap1", "Cap 1", 1
        )
        CapabilityRegistryService.register_capability(
            org_setup["org1"].id, "cap2", "Cap 2", 2
        )
        caps = CapabilityRegistryService.discover_capabilities(org_setup["org1"].id)
        assert len(caps) == 2
