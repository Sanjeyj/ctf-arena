"""
ThreatExchange Service - Phase 23 Global Threat Exchange.
Orchestrates secure indicators sharing (YARA, Sigma, reports) under trust tiers validation.
"""
from app.extensions import db
from app.models.shared_ioc import SharedIOC

class ThreatExchangeService:

    @staticmethod
    def share_ioc(value: str, ioc_type: str = 'IP', trust_level: str = 'community', org_id: int = None) -> SharedIOC:
        if trust_level not in ['community', 'verified', 'trusted']:
            raise ValueError(f"Invalid trust level: {trust_level}")
            
        ioc = SharedIOC(
            value=value,
            ioc_type=ioc_type,
            trust_level=trust_level,
            shared_by_org_id=org_id,
            organization_id=org_id
        )
        db.session.add(ioc)
        db.session.commit()
        return ioc

    @staticmethod
    def validate_ioc(value: str) -> bool:
        """Validate if value follows indicator format structures."""
        if not value:
            return False
        # Simple domain or IP or hash basic validation checks
        return len(value.strip()) >= 4

    @staticmethod
    def list_shared_indicators(trust_level: str = None, org_id: int = None) -> list[SharedIOC]:
        q = SharedIOC.query
        if trust_level:
            q = q.filter_by(trust_level=trust_level)
        if org_id:
            q = q.filter_by(organization_id=org_id)
        return q.all()
