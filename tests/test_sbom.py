"""
Unit and Integration tests for SBOM records.
Contains 10 test cases covering SBOMRecord model, SPDX/CycloneDX formats registration, validate metadata offline, risk summaries, version compares, and REST APIs.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.sbom_record import SBOMRecord
from app.services.sbom_service import SBOMService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def sbom_setup(app):
    """Fixture for SBOM tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(SBOMRecord).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="S Org 1", slug="s-org-1", plan_type="enterprise")
        o2 = Organization(name="S Org 2", slug="s-org-2", plan_type="enterprise")
        db.session.add_all([o1, o2])
        db.session.commit()

        try:
            UserRepository.create(
                username="sbom_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="SBOM Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "sbom_admin"}, secret)

        yield {
            "o1": o1,
            "o2": o2,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_sbom_record_model_fields(app, sbom_setup):
    """Test 1: SBOMRecord model fields."""
    with app.app_context():
        rec = SBOMRecord(
            artifact_name="CTF-Web",
            artifact_version="1.0.0",
            format_type="CycloneDX",
            component_count=15,
            dependency_count=45,
            known_risk_count=2,
            document_hash="hash123",
            organization_id=sbom_setup["o1"].id
        )
        db.session.add(rec)
        db.session.commit()
        assert rec.id is not None
        assert rec.artifact_name == "CTF-Web"
        assert rec.component_count == 15


def test_sbom_record_repr(app, sbom_setup):
    """Test 2: SBOMRecord repr format."""
    with app.app_context():
        rec = SBOMRecord(artifact_name="Range-API", format_type="SPDX", organization_id=sbom_setup["o1"].id)
        assert "Range-API" in repr(rec)
        assert "SPDX" in repr(rec)


def test_sbom_record_to_dict(app, sbom_setup):
    """Test 3: SBOMRecord serialization."""
    with app.app_context():
        rec = SBOMRecord(
            artifact_name="Dashboard",
            artifact_version="3.0",
            format_type="CycloneDX",
            metadata_json='{"generator": "Syft"}',
            organization_id=sbom_setup["o1"].id
        )
        d = rec.to_dict()
        assert d["artifact_name"] == "Dashboard"
        assert d["metadata"] == {"generator": "Syft"}


def test_sbom_service_register(app, sbom_setup):
    """Test 4: Service registers CycloneDX SBOM successfully."""
    with app.app_context():
        metadata = {
            'components': [{'name': 'react'}, {'name': 'lodash'}],
            'dependencies': [{'ref': 'react'}],
            'risk_count': 1
        }
        rec = SBOMService.register("Front-End", "2.0.0", "CycloneDX", "hashFront", sbom_setup["o1"].id, metadata)
        assert rec.id is not None
        assert rec.component_count == 2
        assert rec.dependency_count == 1
        assert rec.known_risk_count == 1


def test_sbom_service_validate_metadata_valid(app, sbom_setup):
    """Test 5: Validate metadata parses successfully for valid formats."""
    with app.app_context():
        rec = SBOMService.register("Front-End", "2.0.0", "CycloneDX", "hashFront", sbom_setup["o1"].id, {'components': []})
        assert SBOMService.validate_metadata(rec.id, sbom_setup["o1"].id) is True


def test_sbom_service_validate_metadata_invalid_format(app, sbom_setup):
    """Test 6: Validate metadata returns False for unknown format types."""
    with app.app_context():
        rec = SBOMService.register("Front-End", "2.0.0", "unknown_format", "hashFront", sbom_setup["o1"].id, {'components': []})
        assert SBOMService.validate_metadata(rec.id, sbom_setup["o1"].id) is False


def test_sbom_service_calculate_risk_summary(app, sbom_setup):
    """Test 7: Risk calculation correctly sets levels and score indices."""
    with app.app_context():
        rec1 = SBOMService.register("Pkg1", "1.0", "SPDX", "h1", sbom_setup["o1"].id, {'risk_count': 0})
        rec2 = SBOMService.register("Pkg2", "1.0", "SPDX", "h2", sbom_setup["o1"].id, {'risk_count': 4})
        rec3 = SBOMService.register("Pkg3", "1.0", "SPDX", "h3", sbom_setup["o1"].id, {'risk_count': 10})

        r1 = SBOMService.calculate_risk_summary(rec1.id, sbom_setup["o1"].id)
        r2 = SBOMService.calculate_risk_summary(rec2.id, sbom_setup["o1"].id)
        r3 = SBOMService.calculate_risk_summary(rec3.id, sbom_setup["o1"].id)

        assert r1["risk_level"] == "low"
        assert r2["risk_level"] == "high"
        assert r3["risk_level"] == "critical"


def test_sbom_service_compare_versions(app, sbom_setup):
    """Test 8: Compare versions returns list ordered descending."""
    with app.app_context():
        SBOMService.register("Lib", "1.0.0", "SPDX", "h1", sbom_setup["o1"].id, {})
        SBOMService.register("Lib", "2.0.0", "SPDX", "h2", sbom_setup["o1"].id, {})

        versions = SBOMService.compare_versions("Lib", sbom_setup["o1"].id)
        assert len(versions) == 2
        assert versions[0]["artifact_version"] == "2.0.0"


def test_sbom_service_tenant_isolation(app, sbom_setup):
    """Test 9: SBOM verification rejects cross-tenant parameters lookup."""
    with app.app_context():
        rec = SBOMService.register("Pkg", "1.0", "SPDX", "hash", sbom_setup["o1"].id, {})
        # Verification using Tenant 2 org_id should return False
        assert SBOMService.validate_metadata(rec.id, sbom_setup["o2"].id) is False


def test_api_register_sbom(client, sbom_setup):
    """Test 10: POST /api/v1/assurance/sbom REST endpoint."""
    resp = client.post(
        f'/api/v1/assurance/sbom?org_id={sbom_setup["o1"].id}',
        json={
            'artifact_name': 'Backend-Core',
            'artifact_version': '4.1.0',
            'format_type': 'CycloneDX',
            'document_hash': 'documentHash123',
            'metadata': {
                'components': [{'name': 'flask'}, {'name': 'sqlalchemy'}],
                'dependencies': [{'ref': 'flask'}],
                'risk_count': 0
            }
        },
        headers=sbom_setup["headers"]
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data["artifact_name"] == "Backend-Core"
    assert data["component_count"] == 2
