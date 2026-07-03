"""
SOC AI Service — Phase 18 SOC Platform.
AI-powered alert triage, MITRE mapping, incident summarization,
and investigation guidance. Simulation only — no external AI calls.
"""
import datetime
import json
import random
from app.extensions import db
from app.models.alert import Alert, ALERT_SEVERITIES
from app.models.case import Case
from app.services.hook_service import HookService


# Simulated MITRE tactic/technique catalog
_MITRE_MAPPING = {
    'authentication': ('TA0001', 'T1078 - Valid Accounts'),
    'network': ('TA0011', 'T1071 - Application Layer Protocol'),
    'endpoint': ('TA0003', 'T1055 - Process Injection'),
    'web': ('TA0001', 'T1190 - Exploit Public-Facing Application'),
    'cloud': ('TA0006', 'T1552 - Unsecured Credentials'),
    'other': ('TA0040', 'T1485 - Data Destruction'),
}

# Severity upgrade rules (simulated)
_SEVERITY_UPGRADE = {
    'info': 'low',
    'low': 'medium',
    'medium': 'high',
    'high': 'critical',
    'critical': 'critical',
}

_INVESTIGATION_STEPS = {
    'authentication': [
        "1. Review authentication logs for the source IP.",
        "2. Check if the account is a service or human account.",
        "3. Look for lateral movement from authenticated session.",
        "4. Reset credentials if compromise confirmed.",
        "5. Enable MFA if not already enforced.",
    ],
    'network': [
        "1. Capture and inspect traffic from source IP.",
        "2. Correlate with known C2 IOCs.",
        "3. Identify affected endpoints.",
        "4. Block source IP at perimeter (via SOAR playbook).",
        "5. Hunt for related network connections.",
    ],
    'endpoint': [
        "1. Isolate the affected endpoint (via SOAR playbook).",
        "2. Collect memory dump and forensic image.",
        "3. Scan artifacts with YARA rules.",
        "4. Check for persistence mechanisms.",
        "5. Restore from known-good snapshot if needed.",
    ],
    'web': [
        "1. Review WAF logs for the request pattern.",
        "2. Identify the vulnerable endpoint.",
        "3. Check for data exfiltration.",
        "4. Patch the vulnerability or apply WAF rule.",
        "5. Notify security team and affected users.",
    ],
    'cloud': [
        "1. Review CloudTrail / audit logs.",
        "2. Identify IAM principals involved.",
        "3. Revoke compromised credentials immediately.",
        "4. Audit resource changes in the blast radius.",
        "5. Enable GuardDuty / CSPM alerts.",
    ],
}


