"""
IdentityTrustService - Phase 32 Cyber Trust, Assurance & Verification Fabric.
Stores simulated identity assurance posture and evaluates trust scores.
"""
from app.extensions import db
from app.models.trust_identity import TrustIdentity
import datetime


class IdentityTrustService:
    @staticmethod
    def register_identity(user_id: int, identity_type: str, org_id: int, authentication_strength: float = 1.0, risk_score: float = 0.0) -> TrustIdentity:
        """Register a simulated identity assurance posture."""
        ident = TrustIdentity(
            user_id=user_id,
            identity_type=identity_type,
            authentication_strength=max(0.0, min(1.0, authentication_strength)),
            risk_score=max(0.0, min(1.0, risk_score)),
            verification_status='unverified',
            organization_id=org_id
        )
        IdentityTrustService.calculate_trust(ident)
        db.session.add(ident)
        db.session.commit()
        return ident

    @staticmethod
    def calculate_trust(identity: TrustIdentity) -> float:
        """Calculate identity trust score, clamping output to [0.0, 100.0]."""
        # score = (auth_strength * 100) - (risk_score * 50)
        # if restricted, cap trust at 40. if revoked, set to 0.
        if identity.verification_status == 'revoked_simulation':
            score = 0.0
        else:
            base = (identity.authentication_strength * 100.0) - (identity.risk_score * 50.0)
            score = max(0.0, min(100.0, base))
            if identity.verification_status == 'restricted':
                score = min(40.0, score)

        identity.trust_score = round(score, 2)
        return identity.trust_score

    @staticmethod
    def verify(identity_id: int, org_id: int) -> TrustIdentity:
        """Mark identity verification status as verified."""
        ident = db.session.get(TrustIdentity, identity_id)
        if not ident or ident.organization_id != org_id:
            return None
        ident.verification_status = 'verified'
        ident.last_verified_at = datetime.datetime.utcnow()
        IdentityTrustService.calculate_trust(ident)
        db.session.commit()
        return ident

    @staticmethod
    def restrict(identity_id: int, org_id: int) -> TrustIdentity:
        """Restrict identity due to anomaly detection."""
        ident = db.session.get(TrustIdentity, identity_id)
        if not ident or ident.organization_id != org_id:
            return None
        ident.verification_status = 'restricted'
        IdentityTrustService.calculate_trust(ident)
        db.session.commit()
        return ident

    @staticmethod
    def revoke(identity_id: int, org_id: int) -> TrustIdentity:
        """Revoke identity simulation status."""
        ident = db.session.get(TrustIdentity, identity_id)
        if not ident or ident.organization_id != org_id:
            return None
        ident.verification_status = 'revoked_simulation'
        IdentityTrustService.calculate_trust(ident)
        db.session.commit()
        return ident

    @staticmethod
    def explain_score(identity_id: int, org_id: int) -> str:
        """Provide detailed human-readable explanation of identity trust evaluation."""
        ident = db.session.get(TrustIdentity, identity_id)
        if not ident or ident.organization_id != org_id:
            return "Identity not found."
        
        reasons = []
        if ident.verification_status == 'revoked_simulation':
            reasons.append("Simulated identity has been revoked.")
        else:
            if ident.authentication_strength >= 0.8:
                reasons.append("Strong authentication mechanism verified (e.g. multi-factor authentication).")
            else:
                reasons.append("Weak authentication strength detected.")
            
            if ident.risk_score > 0.4:
                reasons.append("Elevated risk indicators detected on identity profile.")
            
            if ident.verification_status == 'restricted':
                reasons.append("Identity is currently in restricted status.")

        return f"Identity trust score is {ident.trust_score}/100. Analysis: " + " ".join(reasons)
