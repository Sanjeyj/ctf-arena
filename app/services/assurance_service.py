"""
AssuranceService - Phase 32 Cyber Trust, Assurance & Verification Fabric.
Manages structured claims, evidence linkages, confidence logic, and gap analysis.
"""
from app.extensions import db
from app.models.assurance_case import AssuranceCase
from app.models.assurance_evidence_link import AssuranceEvidenceLink
from app.models.evidence_record import EvidenceRecord
from app.services.hook_service import HookService


class AssuranceService:
    @staticmethod
    def create_case(title: str, claim: str, org_id: int, scope: str = None, owner: str = None) -> AssuranceCase:
        """Create a security claim assurance case."""
        case = AssuranceCase(
            title=title,
            claim=claim,
            scope=scope,
            confidence_score=0.0,
            status='draft',
            owner=owner,
            organization_id=org_id
        )
        db.session.add(case)
        db.session.commit()
        return case

    @staticmethod
    def attach_evidence(case_id: int, evidence_id: int, relationship_type: str, weight: float, org_id: int) -> AssuranceEvidenceLink:
        """Attach compliance evidence to a claim, rejecting cross-tenant link mappings."""
        case = db.session.get(AssuranceCase, case_id)
        ev = db.session.get(EvidenceRecord, evidence_id)

        if not case or case.organization_id != org_id:
            return None
        if not ev or ev.organization_id != org_id:
            return None

        # Rejects cross-tenant evidence attachments
        link = AssuranceEvidenceLink(
            assurance_case_id=case_id,
            evidence_record_id=evidence_id,
            relationship_type=relationship_type,
            weight=max(0.0, min(1.0, weight)),
            validation_status='valid',
            organization_id=org_id
        )
        db.session.add(link)
        db.session.commit()
        return link

    @staticmethod
    def evaluate_case(case_id: int, org_id: int) -> float:
        """Evaluate case claim confidence score, triggering wargaming check hooks."""
        case = db.session.get(AssuranceCase, case_id)
        if not case or case.organization_id != org_id:
            return 0.0

        # Hook fired before evaluation
        HookService.trigger_hook("before_assurance_evaluation", assurance_case=case)

        links = AssuranceEvidenceLink.query.filter_by(assurance_case_id=case_id, organization_id=org_id).all()
        if not links:
            case.confidence_score = 0.0
            case.status = 'insufficient_evidence'
            db.session.commit()
            return 0.0

        total_weight = 0.0
        contradictions_found = False

        for link in links:
            if link.relationship_type == 'contradicts':
                contradictions_found = True
            elif link.relationship_type == 'supports':
                total_weight += link.weight
            elif link.relationship_type == 'compensating_control':
                total_weight += (link.weight * 0.8)

        # Base confidence calculation
        confidence = total_weight * 100.0
        if contradictions_found:
            confidence = confidence * 0.20  # Apply heavy penalty to confidence

        confidence = max(0.0, min(100.0, round(confidence, 2)))
        case.confidence_score = confidence

        if confidence >= 70.0:
            case.status = 'supported'
        elif confidence >= 30.0:
            case.status = 'under_review'
        else:
            case.status = 'insufficient_evidence'

        db.session.commit()

        # Hook fired after evaluation
        HookService.trigger_hook("after_assurance_evaluation", assurance_case=case, confidence=confidence)

        return confidence

    @staticmethod
    def identify_evidence_gaps(case_id: int, org_id: int) -> list:
        """Identify missing or weak links supporting a claim."""
        case = db.session.get(AssuranceCase, case_id)
        if not case or case.organization_id != org_id:
            return []
        
        links = AssuranceEvidenceLink.query.filter_by(assurance_case_id=case_id, organization_id=org_id).all()
        gaps = []
        if not links:
            gaps.append("No compliance evidence linked to this assurance case.")
        else:
            support_weight = sum(l.weight for l in links if l.relationship_type == 'supports')
            if support_weight < 0.6:
                gaps.append("Supporting evidence total weight is low (less than 0.6).")
            
            for l in links:
                if l.relationship_type == 'contradicts':
                    gaps.append(f"Contradictory evidence reference found (ID: {l.evidence_record_id}).")
        return gaps

    @staticmethod
    def assurance_summary(org_id: int) -> dict:
        """Retrieve high level statistics of all assurance claims."""
        cases = AssuranceCase.query.filter_by(organization_id=org_id).all()
        if not cases:
            return {'total_cases': 0, 'supported_count': 0, 'avg_confidence': 0.0}
        supported = sum(1 for c in cases if c.status == 'supported')
        avg_conf = sum(c.confidence_score for c in cases) / len(cases)
        return {
            'total_cases': len(cases),
            'supported_count': supported,
            'avg_confidence': round(avg_conf, 2)
        }
