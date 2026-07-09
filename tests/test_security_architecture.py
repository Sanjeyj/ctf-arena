"""
Unit and Integration tests for Security Architecture.
Contains 10 test cases covering zones, boundaries, validations, boundary gaps, and tenant boundaries.
"""
import pytest
import datetime
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.architecture_zone import ArchitectureZone
from app.models.trust_boundary import TrustBoundary
from app.models.exposure_asset import ExposureAsset
from app.models.control_validation import ControlValidation
from app.services.architecture_service import ArchitectureService
from app.research.routes import create_jwt


@pytest.fixture
def arch_setup(app):
    with app.app_context():
        db.session.query(ControlValidation).delete()
        db.session.query(ExposureAsset).delete()
        db.session.query(TrustBoundary).delete()
        db.session.query(ArchitectureZone).delete()
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


def test_zone_model(app, arch_setup):
    """Test 1: ArchitectureZone fields initialization."""
    with app.app_context():
        z = ArchitectureZone(
            name="Public DMZ",
            zone_type="public",
            description="Front facing zone",
            trust_level=0.2,
            organization_id=arch_setup["o1"].id
        )
        db.session.add(z)
        db.session.commit()
        assert z.id is not None
        assert z.name == "Public DMZ"


def test_boundary_model(app, arch_setup):
    """Test 2: TrustBoundary fields initialization."""
    with app.app_context():
        z1 = ArchitectureService.create_zone("z1", "public", "z1 desc", 0.1, "high", arch_setup["o1"].id)
        z2 = ArchitectureService.create_zone("z2", "edge", "z2 desc", 0.5, "medium", arch_setup["o1"].id)
        b = TrustBoundary(
            name="dmz-edge",
            source_zone_id=z1.id,
            target_zone_id=z2.id,
            boundary_type="network",
            required_trust_score=0.8,
            control_requirements_json='["CTRL-01"]',
            organization_id=arch_setup["o1"].id
        )
        db.session.add(b)
        db.session.commit()
        assert b.id is not None
        assert b.required_trust_score == 0.8


def test_create_zone_service(app, arch_setup):
    """Test 3: ArchitectureService.create_zone."""
    with app.app_context():
        z = ArchitectureService.create_zone("app-zone", "application", "app", 0.9, "high", arch_setup["o1"].id)
        assert z.id is not None
        assert z.zone_type == "application"


def test_create_boundary_service(app, arch_setup):
    """Test 4: ArchitectureService.create_boundary."""
    with app.app_context():
        z1 = ArchitectureService.create_zone("z1", "public", "z1", 0.1, "high", arch_setup["o1"].id)
        z2 = ArchitectureService.create_zone("z2", "edge", "z2", 0.5, "medium", arch_setup["o1"].id)
        b = ArchitectureService.create_boundary("b1", z1.id, z2.id, "network", 0.6, '["CTRL-01"]', arch_setup["o1"].id)
        assert b.id is not None
        assert b.name == "b1"


def test_map_resource_to_zone(app, arch_setup):
    """Test 5: ArchitectureService.map_resource_to_zone."""
    with app.app_context():
        z = ArchitectureService.create_zone("z1", "public", "z1", 0.1, "high", arch_setup["o1"].id)
        asset = ExposureAsset(
            asset_reference_type="asset",
            asset_reference_id=1,
            display_name="Server",
            organization_id=arch_setup["o1"].id
        )
        db.session.add(asset)
        db.session.commit()

        mapped = ArchitectureService.map_resource_to_zone(asset.id, z.id, arch_setup["o1"].id)
        assert mapped is not None
        assert mapped.architecture_zone_id == z.id


