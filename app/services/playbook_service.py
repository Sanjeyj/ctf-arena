"""
Playbook Service — Phase 18 SOC Platform / SOAR.
Simulated automated response playbook actions.
SIMULATION ONLY — no real infrastructure actions taken.
"""
import datetime
import json
from app.extensions import db
from app.models.case import Case
from app.models.ioc import IOC
from app.models.alert import Alert


class PlaybookService:
    """
    SOAR playbook executor — all actions are simulated and logged.
    No live EDR, network, or user account changes are made.
    """

    # -------------------------------------------------------------------------
    # Playbook Actions
    # -------------------------------------------------------------------------

    @staticmethod
    def isolate_host(hostname: str, case_id: int = None) -> dict:
        """
        SIMULATION: Log a host isolation action.
        No actual network or endpoint changes occur.
        """
        action = PlaybookService._build_action(
            action_type='isolate_host',
            target=hostname,
            case_id=case_id,
            details={'hostname': hostname, 'isolation_method': 'simulated_edr_api'},
            note=f"[SIMULATION] Host '{hostname}' marked for isolation. No real action taken.",
        )
        PlaybookService._append_case_note(case_id, action['note'])
        return action

    @staticmethod
    def disable_user(username: str, case_id: int = None) -> dict:
        """
        SIMULATION: Log a user account disable action.
        No actual account changes occur.
        """
        action = PlaybookService._build_action(
            action_type='disable_user',
            target=username,
            case_id=case_id,
            details={'username': username, 'method': 'simulated_idp_api'},
            note=f"[SIMULATION] Account '{username}' marked for disablement. No real action taken.",
        )
        PlaybookService._append_case_note(case_id, action['note'])
        return action

    @staticmethod
    def block_ioc(ioc_id: int, case_id: int = None) -> dict:
        """
        SIMULATION: Mark an IOC as blocked in the database.
        No firewall / proxy / DNS changes occur.
        """
        ioc = db.session.get(IOC, ioc_id)
        if not ioc:
            return {'error': f'IOC {ioc_id} not found', 'success': False}

        ioc.is_blocked = True
        db.session.commit()

        action = PlaybookService._build_action(
            action_type='block_ioc',
            target=f"{ioc.type}:{ioc.value}",
            case_id=case_id,
            details={'ioc_id': ioc_id, 'ioc_value': ioc.value, 'ioc_type': ioc.type},
            note=f"[SIMULATION] IOC {ioc.type}:{ioc.value} flagged as blocked (DB only).",
        )
        PlaybookService._append_case_note(case_id, action['note'])
        return action

    @staticmethod
    def create_incident(case_id: int) -> dict:
        """
        Escalate a case to a formal incident (transitions case status if possible).
        """
        case = db.session.get(Case, case_id)
        if not case:
            return {'error': f'Case {case_id} not found', 'success': False}

        # Try to move to investigating if still open
        if case.status == 'open':
            case.status = 'investigating'
            db.session.commit()

        action = PlaybookService._build_action(
            action_type='create_incident',
            target=f"case:{case_id}",
            case_id=case_id,
            details={'case_id': case_id, 'new_status': case.status},
            note=f"Case #{case_id} escalated to incident via SOAR playbook.",
        )
        PlaybookService._append_case_note(case_id, action['note'])
        return action

    @staticmethod
    def notify_analyst(analyst_id: int, message: str, case_id: int = None) -> dict:
        """
        Simulate notifying an analyst — logs notification, no real email/SMS sent.
        """
        action = PlaybookService._build_action(
            action_type='notify_analyst',
            target=f"analyst:{analyst_id}",
            case_id=case_id,
            details={'analyst_id': analyst_id, 'message': message},
            note=f"[SIMULATION] Notification sent to analyst #{analyst_id}: {message}",
        )
        PlaybookService._append_case_note(case_id, action['note'])
        return action

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _build_action(action_type: str, target: str, case_id: int,
                      details: dict, note: str) -> dict:
        return {
            'action_type': action_type,
            'target': target,
            'case_id': case_id,
            'details': details,
            'note': note,
            'executed_at': datetime.datetime.utcnow().isoformat(),
            'success': True,
            'simulation': True,
        }

    @staticmethod
    def _append_case_note(case_id: int, note: str):
        if not case_id:
            return
        case = db.session.get(Case, case_id)
        if not case:
            return
        existing = json.loads(case.notes or '[]')
        existing.append({
            'text': note,
            'author': 'soar_playbook',
            'timestamp': datetime.datetime.utcnow().isoformat(),
        })
        case.notes = json.dumps(existing)
        db.session.commit()
