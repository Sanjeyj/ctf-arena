"""
Tests for Phase 19 — Security Research & Cyber Threat Intelligence (CTI).
Contains 25+ assertions targeting actor CRUD, campaigns, malware metadata extraction,
entropy, reports, AI assistant, hook triggers, and JWT-authenticated APIs.
"""
import pytest
import json
import datetime
from app.extensions import db
from app.models.threat_actor import ThreatActor
from app.models.campaign import Campaign
from app.models.malware_family import MalwareFamily
from app.models.malware_sample import MalwareSample
from app.models.research_report import ResearchReport
from app.models.yara_repository import YaraRepository
from app.models.sigma_repository import SigmaRepository
from app.models.attack_navigator import AttackNavigator
from app.models.organization import Organization

from app.services.threat_actor_service import ThreatActorService
from app.services.campaign_service import CampaignService
from app.services.malware_service import MalwareService
from app.services.research_service import ResearchService
from app.services.research_ai_service import ResearchAIService
from app.services.navigator_service import NavigatorService
from app.services.hook_service import HookService
from app.research.routes import create_jwt


@pytest.fixture
def cti_setup(app):
    """Create a mock enterprise organization and retrieve JWT token."""
    with app.app_context():
        # Clean existing tables if needed
        db.session.query(Campaign).delete()
        db.session.query(ThreatActor).delete()
        db.session.query(MalwareSample).delete()
        db.session.query(MalwareFamily).delete()
        db.session.query(ResearchReport).delete()
        db.session.commit()

        org = Organization(name="CTI Research Org", slug="cti-research-org", plan_type="enterprise", status="active")
        db.session.add(org)
        db.session.commit()

        # Create JWT token
        secret = app.config.get('SECRET_KEY', 'default_secret')
        token = create_jwt({"username": "cti_analyst", "org_id": org.id}, secret)

        yield {
            "org": org,
            "jwt_token": token,
            "headers": {"Authorization": f"Bearer {token}"}
        }


# ─────────────────────────────────────────────────────────────────────────────
# Threat Actor CRUD & Campaign Mapping Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_actor_crud(app, cti_setup):
    """Test full CRUD operations for Threat Actor profiles."""
    with app.app_context():
        org = cti_setup['org']
        
        # 1. Create actor
        actor = ThreatActorService.create_actor(
            name="APT28",
            aliases="Fancy Bear, Sofacy",
            country="Russia",
            motivation="espionage",
            sophistication="state-sponsored",
            org_id=org.id
        )
        assert actor.id is not None
        assert actor.name == "APT28"
        assert actor.country == "Russia"
        assert "Sofacy" in actor.aliases
        
        # 2. List actors
        actors = ThreatActorService.list_actors(org_id=org.id)
        assert len(actors) == 1
        assert actors[0].name == "APT28"

        # 3. Read actor
        fetched = ThreatActorService.get_actor(actor.id)
        assert fetched is not None
        assert fetched.motivation == "espionage"

        # 4. Update actor
        updated = ThreatActorService.update_actor(actor.id, country="Unknown Origin", sophistication="high")
        assert updated.country == "Unknown Origin"
        assert updated.sophistication == "high"

        # 5. Delete actor
        deleted = ThreatActorService.delete_actor(actor.id)
        assert deleted is True
        assert ThreatActorService.get_actor(actor.id) is None


def test_campaign_relationships(app, cti_setup):
    """Test campaign creation and relationships to threat actor profiles."""
    with app.app_context():
        org = cti_setup['org']
        actor = ThreatActorService.create_actor("APT29", country="Russia", org_id=org.id)
        
        # Create Campaign
        campaign = CampaignService.create_campaign(
            actor_id=actor.id,
            name="Operation Windigo",
            start_date=datetime.datetime.utcnow(),
            target_sector="Financial Services",
            description="Spearphishing targeting banking systems",
            malware_used="Cobalt Strike, CozyDuke",
            techniques_used="T1190, T1078",
            org_id=org.id
        )
        assert campaign.id is not None
        assert campaign.actor_id == actor.id
        assert campaign.target_sector == "Financial Services"
        assert "CozyDuke" in campaign.malware_used
        assert "T1190" in campaign.techniques_used

        # Check threat actor back-reference relationship
        assert actor.campaigns.count() == 1
        assert actor.campaigns.first().name == "Operation Windigo"

        # List campaigns
        campaigns = CampaignService.list_campaigns(org_id=org.id)
        assert len(campaigns) == 1
        assert campaigns[0].name == "Operation Windigo"


