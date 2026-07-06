"""
Unit and Integration tests for Software Attestations.
Contains 10 test cases covering SoftwareAttestation model, attestations registry, SHA-256 digest validation, and tenant isolation constraints.
"""
import pytest
import json
import hashlib
from app.extensions import db
from app.models.organization import Organization
from app.models.software_attestation import SoftwareAttestation
from app.services.attestation_service import AttestationService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def att_setup(app):
    """Fixture for attestation tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(SoftwareAttestation).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="A Org 1", slug="a-org-1", plan_type="enterprise")
        o2 = Organization(name="A Org 2", slug="a-org-2", plan_type="enterprise")
        db.session.add_all([o1, o2])
        db.session.commit()

        digest = hashlib.sha256(b"artifact_data_mock").hexdigest()

        try:
            UserRepository.create(
                username="att_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Att Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "att_admin"}, secret)

        yield {
            "o1": o1,
            "o2": o2,
            "digest": digest,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_software_attestation_model_fields(app, att_setup):
    """Test 1: SoftwareAttestation model fields."""
    with app.app_context():
        att = SoftwareAttestation(
            artifact_name="CTF-Engine",
            artifact_version="2.4.0",
            artifact_digest=att_setup["digest"],
            builder_identity="builder@ci.local",
            build_environment="github-actions",
            attestation_type="slsa",
            verification_status="valid",
            organization_id=att_setup["o1"].id
        )
        db.session.add(att)
        db.session.commit()
        assert att.id is not None
        assert att.artifact_name == "CTF-Engine"
        assert att.artifact_digest == att_setup["digest"]


def test_software_attestation_repr(app, att_setup):
    """Test 2: SoftwareAttestation repr format."""
    with app.app_context():
        att = SoftwareAttestation(artifact_name="Range-Core", verification_status="invalid", organization_id=att_setup["o1"].id)
        assert "Range-Core" in repr(att)
        assert "invalid" in repr(att)


def test_software_attestation_to_dict(app, att_setup):
    """Test 3: SoftwareAttestation serialization."""
    with app.app_context():
        att = SoftwareAttestation(
            artifact_name="Portal",
            artifact_version="1.0",
            artifact_digest="digest123",
            metadata_json='{"provenance": "verified"}',
            organization_id=att_setup["o1"].id
        )
        d = att.to_dict()
        assert d["artifact_name"] == "Portal"
        assert d["metadata"] == {"provenance": "verified"}


def test_attestation_service_register(app, att_setup):
    """Test 4: Service registers attestation successfully."""
    with app.app_context():
        att = AttestationService.register_attestation(
            "API-Gate", "1.2.0", att_setup["digest"], att_setup["o1"].id, "CI-Runner", "GitLab"
        )
        assert att.id is not None
        assert att.builder_identity == "CI-Runner"
        assert att.verification_status == "valid"


def test_attestation_service_verify_digest_success(app, att_setup):
    """Test 5: Digest verification passes with identical SHA-256 hash."""
    with app.app_context():
        att = AttestationService.register_attestation("Pkg", "1.0", att_setup["digest"], att_setup["o1"].id)
        assert AttestationService.verify_digest(att.id, att_setup["digest"], att_setup["o1"].id) is True


def test_attestation_service_verify_digest_failure(app, att_setup):
    """Test 6: Digest verification fails and invalidates status on mismatch."""
    with app.app_context():
        att = AttestationService.register_attestation("Pkg", "1.0", att_setup["digest"], att_setup["o1"].id)
        assert AttestationService.verify_digest(att.id, "different_hash_value", att_setup["o1"].id) is False
        
        # Status must transition to invalid
        db.session.refresh(att)
        assert att.verification_status == "invalid"


def test_attestation_service_verify_metadata(app, att_setup):
    """Test 7: Metadata checks verify builder properties presence."""
    with app.app_context():
        att1 = AttestationService.register_attestation("Pkg1", "1.0", att_setup["digest"], att_setup["o1"].id, "CI", "Runner")
        att2 = AttestationService.register_attestation("Pkg2", "1.0", att_setup["digest"], att_setup["o1"].id)
        
        assert AttestationService.verify_metadata(att1.id, att_setup["o1"].id) is True
        assert AttestationService.verify_metadata(att2.id, att_setup["o1"].id) is False


def test_attestation_service_confidence(app, att_setup):
    """Test 8: Confidence calculations apply correct weights."""
    with app.app_context():
        # Complete metadata -> 100
        att1 = AttestationService.register_attestation("Pkg1", "1.0", att_setup["digest"], att_setup["o1"].id, "CI", "Runner")
        assert AttestationService.calculate_confidence(att1.id, att_setup["o1"].id) == 100.0

        # Missing environment -> 70
        att2 = AttestationService.register_attestation("Pkg2", "1.0", att_setup["digest"], att_setup["o1"].id, "CI")
        assert AttestationService.calculate_confidence(att2.id, att_setup["o1"].id) == 70.0


def test_attestation_service_tenant_isolation(app, att_setup):
    """Test 9: Attestation verification rejects cross-tenant parameters lookup."""
    with app.app_context():
        att = AttestationService.register_attestation("Pkg", "1.0", att_setup["digest"], att_setup["o1"].id)
        # Verification using Tenant 2 org_id should return False
        assert AttestationService.verify_digest(att.id, att_setup["digest"], att_setup["o2"].id) is False


def test_api_register_attestation(client, att_setup):
    """Test 10: POST /api/v1/assurance/attestations REST endpoint."""
    resp = client.post(
        f'/api/v1/assurance/attestations?org_id={att_setup["o1"].id}',
        json={
            'artifact_name': 'Core-Service',
            'artifact_version': '1.0.0',
            'artifact_digest': att_setup["digest"],
            'builder_identity': 'CI-Pipeline'
        },
        headers=att_setup["headers"]
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data["artifact_name"] == "Core-Service"
    assert data["builder_identity"] == "CI-Pipeline"
