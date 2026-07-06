"""
ReliabilityService - Phase 31 Cyber Platform Control Plane.
Stores simulated SLI/SLO definitions, error budgets, and breach indicators.
"""
from app.extensions import db
from app.models.reliability_objective import ReliabilityObjective
from app.models.platform_service import PlatformService


class ReliabilityService:
    @staticmethod
    def create_objective(service_id: int, metric_name: str, target_value: float, org_id: int, measurement_window: str = '30d') -> ReliabilityObjective:
        """Register SLI/SLO target definition for a service."""
        srv = db.session.get(PlatformService, service_id)
        if not srv or srv.organization_id != org_id:
            return None
        obj = ReliabilityObjective(
            service_id=service_id,
            metric_name=metric_name,
            target_value=target_value,
            current_value=1.0,
            measurement_window=measurement_window,
            error_budget=1.0,
            status='compliant',
            organization_id=org_id
        )
        db.session.add(obj)
        db.session.commit()
        return obj

    @staticmethod
    def evaluate_objective(objective_id: int, current_value: float, org_id: int) -> ReliabilityObjective:
        """Evaluate current metrics, calculating error budgets and compliance breaches."""
        obj = db.session.get(ReliabilityObjective, objective_id)
        if not obj or obj.organization_id != org_id:
            return None
        
        obj.current_value = max(0.0, current_value)
        # Calculate error budget remaining: how far current is from 1.0 vs target
        # SLO error budget: 1.0 - target. Remaining: (current - target) / (1.0 - target)
        denom = (1.0 - obj.target_value)
        if abs(denom) < 1e-9:
            obj.error_budget = 1.0 if current_value >= obj.target_value else 0.0
        else:
            budget = (current_value - obj.target_value) / denom
            obj.error_budget = max(0.0, min(1.0, round(budget, 4)))

        obj.status = 'compliant' if obj.current_value >= obj.target_value else 'breaching'
        db.session.commit()
        return obj

    @staticmethod
    def calculate_error_budget(objective_id: int, org_id: int) -> float:
        """Return cached remaining error budget metric."""
        obj = db.session.get(ReliabilityObjective, objective_id)
        if not obj or obj.organization_id != org_id:
            return 0.0
        return obj.error_budget

    @staticmethod
    def detect_breach(org_id: int) -> list:
        """Identify all reliability objectives currently breaching targets."""
        return ReliabilityObjective.query.filter_by(status='breaching', organization_id=org_id).all()

    @staticmethod
    def reliability_summary(org_id: int) -> dict:
        """Report overview numbers for reliability engineering dashboard."""
        objs = ReliabilityObjective.query.filter_by(organization_id=org_id).all()
        if not objs:
            return {'total_objectives': 0, 'breach_count': 0, 'avg_budget': 1.0}
        breaches = sum(1 for o in objs if o.status == 'breaching')
        avg_budget = sum(o.error_budget for o in objs) / len(objs)
        return {
            'total_objectives': len(objs),
            'breach_count': breaches,
            'avg_budget': round(avg_budget, 3)
        }