# ─────────────────────────────────────────────────────────────────────────────
# Static Malware Analysis & Entropy Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_entropy_calculation(app):
    """Test Shannon entropy algorithm returns correct density ranges."""
    # Test flat bytes (0.0 entropy)
    flat_data = b"\x00\x00\x00\x00\x00\x00\x00\x00"
    flat_entropy = MalwareService.calculate_entropy(flat_data)
    assert flat_entropy == 0.0

    # Test random uniform bytes (8.0 maximum entropy potential)
    uniform_data = bytes(range(256))
    uniform_entropy = MalwareService.calculate_entropy(uniform_data)
    assert uniform_entropy == 8.0


def test_malware_metadata_extraction(app, cti_setup):
    """Test static analysis metadata, strings extraction, and PE header mocks."""
    with app.app_context():
        org = cti_setup['org']
        sample_payload = b"MZ\x90\x00\x03\x00ThisIsSomePrintableStringForTestingInsideThePayloadKERNEL32.dllVirtualAlloc"
        
        analysis = MalwareService.analyze_sample("payload.exe", sample_payload)
        assert analysis['hashes']['md5'] is not None
        assert analysis['hashes']['sha256'] is not None
        assert analysis['entropy'] > 0.0
        
        # Test strings extraction caught our test string
        assert "ThisIsSomePrintableStringForTestingInsideThePayload" in analysis['strings']
        assert "KERNEL32.dllVirtualAlloc" in analysis['strings']

        # Save malware sample record
        family = MalwareService.get_family_or_create("CozyBearTrojan", family_type="trojan", org_id=org.id)
        sample = MalwareService.create_sample(
            family_id=family.id,
            filename="payload.exe",
            file_size=len(sample_payload),
            md5=analysis['hashes']['md5'],
            sha1=analysis['hashes']['sha1'],
            sha256=analysis['hashes']['sha256'],
            static_metadata=analysis['metadata'],
            entropy=analysis['entropy'],
            extracted_strings=analysis['strings'],
            org_id=org.id
        )
        assert sample.id is not None
        assert sample.entropy == analysis['entropy']
        assert sample.family_id == family.id


# ─────────────────────────────────────────────────────────────────────────────
# ATT&CK Navigator Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_attack_navigator_coverage(app, cti_setup):
    """Test computing technique coverage scores and tactical heatmaps."""
    with app.app_context():
        org = cti_setup['org']
        
        # Register a mock rule to seed base metrics
        sigma_repo = SigmaRepository(rule_name="Process Injection Detect", rule_text="selection: EventID: 1", organization_id=org.id)
        yara_repo = YaraRepository(rule_name="Trojan Signature", rule_text="rule WebShell { condition: true }", organization_id=org.id)
        db.session.add(sigma_repo)
        db.session.add(yara_repo)
        db.session.commit()

        coverage = NavigatorService.compute_coverage(org_id=org.id)
        assert "tactic_coverage_pct" in coverage
        assert "detection_coverage_pct" in coverage
        assert "heatmap" in coverage
        
        # Check that standard tactics like Credential Access are in the heatmap
        assert "Credential Access" in coverage['heatmap']
        assert coverage['heatmap']['Credential Access']['score'] > 0


# ─────────────────────────────────────────────────────────────────────────────
# CTI Research Reports Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_report_generation(app, cti_setup):
    """Test generating structured research reports with standard sections."""
    with app.app_context():
        org = cti_setup['org']
        
        report = ResearchService.create_report(
            title="Active Espionage Threat Profile CozyBear",
            executive_summary="Executive briefing of APT29 activities",
            technical_analysis="Binary reversing analysis details",
            iocs=["192.168.1.1", "evil.com"],
            mitre_techniques=["T1190", "T1078"],
            recommendations="Upgrade defensive firewalls and credentials",
            org_id=org.id
        )
        assert report.id is not None
        assert report.title == "Active Espionage Threat Profile CozyBear"
        assert "APT29" in report.executive_summary
        
        # Check serialized lists
        iocs = json.loads(report.ioc_json)
        assert "evil.com" in iocs
        techniques = json.loads(report.mitre_techniques_json)
        assert "T1190" in techniques

        # List
        reports = ResearchService.list_reports(org_id=org.id)
        assert len(reports) == 1


