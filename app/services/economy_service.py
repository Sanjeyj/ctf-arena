"""
EconomyService - Phase 28 Cyber Civilization Platform.
Manages investment ledgers, projects security growth, and computes workforce skill metrics.
"""
from app.extensions import db
from app.models.security_economy import SecurityEconomy
from app.models.workforce_profile import WorkforceProfile


class EconomyService:
    @staticmethod
    def growth(org_id: int) -> float:
        """Calculate projected annual economic growth rate."""
        econ = SecurityEconomy.query.filter_by(organization_id=org_id).first()
        if not econ:
            return 0.05
        # Compound formula baseline (simulation)
        projected = econ.growth_rate * (1.0 + (econ.workforce_score * 0.1))
        return round(projected, 3)

    @staticmethod
    def investment(amount: float, org_id: int) -> SecurityEconomy:
        """Record investment and adjust market value / growth score."""
        econ = SecurityEconomy.query.filter_by(organization_id=org_id).first()
        if not econ:
            econ = SecurityEconomy(
                investment=0.0,
                growth_rate=0.05,
                workforce_score=0.7,
                market_value=1000000.0,
                organization_id=org_id
            )
            db.session.add(econ)
            db.session.commit()

        econ.investment += amount
        econ.market_value += (amount * 1.5)
        # Increase growth score up to a maximum on large investments
        econ.growth_rate = min(0.25, econ.growth_rate + (amount / 1000000.0) * 0.01)
        db.session.commit()
        return econ

    @staticmethod
    def workforce(org_id: int) -> dict:
        """Retrieve workforce metrics and baseline experience rating."""
        profiles = WorkforceProfile.query.filter_by(organization_id=org_id).all()
        if not profiles:
            return {'total_workforce': 0, 'avg_skill': 0.0, 'capacity': 'low'}
        
        total = len(profiles)
        avg_skill = sum(p.skill_score for p in profiles) / total
        capacity = "high" if avg_skill >= 0.75 else ("medium" if avg_skill >= 0.5 else "low")
        return {
            'total_workforce': total,
            'avg_skill': round(avg_skill, 3),
            'capacity': capacity
        }
