"""
Tests for Phase 18 — Enterprise SOC & Threat Intelligence.
"""
import pytest
import json
from app.extensions import db
from app.models.user import User
from app.models.organization import Organization
from app.models.ioc import IOC
from app.models.threat_feed import ThreatFeed
from app.models.sigma_rule import SigmaRule
from app.models.yara_rule import YaraRule
from app.models.alert import Alert
from app.models.case import Case
from app.models.hunt import Hunt
from app.models.attack_event import AttackEvent

from app.services.threat_intelligence_service import ThreatIntelligenceService
from app.services.sigma_service import SigmaService
from app.services.yara_service import YaraService
from app.services.siem_service import SIEMService
from app.services.case_service import CaseService
from app.services.hunt_service import HuntService
from app.services.playbook_service import PlaybookService
from app.services.soc_ai_service import SOCAIService


@pytest.fixture
def soc_setup(app):
    """Set up basic organization, admin user, and analyst user."""
    with app.app_context():
        # Create organization
        org = Organization(name="SOC Test Org", slug="soc-test-org", plan_type="enterprise", status="active")
        db.session.add(org)
        db.session.commit()

        # Create analyst/user
        from app.services.auth_service import hash_password
        analyst = User(username="analyst_bob", email="bob@soc.org", is_active=True, password_hash=hash_password("SecurePassword123"))
        db.session.add(analyst)
        db.session.commit()

        yield {
            'org': org,
            'analyst': analyst
        }


# -------------------------------------------------------------------------
# IOC Tests
# -------------------------------------------------------------------------

def test_ioc_crud(app, soc_setup):
    """Test creating, reading, updating and deleting IOCs."""
    with app.app_context():
        org = soc_setup['org']
        ioc = ThreatIntelligenceService.create_ioc(
            ioc_type="ip",
            value="198.51.100.100",
            severity="high",
            confidence=85,
            source="alienvault",
            org_id=org.id,
            tags="c2,apt29",
            description="Active C2 IP"
        )
        assert ioc.id is not None
        assert ioc.value == "198.51.100.100"
        assert ioc.severity == "high"
        assert ioc.confidence == 85

        # List
        iocs = ThreatIntelligenceService.list_iocs(org_id=org.id)
        assert len(iocs) == 1
        assert iocs[0].value == "198.51.100.100"

        # Update
        updated = ThreatIntelligenceService.update_ioc(ioc.id, severity="critical", confidence=99)
        assert updated.severity == "critical"
        assert updated.confidence == 99


def test_ioc_enrichment(app, soc_setup):
    """Test simulated enrichment of an IOC."""
    with app.app_context():
        org = soc_setup['org']
        ioc = ThreatIntelligenceService.create_ioc(
            ioc_type="domain",
            value="dangerous-malware-c2.net",
            severity="medium",
            org_id=org.id
        )
        res = ThreatIntelligenceService.enrich_ioc(ioc.id)
        assert res['ioc_id'] == ioc.id
        assert ioc.geo_country is not None
        assert ioc.reputation_score is not None
        assert ioc.reputation_score < 40  # because domain has "malware" pattern trigger


def test_ioc_correlation(app, soc_setup):
    """Test grouping IOCs based on shared sources/attributes."""
    with app.app_context():
        org = soc_setup['org']
        # Create correlated IOCs
        ThreatIntelligenceService.create_ioc("ip", "1.1.1.1", "high", source="feedX", org_id=org.id)
        ThreatIntelligenceService.create_ioc("domain", "evil.com", "high", source="feedX", org_id=org.id)

        correlations = ThreatIntelligenceService.correlate_iocs(org_id=org.id)
        assert len(correlations) >= 1
        assert correlations[0]['size'] == 2


def test_threat_feed(app, soc_setup):
    """Test threat feeds setup and simulated pull/aggregation."""
    with app.app_context():
        org = soc_setup['org']
        feed = ThreatIntelligenceService.create_feed("URLHaus Feed", "https://urlhaus.example/api", org_id=org.id)
        assert feed.id is not None
        assert feed.name == "URLHaus Feed"

        # Run aggregation
        res = ThreatIntelligenceService.aggregate_feeds(org_id=org.id)
        assert res['feeds_processed'] == 1
        assert res['total_new_iocs'] >= 2
        assert feed.ioc_count >= 2
        assert feed.last_fetched is not None


# -------------------------------------------------------------------------
# Detection Rule Tests
# -------------------------------------------------------------------------