# ─────────────────────────────────────────────────────────────────────────────
# AI Assistant & Hook Lifecycle Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_ai_assistant_and_hooks(app, cti_setup):
    """Test CTI AI assistant summaries and verify hook trigger lifecycles."""
    with app.app_context():
        org = cti_setup['org']
        
        # Setup mock entities
        actor = ThreatActorService.create_actor("OceanLotus", country="Vietnam", org_id=org.id)
        campaign = CampaignService.create_campaign(
            actor_id=actor.id, name="Operation Lotus Leaf", target_sector="Gov", org_id=org.id
        )

        # Track hook calls
        hook_calls = []
        def before_cb(*args, **kwargs):
            hook_calls.append("before")
        def after_cb(*args, **kwargs):
            hook_calls.append("after")

        HookService.register_hook('before_research_request', before_cb)
        HookService.register_hook('after_research_response', after_cb)

        try:
            # Trigger AI campaign summarizer
            summary = ResearchAIService.summarize_campaign(campaign.id)
            assert "OceanLotus" in summary
            assert "Lotus Leaf" in summary

            # Check hooks fired
            assert "before" in hook_calls
            assert "after" in hook_calls
        finally:
            # Cleanup hooks
            HookService.clear_all()


# ─────────────────────────────────────────────────────────────────────────────
# Authenticated API Endpoints Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_research_api_endpoints(client, cti_setup):
    """Test all Phase 19 Research API routes using JWT Bearer headers."""
    headers = cti_setup['headers']
    
    # 1. Access without JWT token (should fail with 401)
    resp = client.get('/api/v1/threat-actors')
    assert resp.status_code == 401

    # 2. Access with valid JWT token (should succeed with 200)
    resp = client.get('/api/v1/threat-actors', headers=headers)
    assert resp.status_code == 200

    # 3. Create Threat Actor
    resp = client.post('/api/v1/threat-actors', data=json.dumps({
        "name": "APT33", "country": "Iran", "motivation": "sabotage"
    }), content_type='application/json', headers=headers)
    assert resp.status_code == 201
    actor_id = json.loads(resp.data)['threat_actor']['id']

    # 4. Create Campaign
    resp = client.post('/api/v1/campaigns', data=json.dumps({
        "actor_id": actor_id, "name": "Operation Shamoon", "target_sector": "Energy"
    }), content_type='application/json', headers=headers)
    assert resp.status_code == 201
    camp_id = json.loads(resp.data)['campaign']['id']

    # 5. Get campaigns
    resp = client.get('/api/v1/campaigns', headers=headers)
    assert resp.status_code == 200

    # 6. Analyze malware static artifact
    resp = client.post('/api/v1/malware/analyze?family=ShamoonWiper', data=json.dumps({
        "filename": "wiper.exe", "content": "MZ header data test strings"
    }), content_type='application/json', headers=headers)
    assert resp.status_code == 201

    # 7. Create Research Report
    resp = client.post('/api/v1/reports', data=json.dumps({
        "title": "Shamoon Campaign Report",
        "executive_summary": "Summary of wiper incident",
        "iocs": ["shamoon.c2.net"]
    }), content_type='application/json', headers=headers)
    assert resp.status_code == 201

    # 8. Query AI Chatbot
    resp = client.post('/api/v1/research/ai/chat', data=json.dumps({
        "type": "summarize_campaign", "target_id": camp_id
    }), content_type='application/json', headers=headers)
    assert resp.status_code == 200
    assert "Operation Shamoon" in json.loads(resp.data)['response']


# ─────────────────────────────────────────────────────────────────────────────
# Phase 19 — Additional Unit Tests to satisfy 275+ targets
# ─────────────────────────────────────────────────────────────────────────────

def test_actor_aliases_empty(app, cti_setup):
    """Test actor profile creation with empty aliases value."""
    with app.app_context():
        org = cti_setup['org']
        actor = ThreatActorService.create_actor("APT_Empty", aliases="", org_id=org.id)
        assert actor.aliases == ""
        assert actor.to_dict()['aliases'] == []


def test_actor_motivation_default(app, cti_setup):
    """Test actor creation with no motivation returns empty or default."""
    with app.app_context():
        org = cti_setup['org']
        actor = ThreatActorService.create_actor("APT_NoMotiv", org_id=org.id)
        assert actor.motivation == ""
        assert actor.country == ""


def test_actor_update_invalid_id(app):
    """Test updating actor with invalid ID throws ValueError."""
    with app.app_context():
        with pytest.raises(ValueError):
            ThreatActorService.update_actor(9999, country="US")


def test_actor_delete_invalid_id(app):
    """Test deleting actor with invalid ID returns False."""
    with app.app_context():
        res = ThreatActorService.delete_actor(9999)
        assert res is False


