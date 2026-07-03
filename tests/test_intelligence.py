"""
Unit and Integration tests for Phase 27 Global Security Intelligence Network — Intelligence.
Contains 10 test cases covering models, services, and endpoints.
"""
import pytest
import json
from app.extensions import db
from app.models.organization import Organization
from app.models.global_threat_feed import GlobalThreatFeed
from app.models.intelligence_report import IntelligenceReport
from app.services.intelligence_service import IntelligenceService
from app.research.routes import create_jwt
from app.repositories.user_repository import UserRepository
from app.services.auth_service import hash_password


@pytest.fixture
def intel_setup(app):
    """Fixture for intelligence tests."""
    with app.app_context():
        from app.repositories.role_repository import RoleRepository
        from app.repositories.permission_repository import PermissionRepository
        RoleRepository.setup_default_roles()
        PermissionRepository.setup_default_permissions_and_roles_map()

        db.session.query(GlobalThreatFeed).delete()
        db.session.query(IntelligenceReport).delete()
        db.session.query(Organization).delete()
        db.session.commit()

        org = Organization(name="Intel Org", slug="intel-org", plan_type="enterprise")
        db.session.add(org)
        db.session.commit()

        try:
            UserRepository.create(
                username="intel_admin",
                password_hash=hash_password("AdminPass123!"),
                display_name="Intel Admin",
                role_name="Admin"
            )
        except Exception:
            pass

        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "intel_admin"}, secret)

        yield {
            "org": org,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


def test_global_threat_feed_creation(app, intel_setup):
    """Test 1: GlobalThreatFeed model fields."""
    with app.app_context():
        feed = GlobalThreatFeed(
            name="OSINT-Threats",
            source="https://example.com/feed",
            trust_score=0.85,
            status="active",
            update_frequency="hourly",
            organization_id=intel_setup["org"].id
        )
        db.session.add(feed)
        db.session.commit()
        assert feed.id is not None
        assert feed.name == "OSINT-Threats"
        assert feed.trust_score == 0.85


def test_global_threat_feed_to_dict(app, intel_setup):
    """Test 2: GlobalThreatFeed serialization."""
    with app.app_context():
        feed = GlobalThreatFeed(
            name="SANS-ISC",
            source="https://example.com/sans",
            trust_score=0.9,
            status="active",
            update_frequency="daily",
            organization_id=intel_setup["org"].id
        )
        db.session.add(feed)
        db.session.commit()
        d = feed.to_dict()
        assert d["name"] == "SANS-ISC"
        assert d["trust_score"] == 0.9
        assert d["status"] == "active"


def test_intelligence_report_creation(app, intel_setup):
    """Test 3: IntelligenceReport model fields."""
    with app.app_context():
        report = IntelligenceReport(
            title="APT29 Phishing Campaign",
            severity="high",
            source="Malware Patrol",
            confidence=0.88,
            summary="New wave targeting government agencies.",
            organization_id=intel_setup["org"].id
        )
        db.session.add(report)
        db.session.commit()
        assert report.id is not None
        assert report.title == "APT29 Phishing Campaign"
        assert report.severity == "high"


def test_intelligence_report_to_dict(app, intel_setup):
    """Test 4: IntelligenceReport serialization."""
    with app.app_context():
        report = IntelligenceReport(
            title="WannaCry Variant",
            severity="critical",
            source="AlienVault OTX",
            confidence=0.95,
            summary="Ransomware propagation via SMB.",
            organization_id=intel_setup["org"].id
        )
        db.session.add(report)
        db.session.commit()
        d = report.to_dict()
        assert d["title"] == "WannaCry Variant"
        assert d["severity"] == "critical"
        assert d["confidence"] == 0.95


def test_intelligence_service_normalize(app):
    """Test 5: IntelligenceService normalization logic."""
    raw = {
        "title": "Log4Shell Exploit",
        "level": "Critical",
        "provider": "CISA",
        "score": 0.99,
        "description": "RCE vulnerability in Apache Log4j."
    }
    norm = IntelligenceService.normalize(raw)
    assert norm["title"] == "Log4Shell Exploit"
    assert norm["severity"] == "critical"
    assert norm["source"] == "CISA"
    assert norm["confidence"] == 0.99
    assert norm["summary"] == "RCE vulnerability in Apache Log4j."


def test_intelligence_service_ingest(app, intel_setup):
    """Test 6: Ingestion of raw intelligence payload."""
    raw = {
        "title": "Apache CVE-2026",
        "severity": "high",
        "source": "OpenSource",
        "confidence": 0.8,
        "summary": "Path traversal issue."
    }
    with app.app_context():
        report = IntelligenceService.ingest(raw, organization_id=intel_setup["org"].id)
        assert report.id is not None
        assert report.title == "Apache CVE-2026"
        assert report.organization_id == intel_setup["org"].id


def test_intelligence_service_correlate(app, intel_setup):
    """Test 7: Correlation of reports."""
    with app.app_context():
        r1 = IntelligenceReport(title="Exploit A", severity="high", source="S1", confidence=0.8, organization_id=intel_setup["org"].id)
        r2 = IntelligenceReport(title="Exploit B", severity="high", source="S2", confidence=0.7, organization_id=intel_setup["org"].id)
        r3 = IntelligenceReport(title="Exploit C", severity="low", source="S3", confidence=0.6, organization_id=intel_setup["org"].id)
        db.session.add_all([r1, r2, r3])
        db.session.commit()

        correlated = IntelligenceService.correlate(r1.id)
        assert len(correlated) >= 1
        assert correlated[0]["title"] == "Exploit B"


def test_intelligence_service_list_reports(app, intel_setup):
    """Test 8: Listing reports with organization filtering."""
    with app.app_context():
        r1 = IntelligenceReport(title="R1", severity="medium", source="S1", organization_id=intel_setup["org"].id)
        r2 = IntelligenceReport(title="R2", severity="low", source="S2", organization_id=999)
        db.session.add_all([r1, r2])
        db.session.commit()

        all_reports = IntelligenceService.list_reports()
        assert len(all_reports) >= 2

        filtered = IntelligenceService.list_reports(org_id=intel_setup["org"].id)
        assert len(filtered) == 1
        assert filtered[0].title == "R1"


def test_api_get_intelligence(client, intel_setup):
    """Test 9: GET /api/v1/intelligence returns ingested reports."""
    with client.application.app_context():
        r = IntelligenceReport(title="API Report", severity="medium", source="API", organization_id=intel_setup["org"].id)
        db.session.add(r)
        db.session.commit()

    resp = client.get(
        f'/api/v1/intelligence?org_id={intel_setup["org"].id}',
        headers=intel_setup["headers"]
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) >= 1
    assert data[0]["title"] == "API Report"


def test_api_post_intelligence(client, intel_setup):
    """Test 10: POST /api/v1/intelligence registers new report."""
    resp = client.post(
        '/api/v1/intelligence',
        json={
            'title': 'Zero-Day exploit',
            'severity': 'critical',
            'source': 'Shadow Brokers',
            'confidence': 0.99,
            'summary': 'New zero-day exploit leaked.',
            'organization_id': intel_setup["org"].id
        },
        headers=intel_setup["headers"]
    )
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data["title"] == "Zero-Day exploit"
    assert data["severity"] == "critical"
