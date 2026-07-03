"""
CertService - Phase 29 Global Cyber Command Center.
Manages national CERT team registration, evaluation, and synchronization.
"""
from app.extensions import db
from app.models.cert_team import CertTeam


class CertService:
    @staticmethod
    def register(country: str, capability: float, org_id: int) -> CertTeam:
        """Register a new national CERT team."""
        cert = CertTeam(
            country=country,
            capability=max(0.0, min(1.0, capability)),
            readiness=0.5,
            trust_score=0.5,
            organization_id=org_id,
        )
        db.session.add(cert)
        db.session.commit()
        return cert

    @staticmethod
    def evaluate(cert_id: int) -> dict:
        """Evaluate CERT readiness based on capability and trust score."""
        cert = db.session.get(CertTeam, cert_id)
        if not cert:
            return {'error': 'CERT team not found'}
        composite = round((cert.capability + cert.readiness + cert.trust_score) / 3.0, 3)
        rating = 'excellent' if composite >= 0.8 else 'good' if composite >= 0.6 else 'needs_improvement'
        return {
            'cert_id': cert_id,
            'country': cert.country,
            'composite_score': composite,
            'rating': rating,
        }

    @staticmethod
    def synchronize(org_id: int) -> dict:
        """Synchronize all CERTs in org — boost readiness scores."""
        certs = CertTeam.query.filter_by(organization_id=org_id).all()
        if not certs:
            return {'synchronized': 0, 'avg_readiness': 0.0}
        for cert in certs:
            cert.readiness = min(1.0, round(cert.readiness + 0.05, 3))
        db.session.commit()
        avg = sum(c.readiness for c in certs) / len(certs)
        return {'synchronized': len(certs), 'avg_readiness': round(avg, 3)}