def test_campaign_dates_verification(app, cti_setup):
    """Test campaign creation with explicit dates."""
    with app.app_context():
        org = cti_setup['org']
        actor = ThreatActorService.create_actor("APT_DateTest", org_id=org.id)
        start = datetime.datetime(2026, 1, 1)
        end = datetime.datetime(2026, 12, 31)
        camp = CampaignService.create_campaign(
            actor_id=actor.id, name="Timed Campaign", start_date=start, end_date=end, org_id=org.id
        )
        assert camp.start_date == start
        assert camp.end_date == end


def test_campaign_malware_list_parsing(app, cti_setup):
    """Test campaign dictionary parses comma-separated malware list."""
    with app.app_context():
        org = cti_setup['org']
        actor = ThreatActorService.create_actor("APT_MalwareList", org_id=org.id)
        camp = CampaignService.create_campaign(
            actor_id=actor.id, name="Malware List Camp", malware_used="Wiper, Keylogger, Ransomware", org_id=org.id
        )
        malwares = camp.to_dict()['malware_used']
        assert len(malwares) == 3
        assert "Keylogger" in malwares


def test_campaign_update_invalid_id(app):
    """Test updating campaign with invalid ID throws ValueError."""
    with app.app_context():
        with pytest.raises(ValueError):
            CampaignService.update_campaign(9999, name="None")


def test_campaign_delete_invalid_id(app):
    """Test deleting campaign with invalid ID returns False."""
    with app.app_context():
        res = CampaignService.delete_campaign(9999)
        assert res is False


def test_malware_shannon_entropy_extreme_low(app):
    """Test Shannon entropy of empty bytes is 0.0."""
    res = MalwareService.calculate_entropy(b"")
    assert res == 0.0


def test_malware_shannon_entropy_mid(app):
    """Test Shannon entropy calculation of non-trivial structured byte data."""
    res = MalwareService.calculate_entropy(b"AABBCCDD")
    assert res == 2.0  # 4 distinct symbols, equal probability


def test_malware_strings_empty(app):
    """Test strings extraction from empty bytes returns empty string."""
    res = MalwareService.extract_strings(b"")
    assert res == ""


def test_malware_strings_short_ignored(app):
    """Test strings shorter than minimum length are ignored."""
    res = MalwareService.extract_strings(b"ABC", min_len=4)
    assert res == ""


def test_malware_strings_multiple_lines(app):
    """Test strings extraction outputs newline-separated printable ASCII values."""
    res = MalwareService.extract_strings(b"Hello\x00World\x00Testing", min_len=4)
    lines = res.split('\n')
    assert "Hello" in lines
    assert "World" in lines


def test_report_empty_iocs_and_ttps(app, cti_setup):
    """Test report creation with empty IOCs and techniques list."""
    with app.app_context():
        org = cti_setup['org']
        rep = ResearchService.create_report("Empty Report", org_id=org.id)
        assert rep.to_dict()['iocs'] == []
        assert rep.to_dict()['mitre_techniques'] == []


def test_report_update_iocs_serialization(app, cti_setup):
    """Test updating report IOCs list properly updates underlying JSON string."""
    with app.app_context():
        org = cti_setup['org']
        rep = ResearchService.create_report("Updatable Report", org_id=org.id)
        updated = ResearchService.update_report(rep.id, iocs=["c2.evil.com", "1.1.1.1"])
        assert "c2.evil.com" in updated.to_dict()['iocs']


def test_report_delete_invalid_id(app):
    """Test deleting research report with invalid ID returns False."""
    with app.app_context():
        res = ResearchService.delete_report(9999)
        assert res is False


def test_research_ai_explain_malware_missing(app):
    """Test AI malware explanation returns error text on invalid sample."""
    with app.app_context():
        res = ResearchAIService.explain_malware(9999)
        assert "not found" in res


def test_research_ai_summarize_campaign_missing(app):
    """Test AI campaign summary returns error text on invalid campaign."""
    with app.app_context():
        res = ResearchAIService.summarize_campaign(9999)
        assert "not found" in res


def test_research_ai_correlate_techniques_missing(app):
    """Test AI technique correlation returns error text on invalid actor."""
    with app.app_context():
        res = ResearchAIService.correlate_techniques(9999)
        assert "not found" in res


def test_research_ai_produce_report(app):
    """Test AI report generation produces valid dictionary structure."""
    with app.app_context():
        res = ResearchAIService.produce_threat_report("Report Title", "Phishing")
        assert res['title'] == "Report Title"
        assert "iocs" in res
        assert len(res['iocs']) >= 1


def test_research_api_route_unauthorized_token(client):
    """Test CTI endpoints return 401 with invalid JWT header prefix."""
    resp = client.get('/api/v1/threat-actors', headers={"Authorization": "Bearer invalid_token_here"})
    assert resp.status_code == 401

