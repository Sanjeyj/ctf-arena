"""
TrustService - Phase 27 Global Security Intelligence Network.
Computes, validates, and updates bilateral trust relationships between organizations.
Simulation-only: no external validation calls.
"""
from app.extensions import db
from app.models.trust_network import TrustNetwork


class TrustService:
    @staticmethod
    def calculate(source_org: str, target_org: str, org_id: int = None) -> TrustNetwork:
        """Compute a new bilateral trust relationship between two organizations."""
        # Check for existing relationship
        existing = TrustNetwork.query.filter_by(
            source_org=source_org, target_org=target_org
        ).first()
        if existing:
            return existing

        # Derive an initial trust score from name length heuristic (simulation)
        base_score = round(0.4 + (len(source_org) % 5) * 0.1, 2)
        trust = TrustNetwork(
            source_org=source_org,
            target_org=target_org,
            trust_score=base_score,
            status='pending',
            organization_id=org_id,
        )
        db.session.add(trust)
        db.session.commit()
        return trust

    @staticmethod
    def validate(trust_id: int) -> dict:
        """Verify the integrity and status of a trust relationship."""
        trust = db.session.get(TrustNetwork, trust_id)
        if not trust:
            return {'valid': False, 'reason': f'TrustNetwork {trust_id} not found'}
        valid = trust.trust_score > 0.0 and trust.status not in ('revoked', 'suspended')
        return {
            'trust_id': trust_id,
            'valid': valid,
            'status': trust.status,
            'trust_score': trust.trust_score,
            'source_org': trust.source_org,
            'target_org': trust.target_org,
        }

    @staticmethod
    def update(trust_id: int, delta: float) -> TrustNetwork:
        """Adjust the trust score on new signals (positive or negative delta)."""
        trust = db.session.get(TrustNetwork, trust_id)
        if not trust:
            return None
        trust.trust_score = round(max(0.0, min(1.0, trust.trust_score + delta)), 3)
        if trust.trust_score >= 0.6 and trust.status == 'pending':
            trust.status = 'active'
        elif trust.trust_score < 0.2:
            trust.status = 'suspended'
        db.session.commit()
        return trust
