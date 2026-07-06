"""
UniverseService - Phase 30 Unified Cyber Defense Universe.
Manages root universe lifecycle: create, activate, pause, complete, and core metrics calculation.
"""
from app.extensions import db
from app.models.defense_universe import DefenseUniverse


class UniverseService:
    @staticmethod
    def create_universe(name: str, org_id: int, description: str = None, universe_type: str = 'default') -> DefenseUniverse:
        """Create a new defense universe."""
        uni = DefenseUniverse(
            name=name,
            description=description,
            universe_type=universe_type,
            status='draft',
            readiness_score=0.5,
            risk_score=0.3,
            resilience_score=0.5,
            organization_id=org_id
        )
        db.session.add(uni)
        db.session.commit()
        return uni

    @staticmethod
    def activate(universe_id: int, org_id: int) -> DefenseUniverse:
        """Move universe status to active."""
        uni = db.session.get(DefenseUniverse, universe_id)
        if not uni or uni.organization_id != org_id:
            return None
        uni.status = 'active'
        db.session.commit()
        return uni

    @staticmethod
    def pause(universe_id: int, org_id: int) -> DefenseUniverse:
        """Pause the universe simulation."""
        uni = db.session.get(DefenseUniverse, universe_id)
        if not uni or uni.organization_id != org_id:
            return None
        uni.status = 'paused'
        db.session.commit()
        return uni

    @staticmethod
    def complete(universe_id: int, org_id: int) -> DefenseUniverse:
        """Complete the universe simulation."""
        uni = db.session.get(DefenseUniverse, universe_id)
        if not uni or uni.organization_id != org_id:
            return None
        uni.status = 'completed'
        db.session.commit()
        return uni

    @staticmethod
    def get_posture(universe_id: int, org_id: int) -> dict:
        """Retrieve unified posture summary score dictionary."""
        uni = db.session.get(DefenseUniverse, universe_id)
        if not uni or uni.organization_id != org_id:
            return None
        return {
            'universe_id': uni.id,
            'status': uni.status,
            'readiness_score': uni.readiness_score,
            'risk_score': uni.risk_score,
            'resilience_score': uni.resilience_score,
        }

    @staticmethod
    def calculate_readiness(universe_id: int, org_id: int) -> float:
        """Perform simple math aggregation to compute dynamic readiness score."""
        uni = db.session.get(DefenseUniverse, universe_id)
        if not uni or uni.organization_id != org_id:
            return 0.0
        from app.models.defense_domain import DefenseDomain
        domains = DefenseDomain.query.filter_by(universe_id=universe_id, organization_id=org_id).all()
        if not domains:
            return uni.readiness_score
        avg_readiness = sum(d.readiness_score for d in domains) / len(domains)
        avg_health = sum(d.health_score for d in domains) / len(domains)
        new_readiness = round((avg_readiness + avg_health) / 2.0, 3)
        uni.readiness_score = new_readiness
        db.session.commit()
        return new_readiness
