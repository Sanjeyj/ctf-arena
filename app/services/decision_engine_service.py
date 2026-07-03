"""
DecisionEngineService - Phase 26 Autonomous Cyber Enterprise.
Evaluates agent recommendations and manages human-in-the-loop approvals.
"""
from app.extensions import db
from app.models.autonomous_decision import AutonomousDecision

class DecisionEngineService:
    @staticmethod
    def evaluate(decision_type: str, recommendation: str, confidence: float, organization_id: int) -> AutonomousDecision:
        """Create a new autonomous decision record for evaluation."""
        decision = AutonomousDecision(
            decision_type=decision_type,
            confidence=confidence,
            recommendation=recommendation,
            approval_status='pending_approval',
            organization_id=organization_id
        )
        db.session.add(decision)
        db.session.commit()
        return decision

    @staticmethod
    def recommend(decision_id: int) -> dict:
        """Analyze a decision and output AI engine safety review & recommendation status."""
        decision = AutonomousDecision.query.get(decision_id)
        if not decision:
            return {'error': f"Decision {decision_id} not found."}

        # Auto-recommendation logic based on confidence threshold
        action = "approve" if decision.confidence >= 0.85 else "request_manual_review"
        
        return {
            'decision_id': decision.id,
            'confidence': decision.confidence,
            'recommendation': decision.recommendation,
            'engine_verdict': action,
            'requires_auth_factor': decision.confidence < 0.7
        }

    @staticmethod
    def approve(decision_id: int) -> AutonomousDecision:
        """Approve a decision to allow remediation or action triggers."""
        decision = AutonomousDecision.query.get(decision_id)
        if not decision:
            return None

        decision.approval_status = 'approved'
        db.session.commit()
        return decision