class SOCAIService:

    # -------------------------------------------------------------------------
    # Alert Triage
    # -------------------------------------------------------------------------

    @staticmethod
    def triage_alert(alert_id: int) -> dict:
        """
        AI-simulated alert triage.
        Fires before/after hooks and returns severity recommendation + MITRE mapping.
        """
        alert = db.session.get(Alert, alert_id)
        if not alert:
            return {'error': f'Alert {alert_id} not found'}

        # Fire before_alert_triage hook
        try:
            HookService.fire('before_alert_triage', alert_id=alert_id)
        except Exception:
            pass

        # Simulated severity recommendation
        recommended_severity = SOCAIService._recommend_severity(alert)

        # Simulated MITRE mapping
        tactic, technique = _MITRE_MAPPING.get(alert.event_type, _MITRE_MAPPING['other'])

        # Build AI analysis text
        analysis = (
            f"AI Triage Analysis for Alert #{alert_id}:\n"
            f"- Original severity: {alert.severity}\n"
            f"- Recommended severity: {recommended_severity}\n"
            f"- Mapped MITRE Tactic: {tactic}\n"
            f"- Mapped MITRE Technique: {technique}\n"
            f"- Event type: {alert.event_type}\n"
            f"- Source IP: {alert.source_ip or 'unknown'}\n"
            f"- Recommendation: {'Escalate immediately' if recommended_severity == 'critical' else 'Monitor and investigate'}"
        )

        # Persist AI fields on alert
        alert.ai_severity_recommendation = recommended_severity
        alert.ai_analysis = analysis
        alert.mitre_tactic = tactic
        alert.mitre_technique = technique
        db.session.commit()

        result = {
            'alert_id': alert_id,
            'original_severity': alert.severity,
            'recommended_severity': recommended_severity,
            'mitre_tactic': tactic,
            'mitre_technique': technique,
            'analysis': analysis,
        }

        # Fire after_alert_triage hook
        try:
            HookService.fire('after_alert_triage', alert_id=alert_id, result=result)
        except Exception:
            pass

        return result

    @staticmethod
    def map_mitre(alert_id: int) -> dict:
        """Map an alert to a MITRE ATT&CK tactic/technique."""
        alert = db.session.get(Alert, alert_id)
        if not alert:
            return {'error': f'Alert {alert_id} not found'}
        tactic, technique = _MITRE_MAPPING.get(alert.event_type, _MITRE_MAPPING['other'])
        alert.mitre_tactic = tactic
        alert.mitre_technique = technique
        db.session.commit()
        return {'alert_id': alert_id, 'tactic': tactic, 'technique': technique}

    # -------------------------------------------------------------------------
    # Incident Summarization
    # -------------------------------------------------------------------------

    @staticmethod
    def summarize_incident(case_id: int) -> str:
        """Generate an AI narrative summary of an incident case."""
        case = db.session.get(Case, case_id)
        if not case:
            return f"Case {case_id} not found."

        notes = json.loads(case.notes or '[]')
        evidence_count = len(json.loads(case.evidence or '[]'))
        note_count = len(notes)

        summary = (
            f"Incident Summary — Case #{case_id}: '{case.title}'\n\n"
            f"Priority: {case.priority.upper()} | Status: {case.status}\n"
            f"Timeline entries: {note_count} notes, {evidence_count} evidence items.\n\n"
            f"Description: {case.description or 'No description provided.'}\n\n"
            f"MITRE Context: {case.mitre_tactic or 'N/A'} / {case.mitre_technique or 'N/A'}\n\n"
            f"Current Status: {case.status}. "
            f"{'Resolved at: ' + case.resolved_at.isoformat() if case.resolved_at else 'Ongoing investigation.'}"
        )

        case.ai_summary = summary
        db.session.commit()
        return summary

    # -------------------------------------------------------------------------
    # Investigation Guidance
    # -------------------------------------------------------------------------

    @staticmethod
    def guide_investigation(case_id: int) -> str:
        """Return step-by-step investigation guidance for an incident case."""
        case = db.session.get(Case, case_id)
        if not case:
            return f"Case {case_id} not found."

        # Determine event type from linked alert if present
        event_type = 'other'
        if case.alert_id:
            alert = db.session.get(Alert, case.alert_id)
            if alert:
                event_type = alert.event_type

        steps = _INVESTIGATION_STEPS.get(event_type, _INVESTIGATION_STEPS.get('other', [
            "1. Collect available logs.",
            "2. Identify affected systems.",
            "3. Contain the threat.",
            "4. Eradicate root cause.",
            "5. Recover and document lessons learned.",
        ]))

        guidance = f"Investigation Playbook for Case #{case_id} ({event_type}):\n\n" + "\n".join(steps)
        case.ai_guidance = guidance
        db.session.commit()
        return guidance

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _recommend_severity(alert: Alert) -> str:
        """
        Upgrade severity if source IP is known-bad or event is critical pattern.
        Simulated heuristic — no live threat intel calls.
        """
        sev = alert.severity
        # Heuristic: brute-force / exploitation patterns upgrade severity
        desc = (alert.description or '').lower() + (alert.title or '').lower()
        upgrade_keywords = ['brute force', 'exploit', 'ransomware', 'lateral', 'exfil', 'c2', 'injection', 'sql']
        if any(kw in desc for kw in upgrade_keywords):
            sev = _SEVERITY_UPGRADE.get(sev, sev)
        return sev
