"""
Case Service — Phase 18 SOC Platform / Case Management.
Full incident case lifecycle with state machine, notes, evidence, and timeline.
"""
import datetime
import json
from app.extensions import db
from app.models.case import Case, CASE_STATUSES, CASE_PRIORITIES, CASE_TRANSITIONS
from app.models.alert import Alert


class CaseService:

    # -------------------------------------------------------------------------
    # Case Creation
    # -------------------------------------------------------------------------

    @staticmethod
    def create_case(title: str, description: str = '', priority: str = 'medium',
                    analyst_id: int = None, org_id: int = None,
                    alert_id: int = None) -> Case:
        if priority not in CASE_PRIORITIES:
            raise ValueError(f"Invalid priority '{priority}'.")
        case = Case(
            title=title,
            description=description,
            priority=priority,
            status='open',
            analyst_id=analyst_id,
            alert_id=alert_id,
            organization_id=org_id,
        )
        if analyst_id:
            case.assigned_at = datetime.datetime.utcnow()
        db.session.add(case)
        db.session.commit()
        return case

    @staticmethod
    def get_case(case_id: int) -> Case:
        return db.session.get(Case, case_id)

    @staticmethod
    def list_cases(org_id: int = None, status: str = None, priority: str = None):
        q = Case.query
        if org_id:
            q = q.filter_by(organization_id=org_id)
        if status:
            q = q.filter_by(status=status)
        if priority:
            q = q.filter_by(priority=priority)
        return q.order_by(Case.created_at.desc()).all()

    # -------------------------------------------------------------------------
    # State Machine
    # -------------------------------------------------------------------------

    @staticmethod
    def transition_case(case_id: int, new_status: str) -> Case:
        """Enforce state machine transitions."""
        if new_status not in CASE_STATUSES:
            raise ValueError(f"Invalid status '{new_status}'.")
        case = db.session.get(Case, case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")
        if not case.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition case from '{case.status}' to '{new_status}'. "
                f"Allowed: {CASE_TRANSITIONS.get(case.status, [])}"
            )
        old_status = case.status
        case.status = new_status
        if new_status in ('resolved', 'closed'):
            case.resolved_at = datetime.datetime.utcnow()

        # Add timeline note
        CaseService._append_note(case, f"Status changed: {old_status} → {new_status}")
        db.session.commit()
        return case

    # -------------------------------------------------------------------------
    # Notes & Evidence
    # -------------------------------------------------------------------------

    @staticmethod
    def add_note(case_id: int, note_text: str, author: str = 'system') -> Case:
        case = db.session.get(Case, case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")
        CaseService._append_note(case, note_text, author=author)
        db.session.commit()
        return case

    @staticmethod
    def add_evidence(case_id: int, evidence: dict) -> Case:
        """Add an evidence artifact to the case."""
        case = db.session.get(Case, case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")
        existing = json.loads(case.evidence or '[]')
        evidence['added_at'] = datetime.datetime.utcnow().isoformat()
        existing.append(evidence)
        case.evidence = json.dumps(existing)
        db.session.commit()
        return case

    @staticmethod
    def _append_note(case: Case, text: str, author: str = 'system'):
        existing = json.loads(case.notes or '[]')
        existing.append({
            'text': text,
            'author': author,
            'timestamp': datetime.datetime.utcnow().isoformat(),
        })
        case.notes = json.dumps(existing)

    # -------------------------------------------------------------------------
    # Timeline
    # -------------------------------------------------------------------------

    @staticmethod
    def get_timeline(case_id: int) -> list:
        """Return chronological list of events for this case."""
        case = db.session.get(Case, case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")
        notes = json.loads(case.notes or '[]')
        evidence = json.loads(case.evidence or '[]')

        timeline = []
        for n in notes:
            timeline.append({'type': 'note', **n})
        for e in evidence:
            timeline.append({'type': 'evidence', **e})

        timeline.sort(key=lambda x: x.get('timestamp', '') or x.get('added_at', ''))
        return timeline

    # -------------------------------------------------------------------------
    # Assignment
    # -------------------------------------------------------------------------

    @staticmethod
    def assign_case(case_id: int, analyst_id: int) -> Case:
        case = db.session.get(Case, case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")
        case.analyst_id = analyst_id
        case.assigned_at = datetime.datetime.utcnow()
        db.session.commit()
        return case
