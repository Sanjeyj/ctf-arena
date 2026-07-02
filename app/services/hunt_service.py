"""
Hunt Service — Phase 18 SOC Platform / Threat Hunting.
IOC, behavioral, MITRE ATT&CK, and anomaly hunts (simulation only).
"""
import datetime
import json
import re
from app.extensions import db
from app.models.hunt import Hunt, HUNT_TYPES, HUNT_STATUSES
from app.models.ioc import IOC
from app.models.attack_event import AttackEvent


class HuntService:

    # -------------------------------------------------------------------------
    # Hunt Management
    # -------------------------------------------------------------------------

    @staticmethod
    def create_hunt(name: str, hunt_type: str, hypothesis: str = '',
                    description: str = '', analyst_id: int = None,
                    org_id: int = None) -> Hunt:
        if hunt_type not in HUNT_TYPES:
            raise ValueError(f"Invalid hunt type '{hunt_type}'. Must be one of {HUNT_TYPES}")
        hunt = Hunt(
            name=name,
            hunt_type=hunt_type,
            hypothesis=hypothesis,
            description=description,
            analyst_id=analyst_id,
            status='planned',
            organization_id=org_id,
        )
        db.session.add(hunt)
        db.session.commit()
        return hunt

    @staticmethod
    def get_hunt(hunt_id: int) -> Hunt:
        return db.session.get(Hunt, hunt_id)

    @staticmethod
    def list_hunts(org_id: int = None, status: str = None):
        q = Hunt.query
        if org_id:
            q = q.filter_by(organization_id=org_id)
        if status:
            q = q.filter_by(status=status)
        return q.order_by(Hunt.created_at.desc()).all()

    # -------------------------------------------------------------------------
    # IOC Hunt
    # -------------------------------------------------------------------------

    @staticmethod
    def run_ioc_hunt(hunt_id: int, ioc_values: list) -> dict:
        """
        Simulate scanning for known IOC values in the IOC database.
        Returns matches from the IOC table.
        """
        hunt = db.session.get(Hunt, hunt_id)
        if not hunt:
            raise ValueError(f"Hunt {hunt_id} not found")

        hunt.status = 'active'
        hunt.started_at = datetime.datetime.utcnow()
        hunt.query = json.dumps(ioc_values)
        db.session.commit()

        # Search IOC table for value matches
        matches = []
        for val in ioc_values:
            iocs = IOC.query.filter(IOC.value.ilike(f'%{val}%')).all()
            for ioc in iocs:
                matches.append({
                    'ioc_id': ioc.id,
                    'type': ioc.type,
                    'value': ioc.value,
                    'severity': ioc.severity,
                    'source': ioc.source,
                })

        findings = {'type': 'ioc', 'matches': matches, 'searched': ioc_values}
        HuntService._complete_hunt(hunt, findings, len(matches))
        return findings

    # -------------------------------------------------------------------------
    # Behavioral Hunt
    # -------------------------------------------------------------------------

    @staticmethod
    def run_behavioral_hunt(hunt_id: int, pattern: str) -> dict:
        """
        Simulate a behavioral hunt by scanning AttackEvent records for pattern.
        """
        hunt = db.session.get(Hunt, hunt_id)
        if not hunt:
            raise ValueError(f"Hunt {hunt_id} not found")

        hunt.status = 'active'
        hunt.started_at = datetime.datetime.utcnow()
        hunt.query = pattern
        db.session.commit()

        # Pattern match against attack_events technique/tactic fields
        matches = []
        try:
            events = AttackEvent.query.all()
            pat = re.compile(pattern, re.IGNORECASE)
            for ev in events:
                if pat.search(ev.technique or '') or pat.search(ev.tactic or ''):
                    matches.append({
                        'event_id': ev.id,
                        'technique': ev.technique,
                        'tactic': ev.tactic,
                        'severity': ev.severity,
                    })
        except Exception:
            pass

        findings = {'type': 'behavioral', 'pattern': pattern, 'matches': matches}
        HuntService._complete_hunt(hunt, findings, len(matches))
        return findings

    # -------------------------------------------------------------------------
    # MITRE ATT&CK Hunt
    # -------------------------------------------------------------------------

    @staticmethod
    def run_mitre_hunt(hunt_id: int, technique_id: str) -> dict:
        """
        Hunt for specific MITRE ATT&CK technique in AttackEvent records.
        """
        hunt = db.session.get(Hunt, hunt_id)
        if not hunt:
            raise ValueError(f"Hunt {hunt_id} not found")

        hunt.status = 'active'
        hunt.started_at = datetime.datetime.utcnow()
        hunt.query = technique_id
        db.session.commit()

        matches = []
        try:
            events = AttackEvent.query.filter(
                AttackEvent.technique.ilike(f'%{technique_id}%')
            ).all()
            for ev in events:
                matches.append({
                    'event_id': ev.id,
                    'technique': ev.technique,
                    'tactic': ev.tactic,
                    'severity': ev.severity,
                    'source': ev.source,
                })
        except Exception:
            pass

        findings = {'type': 'mitre', 'technique': technique_id, 'matches': matches}
        HuntService._complete_hunt(hunt, findings, len(matches))
        return findings

    # -------------------------------------------------------------------------
    # Anomaly Hunt (simulated)
    # -------------------------------------------------------------------------

    @staticmethod
    def run_anomaly_hunt(hunt_id: int, baseline: dict = None) -> dict:
        """
        Simulate an anomaly hunt: generates a synthetic anomaly report.
        No real ML — educational placeholder.
        """
        hunt = db.session.get(Hunt, hunt_id)
        if not hunt:
            raise ValueError(f"Hunt {hunt_id} not found")

        hunt.status = 'active'
        hunt.started_at = datetime.datetime.utcnow()
        db.session.commit()

        # Simulated findings
        findings = {
            'type': 'anomaly',
            'baseline': baseline or {},
            'anomalies': [
                {'metric': 'login_failures', 'observed': 142, 'baseline': 12, 'z_score': 4.2},
                {'metric': 'outbound_bytes', 'observed': 50_000_000, 'baseline': 1_000_000, 'z_score': 6.1},
            ],
            'note': 'Simulated anomaly detection — educational only',
        }
        HuntService._complete_hunt(hunt, findings, 2)
        return findings

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _complete_hunt(hunt: Hunt, findings: dict, artifact_count: int):
        hunt.findings = json.dumps(findings)
        hunt.artifacts_found = artifact_count
        hunt.iocs_identified = len(findings.get('matches', []))
        hunt.status = 'completed'
        hunt.ended_at = datetime.datetime.utcnow()
        db.session.commit()

    @staticmethod
    def complete_hunt(hunt_id: int, findings: str) -> Hunt:
        hunt = db.session.get(Hunt, hunt_id)
        if not hunt:
            raise ValueError(f"Hunt {hunt_id} not found")
        hunt.findings = findings
        hunt.status = 'completed'
        hunt.ended_at = datetime.datetime.utcnow()
        db.session.commit()
        return hunt