def test_sigma_rule_validation(app, soc_setup):
    """Test validating valid and invalid Sigma YAML formats."""
    with app.app_context():
        valid_yaml = """
title: Suspicious PowerShell execution
logsource:
  product: windows
  service: powershell
detection:
  selection:
    EventID: 4104
    ScriptBlockText|contains: 'mimikatz'
  condition: selection
"""
        invalid_yaml = """
title: Broken
detection:
  condition: missing_selection
"""
        # Valid
        v_ok, v_err = SigmaService.validate_rule(valid_yaml)
        assert v_ok is True
        assert v_err is None

        # Invalid
        inv_ok, inv_err = SigmaService.validate_rule(invalid_yaml)
        assert inv_ok is False
        assert "Missing required keys" in inv_err


def test_sigma_rule_testing(app, soc_setup):
    """Test matching Sigma rule against raw event log."""
    with app.app_context():
        org = soc_setup['org']
        rule_yaml = """
title: Process Injection
logsource:
  product: windows
detection:
  selection:
    CommandLine|contains: 'inject'
  condition: selection
"""
        rule = SigmaService.create_rule("Injection Detection", rule_yaml, logsource="windows", org_id=org.id)
        assert rule.is_valid is True

        # Test matching command line event
        event = {"CommandLine": "powershell.exe -inject -dll"}
        res = SigmaService.test_rule(rule.id, event)
        assert res['matched'] is True

        # Non-matching
        event2 = {"CommandLine": "notepad.exe"}
        res2 = SigmaService.test_rule(rule.id, event2)
        assert res2['matched'] is False


def test_yara_rule_validation(app, soc_setup):
    """Test structural validation of YARA rules."""
    with app.app_context():
        valid_yara = """
rule Mimikatz_String {
    strings:
        $m1 = "mimikatz" nocase
    condition:
        $m1
}
"""
        invalid_yara = """
rule Broken_Rule {
    strings:
        $a = "test"
}
"""
        v_ok, v_err = YaraService.validate_rule(valid_yara)
        assert v_ok is True
        assert v_err is None

        inv_ok, inv_err = YaraService.validate_rule(invalid_yara)
        assert inv_ok is False
        assert "Missing 'condition:'" in inv_err or "YARA structure" in inv_err


def test_yara_rule_testing(app, soc_setup):
    """Test matching YARA rule against sample data payload."""
    with app.app_context():
        org = soc_setup['org']
        rule_text = """
rule WebShell_PHP {
    strings:
        $php = "eval(base64_decode"
    condition:
        $php
}
"""
        rule = YaraService.create_rule("Webshell PHP", rule_text, org_id=org.id)
        assert rule.is_valid is True

        # Test match
        res = YaraService.test_rule(rule.id, "<?php eval(base64_decode('aGVsbG8=')); ?>")
        assert res['matched'] is True

        # Test no match
        res2 = YaraService.test_rule(rule.id, "hello world")
        assert res2['matched'] is False


# -------------------------------------------------------------------------
# SIEM Engine Tests
# -------------------------------------------------------------------------

def test_siem_event_ingestion(app, soc_setup):
    """Test ingesting vendor logs and normalizing them."""
    with app.app_context():
        org = soc_setup['org']
        raw = {
            'sourceIPAddress': '192.168.1.1',
            'DestinationIp': '10.0.0.5',
            'eventName': 'LoginFailure',
            'severity': 'high'
        }
        norm = SIEMService.ingest_event('authentication', raw, org_id=org.id)
        assert norm['source_ip'] == '192.168.1.1'
        assert norm['dest_ip'] == '10.0.0.5'
        assert norm['action'] == 'LoginFailure'
        assert norm['event_type'] == 'authentication'


def test_siem_correlation(app, soc_setup):
    """Test generating Alert when correlation threshold of duplicate source IP logs is met."""
    with app.app_context():
        org = soc_setup['org']
        events = [
            {'source_ip': '198.51.100.1', 'severity': 'high', 'event_type': 'network', 'raw': '{}'},
            {'source_ip': '198.51.100.1', 'severity': 'medium', 'event_type': 'network', 'raw': '{}'},
        ]
        alerts = SIEMService.correlate(events, org_id=org.id)
        assert len(alerts) == 1
        assert "198.51.100.1" in alerts[0].title
        assert alerts[0].severity == "high"


