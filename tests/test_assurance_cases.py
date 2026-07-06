"""
Unit and Integration tests for Assurance Cases.
Contains 10 test cases covering AssuranceCase model, evidence linking, confidence scoring, contradictory penalty factors, and cross-tenant rejects.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.assurance_case import AssuranceCase
from app.models.assurance_evidence_link import AssuranceEvidenceLink
from app.models.evidence_record import EvidenceRecord
from app.services.assurance_service import AssuranceService
from app.services.evidence_service import EvidenceService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def case_setup(app):
    """Fixture for assurance case tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(AssuranceEvidenceLink).delete()
        db.session.query(AssuranceCase).delete()
        db.session.query(EvidenceRecord).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        o1 = Organization(name="C Org 1", slug="c-org-1", plan_type="enterprise")
        o2 = Organization(name="C Org 2", slug="c-org-2", plan_type="enterprise")
        db.session.add_all([o1, o2])
        db.session.commit()

        # Phase 31 Evidence Service collect
        ev = EvidenceService.collect("policy_check", "control_plane", "policy", "1", "Policy checks passed.", o1.id)

        try:
            UserRepository.create(
                username="case_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Case Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "case_admin"}, secret)

        yield {
            "o1": o1,
            "o2": o2,
            "ev": ev,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_assurance_case_model_fields(app, case_setup):
    """Test 1: AssuranceCase model fields."""
    with app.app_context():
        case = AssuranceCase(
            title="SOC Ingestion Assurance",
            claim="Logs are ingested without data loss.",
            scope="SOC",
            confidence_score=90.0,
            status="supported",
            owner="Alice",
            organization_id=case_setup["o1"].id
        )
        db.session.add(case)
        db.session.commit()
        assert case.id is not None
        assert case.title == "SOC Ingestion Assurance"
        assert case.status == "supported"


def test_assurance_case_repr(app, case_setup):
    """Test 2: AssuranceCase repr format."""
    with app.app_context():
        case = AssuranceCase(title="LMS Claim", status="under_review", organization_id=case_setup["o1"].id)
        assert "LMS Claim" in repr(case)
        assert "under_review" in repr(case)


def test_assurance_evidence_link_model_fields(app, case_setup):
    """Test 3: AssuranceEvidenceLink model fields."""
    with app.app_context():
        case = AssuranceService.create_case("CTI Claim", "Threat intel is validated.", case_setup["o1"].id)
        link = AssuranceEvidenceLink(
            assurance_case_id=case.id,
            evidence_record_id=case_setup["ev"].id,
            relationship_type="supports",
            weight=0.8,
            validation_status="valid",
            organization_id=case_setup["o1"].id
        )
        db.session.add(link)
        db.session.commit()
        assert link.id is not None
        assert link.relationship_type == "supports"
        assert link.weight == 0.8


def test_assurance_service_create_case(app, case_setup):
    """Test 4: Service creates case claims."""
    with app.app_context():
        case = AssuranceService.create_case("Verification Case", "Continuous controls checked.", case_setup["o1"].id, owner="Bob")
        assert case.id is not None
        assert case.owner == "Bob"
        assert case.status == "draft"


def test_assurance_service_attach_evidence(app, case_setup):
    """Test 5: Attach evidence maps successfully for same tenant."""
    with app.app_context():
        case = AssuranceService.create_case("TCase", "Claim", case_setup["o1"].id)
        link = AssuranceService.attach_evidence(case.id, case_setup["ev"].id, "supports", 0.95, case_setup["o1"].id)
        assert link.id is not None
        assert link.weight == 0.95


def test_assurance_service_cross_tenant_link_rejection(app, case_setup):
    """Test 6: Reject cross-tenant evidence link mappings."""
    with app.app_context():
        case = AssuranceService.create_case("TCase", "Claim", case_setup["o1"].id)
        # Attempt to link using Tenant 2 org_id should fail and return None
        link = AssuranceService.attach_evidence(case.id, case_setup["ev"].id, "supports", 0.95, case_setup["o2"].id)
        assert link is None


def test_assurance_case_evaluation_supported(app, case_setup):
    """Test 7: Evaluation computes confidence score based on link weight."""
    with app.app_context():
        case = AssuranceService.create_case("Overall Trust", "Security rules enforced.", case_setup["o1"].id)
        AssuranceService.attach_evidence(case.id, case_setup["ev"].id, "supports", 0.9, case_setup["o1"].id)
        
        confidence = AssuranceService.evaluate_case(case.id, case_setup["o1"].id)
        # 0.9 supports -> 90.0 confidence
        assert confidence == 90.0
        assert case.status == "supported"


def test_assurance_case_evaluation_contradictory_penalty(app, case_setup):
    """Test 8: Contradictory evidence linkage triggers heavy penalty factor."""
    with app.app_context():
        case = AssuranceService.create_case("Security Claim", "Zero trust active.", case_setup["o1"].id)
        
        # Add supporting evidence (weight=0.9 -> 90.0 confidence)
        AssuranceService.attach_evidence(case.id, case_setup["ev"].id, "supports", 0.9, case_setup["o1"].id)
        
        # Add contradictory evidence (triggers 20% multiplier penalty)
        ev2 = EvidenceService.collect("incident_log", "soc", "case", "2", "Anomaly alert detected.", case_setup["o1"].id)
        AssuranceService.attach_evidence(case.id, ev2.id, "contradicts", 0.5, case_setup["o1"].id)

        confidence = AssuranceService.evaluate_case(case.id, case_setup["o1"].id)
        # Expected: 90.0 * 0.20 = 18.00
        assert confidence == 18.00
        assert case.status == "insufficient_evidence"


def test_assurance_case_evidence_gaps(app, case_setup):
    """Test 9: Gaps helper identifies missing or weak weights."""
    with app.app_context():
        case = AssuranceService.create_case("Weak Claim", "Unverified claims.", case_setup["o1"].id)
        
        # Check empty case gaps
        gaps1 = AssuranceService.identify_evidence_gaps(case.id, case_setup["o1"].id)
        assert len(gaps1) >= 1
        assert "No compliance evidence" in gaps1[0]

        # Check weak support gap
        AssuranceService.attach_evidence(case.id, case_setup["ev"].id, "supports", 0.3, case_setup["o1"].id)
        gaps2 = AssuranceService.identify_evidence_gaps(case.id, case_setup["o1"].id)
        assert "Supporting evidence total weight is low" in gaps2[0]


def test_api_create_assurance_case(client, case_setup):
    """Test 10: POST /api/v1/assurance/cases REST endpoint."""
    resp = client.post(
        f'/api/v1/assurance/cases?org_id={case_setup["o1"].id}',
        json={
            'title': 'API claim',
            'claim': 'Vulnerabilities resolved before release.'
        },
        headers=case_setup["headers"]
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data["title"] == "API claim"
    assert data["status"] == "draft"
