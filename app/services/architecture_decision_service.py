"""Phase 40 — Architecture Decision Record (ADR) Service.

Manages the lifecycle of Architecture Decision Records (ADRs) with strict
FSM state transitions. All calculations are offline and tenant-isolated.
"""
import json
import logging
import datetime
from typing import Dict, List, Optional

from app.extensions import db
from app.models.architecture_decision_record import ArchitectureDecisionRecord

logger = logging.getLogger(__name__)


class ArchitectureDecisionService:
    """Manages Architecture Decision Records (ADRs) and their transitions."""

    @classmethod
    def create_decision(
        cls,
        org_id: int,
        adr_key: str,
        title: str,
        decision: str,
        context: str = '',
        consequences: str = '',
        alternatives: Optional[List[str]] = None,
        affected_modules: Optional[List[str]] = None,
    ) -> Dict:
        """Create a new ADR record in 'proposed' state."""
        if not adr_key or not title or not decision:
            raise ValueError("adr_key, title, and decision are required")
        existing = ArchitectureDecisionRecord.query.filter_by(
            adr_key=adr_key, organization_id=org_id
        ).first()
        if existing:
            raise ValueError(f"ADR with key '{adr_key}' already exists for org {org_id}")

        rec = ArchitectureDecisionRecord(
            adr_key=adr_key,
            title=title,
            context=context,
            decision=decision,
            consequences=consequences,
            alternatives_json=json.dumps(alternatives or []),
            affected_modules_json=json.dumps(affected_modules or []),
            status='proposed',
            organization_id=org_id,
        )
        db.session.add(rec)
        db.session.commit()
        logger.info(f"[ADR] Created ADR {adr_key} in 'proposed' state for org {org_id}")
        return rec.to_dict()

    @classmethod
    def validate_transition(cls, current_status: str, target_status: str) -> bool:
        """Validate FSM transition constraints."""
        allowed = ArchitectureDecisionRecord.VALID_TRANSITIONS.get(current_status, ())
        return target_status in allowed

    @classmethod
    def accept_decision(cls, org_id: int, adr_id: int, approved_by: str) -> Dict:
        """Transition ADR from 'proposed' to 'accepted' state with human signature."""
        rec = ArchitectureDecisionRecord.query.filter_by(id=adr_id, organization_id=org_id).first()
        if not rec:
            raise ValueError(f"ADR {adr_id} not found")
        if not cls.validate_transition(rec.status, 'accepted'):
            raise ValueError(f"Invalid transition from '{rec.status}' to 'accepted'")
        if not approved_by or not approved_by.strip():
            raise ValueError("Human approval signature required")

        rec.status = 'accepted'
        rec.approved_by = approved_by.strip()
        rec.decided_at = datetime.datetime.utcnow()
        db.session.commit()
        logger.info(f"[ADR] ADR {rec.adr_key} accepted by '{approved_by}'")
        return rec.to_dict()

    @classmethod
    def deprecate_decision(cls, org_id: int, adr_id: int) -> Dict:
        """Transition ADR to 'deprecated' state."""
        rec = ArchitectureDecisionRecord.query.filter_by(id=adr_id, organization_id=org_id).first()
        if not rec:
            raise ValueError(f"ADR {adr_id} not found")
        if not cls.validate_transition(rec.status, 'deprecated'):
            raise ValueError(f"Invalid transition from '{rec.status}' to 'deprecated'")

        rec.status = 'deprecated'
        db.session.commit()
        return rec.to_dict()

    @classmethod
    def supersede_decision(cls, org_id: int, adr_id: int, superseding_adr_key: str) -> Dict:
        """Transition ADR to 'superseded' state."""
        rec = ArchitectureDecisionRecord.query.filter_by(id=adr_id, organization_id=org_id).first()
        if not rec:
            raise ValueError(f"ADR {adr_id} not found")
        if not cls.validate_transition(rec.status, 'superseded'):
            raise ValueError(f"Invalid transition from '{rec.status}' to 'superseded'")

        rec.status = 'superseded'
        rec.consequences = (rec.consequences or '') + f" | Superseded by ADR {superseding_adr_key}"
        db.session.commit()
        return rec.to_dict()

    @classmethod
    def list_affected_modules(cls, org_id: int, adr_id: int) -> List[str]:
        """List modules affected by the decision."""
        rec = ArchitectureDecisionRecord.query.filter_by(id=adr_id, organization_id=org_id).first()
        if not rec:
            raise ValueError(f"ADR {adr_id} not found")
        try:
            return json.loads(rec.affected_modules_json or '[]')
        except Exception:
            return []

    @classmethod
    def decision_summary(cls, org_id: int) -> Dict:
        """Get summary of ADR status count."""
        recs = ArchitectureDecisionRecord.query.filter_by(organization_id=org_id).all()
        counts = {'proposed': 0, 'accepted': 0, 'deprecated': 0, 'superseded': 0}
        for r in recs:
            if r.status in counts:
                counts[r.status] += 1
        return {
            'total_adrs': len(recs),
            'status_counts': counts,
        }