# -------------------------------------------------------------------------
# Alert Lifecycle & Workflow
# -------------------------------------------------------------------------

def test_alert_workflow(app, soc_setup):
    """Test alert state transitions and update endpoints."""
    with app.app_context():
        org = soc_setup['org']
        alert = SIEMService.generate_alert("Suspicious Login", "high", {"source_ip": "1.2.3.4", "event_type": "authentication"}, org_id=org.id)
        assert alert.status == "new"

        # Update status
        SIEMService.update_alert(alert.id, status="investigating")
        assert alert.status == "investigating"


def test_alert_assignment(app, soc_setup):
    """Test assigning an alert to an analyst user."""
    with app.app_context():
        org = soc_setup['org']
        analyst = soc_setup['analyst']
        alert = SIEMService.generate_alert("DDoS Alert", "critical", {"source_ip": "5.6.7.8"}, org_id=org.id)

        # Assign
        SIEMService.assign_alert(alert.id, analyst.id)
        assert alert.assigned_to == analyst.id
        assert alert.status == "acknowledged"
        assert alert.assigned_at is not None


# -------------------------------------------------------------------------
# Case Management Tests
# -------------------------------------------------------------------------

def test_case_lifecycle(app, soc_setup):
    """Test case state transitions and state machine constraints."""
    with app.app_context():
        org = soc_setup['org']
        analyst = soc_setup['analyst']
        case = CaseService.create_case("Malware Execution on Host", priority="high", analyst_id=analyst.id, org_id=org.id)
        assert case.status == "open"

        # transition open -> investigating
        CaseService.transition_case(case.id, "investigating")
        assert case.status == "investigating"

        # invalid transition: open -> contained (must go via investigating)
        case.status = "open" # reset back
        with pytest.raises(ValueError):
            CaseService.transition_case(case.id, "contained")


def test_case_notes_evidence(app, soc_setup):
    """Test appending notes and evidence artifacts to a case."""
    with app.app_context():
        org = soc_setup['org']
        case = CaseService.create_case("Exfiltration Alert", org_id=org.id)

        # Add note
        CaseService.add_note(case.id, "Found outbound HTTP connections", author="bob")
        # Add evidence
        CaseService.add_evidence(case.id, {"type": "pcap", "filename": "dump.pcap", "size": 1024})

        timeline = CaseService.get_timeline(case.id)
        assert len(timeline) == 2
        assert timeline[0]['type'] == 'note'
        assert timeline[1]['type'] == 'pcap'
        assert timeline[1]['filename'] == 'dump.pcap'


def test_case_timeline(app, soc_setup):
    """Test timeline reconstruction matches chronological order."""
    with app.app_context():
        org = soc_setup['org']
        case = CaseService.create_case("SSH Brute Force Case", org_id=org.id)
        CaseService.add_note(case.id, "SSH attempt check", author="system")
        timeline = CaseService.get_timeline(case.id)
        assert len(timeline) >= 1
        assert timeline[0]['text'] == "SSH attempt check"


# -------------------------------------------------------------------------
# Threat Hunting Tests
# -------------------------------------------------------------------------

def test_hunt_ioc(app, soc_setup):
    """Test running an IOC hunt on indicators."""
    with app.app_context():
        org = soc_setup['org']
        # Create IOCs
        ThreatIntelligenceService.create_ioc("ip", "8.8.8.8", "medium", org_id=org.id)
        hunt = HuntService.create_hunt("DNS Search", "ioc", "Look for Google DNS", org_id=org.id)

        # Run hunt
        res = HuntService.run_ioc_hunt(hunt.id, ["8.8.8.8"])
        assert len(res['matches']) == 1
        assert res['matches'][0]['value'] == "8.8.8.8"
        assert hunt.status == "completed"


def test_hunt_mitre(app, soc_setup):
    """Test running a MITRE ATT&CK hunt against AttackEvent records."""
    with app.app_context():
        org = soc_setup['org']
        
        # Insert a cyber range attack event to hunt against
        ev = AttackEvent(
            simulation_id=1,
            tactic="Initial Access",
            technique="T1190",
            severity="high",
            source="external",
            target="webserver"
        )
        db.session.add(ev)
        db.session.commit()

        hunt = HuntService.create_hunt("T1190 Hunt", "mitre", "Look for exploit public public-facing apps", org_id=org.id)
        res = HuntService.run_mitre_hunt(hunt.id, "T1190")
        assert len(res['matches']) == 1
        assert res['matches'][0]['technique'] == "T1190"


