"""
ZeroTrustDecisionService - Phase 32 Cyber Trust, Assurance & Verification Fabric.
Evaluates Zero Trust policies to make deterministic access decisions and audit logs.
"""
from app.extensions import db
from app.models.trust_identity import TrustIdentity
from app.models.device_posture import DevicePosture
from app.models.trust_decision import TrustDecision
from app.services.hook_service import HookService
from app.services.identity_trust_service import IdentityTrustService
from app.services.device_posture_service import DevicePostureService


class ZeroTrustDecisionService:
    @staticmethod
    def evaluate(identity_id: int, device_id: int, resource_type: str, resource_id: str, requested_action: str, org_id: int, context: dict = None) -> TrustDecision:
        """Evaluate access authorization deterministically, triggering policy wargame hooks."""
        ident = db.session.get(TrustIdentity, identity_id)
        dev = db.session.get(DevicePosture, device_id)

        # Enforce strict tenant boundary checks
        if not ident or ident.organization_id != org_id:
            return None
        if not dev or dev.organization_id != org_id:
            return None

        # Fired before trust decision check hook
        HookService.trigger_hook("before_trust_decision", identity=ident, device=dev)

        # Recalculate scores to reflect latest database state
        IdentityTrustService.calculate_trust(ident)
        DevicePostureService.calculate_posture(dev)

        # Deterministic combined trust score
        policy_compliance = 100.0 if dev.compliance_status == 'compliant' else (50.0 if dev.compliance_status == 'restricted' else 0.0)
        res_sensitivity = 50.0 if (context and context.get('sensitivity') == 'high') else 100.0 # higher sensitivity lowers overall trust

        combined_score = ZeroTrustDecisionService.calculate_combined_trust(
            ident.trust_score, dev.posture_score, policy_compliance, res_sensitivity
        )

        decision_str = ZeroTrustDecisionService.decide(combined_score)
        explanation = f"Combined Zero Trust authorization evaluation score is {combined_score:.2f}."

        decision = TrustDecision(
            identity_id=identity_id,
            device_posture_id=device_id,
            resource_type=resource_type,
            resource_id=str(resource_id),
            requested_action=requested_action,
            trust_score=combined_score,
            decision=decision_str,
            explanation=explanation,
            policy_version='1.0.0',
            organization_id=org_id
        )
        db.session.add(decision)
        db.session.commit()

        # Fired after trust decision check hook
        HookService.trigger_hook("after_trust_decision", decision=decision)

        return decision

    @staticmethod
    def calculate_combined_trust(identity_trust: float, device_posture: float, policy_compliance: float, res_sensitivity: float) -> float:
        """Deterministic weighting: identity (40%), device (30%), policy (20%), sensitivity (10%)."""
        score = (
            (identity_trust * 0.40) +
            (device_posture * 0.30) +
            (policy_compliance * 0.20) +
            (res_sensitivity * 0.10)
        )
        return max(0.0, min(100.0, round(score, 2)))

    @staticmethod
    def decide(combined_score: float) -> str:
        """Map combined scores directly to Zero Trust decisions."""
        # Threshold wargame boundaries:
        # score >= 80 -> allow
        # 60 <= score < 80 -> allow_with_monitoring
        # 40 <= score < 60 -> require_step_up
        # score < 40 -> deny_simulation
        if combined_score >= 80.0:
            return 'allow'
        elif combined_score >= 60.0:
            return 'allow_with_monitoring'
        elif combined_score >= 40.0:
            return 'require_step_up'
        else:
            return 'deny_simulation'

    @staticmethod
    def explain(decision_id: int, org_id: int) -> str:
        """Explain decision metrics logic details."""
        dec = db.session.get(TrustDecision, decision_id)
        if not dec or dec.organization_id != org_id:
            return "Decision not found."
        return f"Decision: {dec.decision.upper()}. Details: {dec.explanation}"

    @staticmethod
    def decision_history(org_id: int) -> list:
        """Retrieve recent Zero Trust decisions ledger audits."""
        return TrustDecision.query.filter_by(organization_id=org_id).order_by(TrustDecision.id.desc()).all()
