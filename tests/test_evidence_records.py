"""
Unit and Integration tests for Phase 31 — Evidence Records.
Contains 10 test cases covering EvidenceRecord model, evidence collection, redaction rules, SHA-256 integrity verification, and manifests export.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.evidence_record import EvidenceRecord
from app.services.evidence_service import EvidenceService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def ev_setup(app):
    """Fixture for evidence tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(EvidenceRecord).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Ev Org", slug="ev-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="ev_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Ev Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "ev_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_evidence_record_creation(app, ev_setup):
    """Test 1: EvidenceRecord model fields."""
    with app.app_context():
        import datetime
        rec = EvidenceRecord(
            evidence_type="wargame_run",
            source_module="scenario_engine",
            resource_type="universe_simulation",
            resource_id="12",
            summary="Simulation run succeeded.",
            integrity_hash="abc123hash",
            collected_at=datetime.datetime.utcnow(),
            status="valid",
            organization_id=ev_setup["org"].id
        )
        db.session.add(rec)
        db.session.commit()
        assert rec.id is not None
        assert rec.evidence_type == "wargame_run"
        assert rec.integrity_hash == "abc123hash"


def test_evidence_record_repr(app, ev_setup):
    """Test 2: EvidenceRecord repr format."""
    with app.app_context():
        rec = EvidenceRecord(evidence_type="policy_check", status="tampered", organization_id=ev_setup["org"].id)
        assert "policy_check" in repr(rec)
        assert "tampered" in repr(rec)


def test_evidence_record_to_dict(app, ev_setup):
    """Test 3: EvidenceRecord serialization."""
    with app.app_context():
        import datetime
        now = datetime.datetime.utcnow()
        rec = EvidenceRecord(
            evidence_type="feature_change",
            source_module="feature_flag",
            resource_type="platform_feature_flag",
            resource_id="5",
            summary="Flag enabled.",
            integrity_hash="hash99",
            collected_at=now,
            status="valid",
            organization_id=ev_setup["org"].id
        )
        d = rec.to_dict()
        assert d["evidence_type"] == "feature_change"
        assert d["integrity_hash"] == "hash99"
        assert d["collected_at"] == now.isoformat()


def test_evidence_service_redact_password(app, ev_setup):
    """Test 4: Redaction rules masks passwords."""
    summary = "User admin updated password=SecretAdmin123."
    redacted = EvidenceService.redact_secrets(summary)
    assert "SecretAdmin123" not in redacted
    assert "password=[REDACTED]" in redacted


def test_evidence_service_redact_auth_header(app, ev_setup):
    """Test 5: Redaction rules masks authorization headers."""
    summary = "API request with Authorization: Bearer eyJhbGciOiJIUzI1NiJ9."
    redacted = EvidenceService.redact_secrets(summary)
    assert "eyJhbGciOiJIUzI1NiJ9" not in redacted
    assert "Bearer [REDACTED]" in redacted


def test_evidence_service_redact_api_key(app, ev_setup):
    """Test 6: Redaction rules masks API keys and tokens."""
    summary = "Swapped models using api_key=sk-1234567890."
    redacted = EvidenceService.redact_secrets(summary)
    assert "sk-1234567890" not in redacted
    assert "api_key=[REDACTED]" in redacted


def test_evidence_service_redact_flags(app, ev_setup):
    """Test 7: Redaction rules masks CTF flags patterns."""
    summary = "Solved challenge flag{solved_arena_flag_value}."
    redacted = EvidenceService.redact_secrets(summary)
    assert "solved_arena_flag_value" not in redacted
    assert "flag=[REDACTED]" in redacted


def test_evidence_service_collect_and_verify(app, ev_setup):
    """Test 8: EvidenceService collects and validates hash integrity."""
    with app.app_context():
        rec = EvidenceService.collect("policy_check", "control_policy", "control_policy", "2", "Run checks on readiness score=0.85.", ev_setup["org"].id)
        assert rec.id is not None
        assert EvidenceService.verify_integrity(rec.id, ev_setup["org"].id) is True


def test_evidence_service_verify_integrity_tampered(app, ev_setup):
    """Test 9: Integrity check fails if metadata record was modified in database."""
    with app.app_context():
        rec = EvidenceService.collect("policy_check", "control_policy", "control_policy", "2", "Original summary.", ev_setup["org"].id)
        
        # Tamper the record summary in DB without updating the hash
        rec.summary = "Tampered summary."
        db.session.commit()

        assert EvidenceService.verify_integrity(rec.id, ev_setup["org"].id) is False


def test_api_collect_evidence(client, ev_setup):
    """Test 10: POST /api/v1/control-plane/evidence REST endpoint."""
    resp = client.post(
        f'/api/v1/control-plane/evidence?org_id={ev_setup["org"].id}',
        json={
            'evidence_type': 'wargame_run',
            'source_module': 'scenario_engine',
            'resource_type': 'universe_simulation',
            'resource_id': '10',
            'summary': 'Wargaming run completed for flag{test_flag_value}'
        },
        headers=ev_setup["headers"]
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data["status"] == "valid"
    assert "flag=[REDACTED]" in data["summary"]