def test_hunt_behavioral(app, soc_setup):
    """Test running a behavioral hunt pattern match."""
    with app.app_context():
        org = soc_setup['org']
        ev = AttackEvent(
            simulation_id=1,
            tactic="Privilege Escalation",
            technique="T1078 - Valid Accounts",
            severity="high",
            source="local",
            target="domain_controller"
        )
        db.session.add(ev)
        db.session.commit()

        hunt = HuntService.create_hunt("Priv Escalation Hunt", "behavioral", "Look for priv escalation", org_id=org.id)
        res = HuntService.run_behavioral_hunt(hunt.id, "Privilege")
        assert len(res['matches']) == 1


# -------------------------------------------------------------------------
# SOAR Playbook Action Tests
# -------------------------------------------------------------------------

def test_playbook_actions(app, soc_setup):
    """Test SOAR playbook actions (simulated execution logs)."""
    with app.app_context():
        org = soc_setup['org']
        case = CaseService.create_case("Infection Active", org_id=org.id)

        # Isolate host
        h_res = PlaybookService.isolate_host("desktop-123", case_id=case.id)
        assert h_res['success'] is True
        assert "isolate_host" in h_res['action_type']

        # Disable user
        u_res = PlaybookService.disable_user("compromised_bob", case_id=case.id)
        assert u_res['success'] is True

        # Escalate incident
        i_res = PlaybookService.create_incident(case.id)
        assert i_res['success'] is True
        assert case.status == "investigating"


# -------------------------------------------------------------------------
# AI Analyst Tests
# -------------------------------------------------------------------------

def test_soc_ai_triage(app, soc_setup):
    """Test SOC AI alert triage, severity recommendation, and mapping."""
    with app.app_context():
        org = soc_setup['org']
        alert = SIEMService.generate_alert("SQL injection attack detected", "medium", {"source_ip": "1.2.3.4", "event_type": "web"}, org_id=org.id)

        res = SOCAIService.triage_alert(alert.id)
        assert res['recommended_severity'] == "high"  # upgraded because of SQL injection keyword
        assert res['mitre_technique'] == "T1190 - Exploit Public-Facing Application"

        # Guidance
        case = CaseService.create_case("Exfil Event", alert_id=alert.id, org_id=org.id)
        guide = SOCAIService.guide_investigation(case.id)
        assert "WAF logs" in guide or "Playbook" in guide


# -------------------------------------------------------------------------
# API Endpoint Tests
# -------------------------------------------------------------------------

def test_soc_api_routes(client, soc_setup):
    """Test all SOC API endpoints for listing and creating objects."""
    # IOC CRUD
    resp = client.post('/api/v1/iocs', data=json.dumps({
        'type': 'ip', 'value': '198.51.100.99', 'severity': 'high', 'confidence': 80
    }), content_type='application/json')
    assert resp.status_code == 201

    resp = client.get('/api/v1/iocs')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['count'] >= 1

    # Alerts
    resp = client.post('/api/v1/alerts', data=json.dumps({
        'title': 'Test Raw Alert', 'severity': 'medium', 'event_type': 'network'
    }), content_type='application/json')
    assert resp.status_code == 201
    alert_id = json.loads(resp.data)['alert']['id']

    resp = client.get('/api/v1/alerts')
    assert resp.status_code == 200

    # Triage
    resp = client.post(f'/api/v1/alerts/{alert_id}/triage')
    assert resp.status_code == 200

    # Cases
    resp = client.post('/api/v1/cases', data=json.dumps({
        'title': 'Test SOC Incident Case', 'priority': 'medium'
    }), content_type='application/json')
    assert resp.status_code == 201
    case_id = json.loads(resp.data)['case']['id']

    resp = client.patch(f'/api/v1/cases/{case_id}', data=json.dumps({
        'status': 'investigating', 'note': 'starting lookup'
    }), content_type='application/json')
    assert resp.status_code == 200

    # Hunts
    resp = client.post('/api/v1/hunts', data=json.dumps({
        'name': 'API IOC Hunt', 'hunt_type': 'ioc'
    }), content_type='application/json')
    assert resp.status_code == 201
    hunt_id = json.loads(resp.data)['hunt']['id']

    resp = client.post(f'/api/v1/hunts/{hunt_id}/run', data=json.dumps({
        'ioc_values': ['198.51.100.99']
    }), content_type='application/json')
    assert resp.status_code == 200
