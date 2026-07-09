"""Tests for Architecture Convergence and overlap analysis."""
import pytest
from app.extensions import db
from app.models.organization import Organization
from app.models.platform_capability import PlatformCapability
from app.services.architecture_convergence_service import ArchitectureConvergenceService
from app.services.capability_registry_service import CapabilityRegistryService


@pytest.fixture
def arch_setup(app):
    with app.app_context():
        db.session.query(PlatformCapability).delete()
        db.session.query(Organization).delete()
        db.session.commit()
        org = Organization(name="Org A", slug="org-a")
        db.session.add(org)
        db.session.commit()
        yield {"org": org}


def test_build_ownership_matrix(app, arch_setup):
    with app.app_context():
        CapabilityRegistryService.register_capability(
            arch_setup["org"].id, "cap1", "Cap 1", 1, "platform"
        )
        CapabilityRegistryService.register_capability(
            arch_setup["org"].id, "cap2", "Cap 2", 2, "platform"
        )
        matrix = ArchitectureConvergenceService.build_ownership_matrix(arch_setup["org"].id)
        assert len(matrix["phases"]) == 2
        assert matrix["total_capabilities"] == 2


def test_detect_capability_overlap_none(app, arch_setup):
    with app.app_context():
        CapabilityRegistryService.register_capability(
            arch_setup["org"].id, "cap1", "Cap 1", 1, "platform"
        )
        overlaps = ArchitectureConvergenceService.detect_capability_overlap(arch_setup["org"].id)
        assert len(overlaps) == 0


def test_detect_capability_overlap_exists(app, arch_setup):
    with app.app_context():
        CapabilityRegistryService.register_capability(
            arch_setup["org"].id, "cap1", "Cap 1", 1, "risk"
        )
        CapabilityRegistryService.register_capability(
            arch_setup["org"].id, "cap2", "Cap 2", 2, "risk"
        )
        overlaps = ArchitectureConvergenceService.detect_capability_overlap(arch_setup["org"].id)
        assert len(overlaps) == 1
        assert overlaps[0]["canonical_owner"] == "risk_quantification"


def test_identify_canonical_owner_success(app, arch_setup):
    with app.app_context():
        CapabilityRegistryService.register_capability(
            arch_setup["org"].id, "risk_quantification", "Risk Canonical", 36, "risk"
        )
        canonical = ArchitectureConvergenceService.identify_canonical_owner(
            arch_setup["org"].id, "risk"
        )
        assert canonical is not None
        assert canonical["capability_key"] == "risk_quantification"


def test_identify_canonical_owner_not_found(app, arch_setup):
    with app.app_context():
        canonical = ArchitectureConvergenceService.identify_canonical_owner(
            arch_setup["org"].id, "risk"
        )
        assert canonical is None


def test_identify_projection_models(app, arch_setup):
    with app.app_context():
        # register canonical risk and a projection risk
        CapabilityRegistryService.register_capability(
            arch_setup["org"].id, "risk_quantification", "Risk Canonical", 36, "risk"
        )
        CapabilityRegistryService.register_capability(
            arch_setup["org"].id, "business_dependency_risk", "Business Risk", 30, "risk"
        )
        projections = ArchitectureConvergenceService.identify_projection_models(
            arch_setup["org"].id
        )
        assert len(projections) == 1
        assert projections[0]["capability_key"] == "business_dependency_risk"


def test_validate_route_ownership_pass(app, arch_setup):
    with app.app_context():
        CapabilityRegistryService.register_capability(
            arch_setup["org"].id, "cap1", "Cap 1", 1, route_prefix="/api/v1/cap1"
        )
        CapabilityRegistryService.register_capability(
            arch_setup["org"].id, "cap2", "Cap 2", 2, route_prefix="/api/v1/cap2"
        )
        audit = ArchitectureConvergenceService.validate_route_ownership(arch_setup["org"].id)
        assert audit["status"] == "PASS"


def test_validate_route_ownership_fail(app, arch_setup):
    with app.app_context():
        CapabilityRegistryService.register_capability(
            arch_setup["org"].id, "cap1", "Cap 1", 1, route_prefix="/api/v1/common"
        )
        CapabilityRegistryService.register_capability(
            arch_setup["org"].id, "cap2", "Cap 2", 2, route_prefix="/api/v1/common"
        )
        audit = ArchitectureConvergenceService.validate_route_ownership(arch_setup["org"].id)
        assert audit["status"] == "FAIL"
        assert audit["collision_count"] == 1


def test_validate_service_boundaries(app, arch_setup):
    with app.app_context():
        CapabilityRegistryService.register_capability(
            arch_setup["org"].id, "cap1", "Cap 1", 1, service_reference="service_a"
        )
        CapabilityRegistryService.register_capability(
            arch_setup["org"].id, "cap2", "Cap 2", 2, service_reference="service_a"
        )
        audit = ArchitectureConvergenceService.validate_service_boundaries(arch_setup["org"].id)
        assert audit["status"] == "PASS"
        assert "cap1" in audit["shared_services"]["service_a"]


def test_convergence_summary(app, arch_setup):
    with app.app_context():
        CapabilityRegistryService.register_capability(
            arch_setup["org"].id, "cap1", "Cap 1", 1, "platform"
        )
        sumry = ArchitectureConvergenceService.convergence_summary(arch_setup["org"].id)
        assert sumry["total_capabilities"] == 1