def test_validate_boundary_clean(app, arch_setup):
    """Test 6: validate_boundary passes when all requirements are met."""
    with app.app_context():
        z1 = ArchitectureService.create_zone("z1", "public", "z1", 0.1, "high", arch_setup["o1"].id)
        z2 = ArchitectureService.create_zone("z2", "edge", "z2", 0.5, "medium", arch_setup["o1"].id)
        b = ArchitectureService.create_boundary("b1", z1.id, z2.id, "network", 0.6, '["CTRL-01"]', arch_setup["o1"].id)

        # Set validation result to passed
        val = ControlValidation(
            control_reference="CTRL-01",
            status="passed",
            validation_type="automated",
            expected_result="passed",
            actual_result="passed",
            tested_at=datetime.datetime.utcnow(),
            effectiveness_score=1.0,
            organization_id=arch_setup["o1"].id
        )
        db.session.add(val)
        db.session.commit()

        res = ArchitectureService.validate_boundary(b.id, arch_setup["o1"].id)
        assert res["status"] == "valid"
        assert len(res["gaps"]) == 0


def test_validate_boundary_violated(app, arch_setup):
    """Test 7: validate_boundary catches unmet controls."""
    with app.app_context():
        z1 = ArchitectureService.create_zone("z1", "public", "z1", 0.1, "high", arch_setup["o1"].id)
        z2 = ArchitectureService.create_zone("z2", "edge", "z2", 0.5, "medium", arch_setup["o1"].id)
        b = ArchitectureService.create_boundary("b1", z1.id, z2.id, "network", 0.6, '["CTRL-01"]', arch_setup["o1"].id)

        # No validation exists in database -> treated as gap
        res = ArchitectureService.validate_boundary(b.id, arch_setup["o1"].id)
        assert res["status"] == "violated"
        assert "CTRL-01" in res["gaps"]


def test_identify_boundary_gaps(app, arch_setup):
    """Test 8: identify_boundary_gaps returns violated boundaries details."""
    with app.app_context():
        z1 = ArchitectureService.create_zone("z1", "public", "z1", 0.1, "high", arch_setup["o1"].id)
        z2 = ArchitectureService.create_zone("z2", "edge", "z2", 0.5, "medium", arch_setup["o1"].id)
        ArchitectureService.create_boundary("b1", z1.id, z2.id, "network", 0.6, '["CTRL-01"]', arch_setup["o1"].id)

        gaps = ArchitectureService.identify_boundary_gaps(arch_setup["o1"].id)
        assert len(gaps) == 1
        assert gaps[0]["boundary_name"] == "b1"


def test_architecture_summary(app, arch_setup):
    """Test 9: architecture_summary metrics."""
    with app.app_context():
        z1 = ArchitectureService.create_zone("z1", "public", "z1", 0.1, "high", arch_setup["o1"].id)
        z2 = ArchitectureService.create_zone("z2", "edge", "z2", 0.5, "medium", arch_setup["o1"].id)
        ArchitectureService.create_boundary("b1", z1.id, z2.id, "network", 0.6, '[]', arch_setup["o1"].id)

        summary = ArchitectureService.architecture_summary(arch_setup["o1"].id)
        assert summary["total_zones"] == 2
        assert summary["total_boundaries"] == 1
        assert summary["boundary_violations"] == 0


def test_tenant_boundary_isolation(app, arch_setup):
    """Test 10: Zone validation ignores records from other tenants."""
    with app.app_context():
        z1 = ArchitectureService.create_zone("z1", "public", "z1", 0.1, "high", arch_setup["o1"].id)
        z2 = ArchitectureService.create_zone("z2", "edge", "z2", 0.5, "medium", arch_setup["o1"].id)
        b = ArchitectureService.create_boundary("b1", z1.id, z2.id, "network", 0.6, '["CTRL-01"]', arch_setup["o1"].id)

        # Set validation for Tenant 2
        val = ControlValidation(
            control_reference="CTRL-01",
            status="passed",
            validation_type="automated",
            expected_result="passed",
            actual_result="passed",
            tested_at=datetime.datetime.utcnow(),
            effectiveness_score=1.0,
            organization_id=arch_setup["o2"].id
        )
        db.session.add(val)
        db.session.commit()

        # Validation for Tenant 1 should still show violated because the valid validation was for Tenant 2
        res = ArchitectureService.validate_boundary(b.id, arch_setup["o1"].id)
        assert res["status"] == "violated"
