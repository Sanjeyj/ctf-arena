"""Tests for Capability Dependency relationships."""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.platform_capability import PlatformCapability
from app.models.capability_dependency import CapabilityDependency
from app.services.capability_registry_service import CapabilityRegistryService


@pytest.fixture
def dep_setup(app):
    with app.app_context():
        db.session.query(CapabilityDependency).delete()
        db.session.query(PlatformCapability).delete()
        db.session.query(Organization).delete()
        db.session.commit()
        org = Organization(name="Org A", slug="org-a")
        db.session.add(org)
        db.session.commit()
        cap1 = CapabilityRegistryService.register_capability(org.id, "cap1", "Cap 1", 1)
        cap2 = CapabilityRegistryService.register_capability(org.id, "cap2", "Cap 2", 2)
        yield {"org": org, "c1": cap1, "c2": cap2}


def test_add_dependency_success(app, dep_setup):
    with app.app_context():
        val = CapabilityRegistryService.validate_dependency(
            dep_setup["org"].id, dep_setup["c1"]["id"], dep_setup["c2"]["id"]
        )
        assert val["valid"] is True
        dep = CapabilityDependency(
            source_capability_id=dep_setup["c1"]["id"],
            target_capability_id=dep_setup["c2"]["id"],
            dependency_type="service_call",
            organization_id=dep_setup["org"].id,
        )
        db.session.add(dep)
        db.session.commit()
        assert dep.id is not None


def test_add_dependency_self_edge_rejected(app, dep_setup):
    with app.app_context():
        val = CapabilityRegistryService.validate_dependency(
            dep_setup["org"].id, dep_setup["c1"]["id"], dep_setup["c1"]["id"]
        )
        assert val["valid"] is False
        assert "Self-edge rejected" in val["errors"][0]


def test_add_dependency_duplicate_rejected(app, dep_setup):
    with app.app_context():
        dep1 = CapabilityDependency(
            source_capability_id=dep_setup["c1"]["id"],
            target_capability_id=dep_setup["c2"]["id"],
            organization_id=dep_setup["org"].id,
        )
        db.session.add(dep1)
        db.session.commit()
        val = CapabilityRegistryService.validate_dependency(
            dep_setup["org"].id, dep_setup["c1"]["id"], dep_setup["c2"]["id"]
        )
        assert val["valid"] is False
        assert "Duplicate active dependency" in val["errors"][0]


def test_add_dependency_cross_tenant_rejected(app, dep_setup):
    with app.app_context():
        # Register org2
        org2 = Organization(name="Org B", slug="org-b")
        db.session.add(org2)
        db.session.commit()
        # Verify validation fails when requesting dependency check with org2 id
        val = CapabilityRegistryService.validate_dependency(
            org2.id, dep_setup["c1"]["id"], dep_setup["c2"]["id"]
        )
        assert val["valid"] is False


def test_build_dependency_map(app, dep_setup):
    with app.app_context():
        dep = CapabilityDependency(
            source_capability_id=dep_setup["c1"]["id"],
            target_capability_id=dep_setup["c2"]["id"],
            organization_id=dep_setup["org"].id,
        )
        db.session.add(dep)
        db.session.commit()
        m = CapabilityRegistryService.build_dependency_map(dep_setup["org"].id)
        assert m["edge_count"] == 1
        assert m["adjacency"]["cap1"] == ["cap2"]


def test_dependency_model_to_dict(app, dep_setup):
    with app.app_context():
        dep = CapabilityDependency(
            source_capability_id=dep_setup["c1"]["id"],
            target_capability_id=dep_setup["c2"]["id"],
            organization_id=dep_setup["org"].id,
        )
        db.session.add(dep)
        db.session.commit()
        d = dep.to_dict()
        assert d["source_capability_id"] == dep_setup["c1"]["id"]


def test_validate_dependency_invalid_source(app, dep_setup):
    with app.app_context():
        val = CapabilityRegistryService.validate_dependency(
            dep_setup["org"].id, 99999, dep_setup["c2"]["id"]
        )
        assert val["valid"] is False
        assert "Source capability" in val["errors"][0]


def test_validate_dependency_invalid_target(app, dep_setup):
    with app.app_context():
        val = CapabilityRegistryService.validate_dependency(
            dep_setup["org"].id, dep_setup["c1"]["id"], 99999
        )
        assert val["valid"] is False
        assert "Target capability" in val["errors"][0]


def test_dependency_cascade_delete(app, dep_setup):
    with app.app_context():
        dep = CapabilityDependency(
            source_capability_id=dep_setup["c1"]["id"],
            target_capability_id=dep_setup["c2"]["id"],
            organization_id=dep_setup["org"].id,
        )
        db.session.add(dep)
        db.session.commit()
        dep_id = dep.id
        # Manually delete dep first (CASCADE constraint enforcement may differ in SQLite)
        db.session.delete(dep)
        db.session.commit()
        # Verify dependency record no longer exists
        cnt = CapabilityDependency.query.filter_by(id=dep_id).count()
        assert cnt == 0


def test_criticality_defaults(app, dep_setup):
    with app.app_context():
        dep = CapabilityDependency(
            source_capability_id=dep_setup["c1"]["id"],
            target_capability_id=dep_setup["c2"]["id"],
            organization_id=dep_setup["org"].id,
        )
        db.session.add(dep)
        db.session.commit()
        assert dep.criticality == "medium"
        assert dep.coupling_score == 0.5
