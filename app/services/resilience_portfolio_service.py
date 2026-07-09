"""
ResiliencePortfolioService - Phase 37 Cyber Resilience Portfolio.
"""
import datetime
from app.extensions import db
from app.models.resilience_portfolio_metric import ResiliencePortfolioMetric
from app.models.resilience_investment_plan import ResilienceInvestmentPlan
from app.services.resilience_planning_service import ResiliencePlanningService
from app.services.portfolio_optimization_service import PortfolioOptimizationService


class ResiliencePortfolioService:
    @staticmethod
    def calculate_before_state(plan_id, org_id):
        # Baseline loss expected
        from app.services.risk_portfolio_service import RiskPortfolioService
        return RiskPortfolioService.calculate_expected_annual_loss(org_id)

    @staticmethod
    def calculate_after_state(plan_id, org_id):
        # Expected loss after plan items are approved/implemented
        before = ResiliencePortfolioService.calculate_before_state(plan_id, org_id)
        loss_red, _ = ResiliencePlanningService.calculate_expected_improvement(plan_id, org_id)
        return max(0.0, before - loss_red)

    @staticmethod
    def calculate_risk_reduction(plan_id, org_id):
        before = ResiliencePortfolioService.calculate_before_state(plan_id, org_id)
        after = ResiliencePortfolioService.calculate_after_state(plan_id, org_id)
        if before == 0:
            return 0.0
        return round(((before - after) / before) * 100.0, 2)

    @staticmethod
    def calculate_resilience_improvement(plan_id, org_id):
        _, res_imp = ResiliencePlanningService.calculate_expected_improvement(plan_id, org_id)
        return res_imp

    @staticmethod
    def calculate_efficiency(plan_id, org_id):
        return PortfolioOptimizationService.calculate_efficiency(plan_id, org_id)

    @staticmethod
    def calculate_appetite_alignment(plan_id, org_id):
        # Returns alignment score between 0 and 100.
        # If expected loss after implementation satisfies the maximum annualized loss limit, score = 100, else score = 50.
        from app.services.risk_portfolio_service import RiskPortfolioService
        appetite = RiskPortfolioService.check_risk_appetite(org_id)
        after = ResiliencePortfolioService.calculate_after_state(plan_id, org_id)
        limit = appetite.get('maximum_annualized_loss_limit', 1000000.0)
        return 100.0 if after <= limit else 50.0

    @staticmethod
    def save_metric(plan_id, org_id):
        plan = ResilienceInvestmentPlan.query.filter_by(id=plan_id, organization_id=org_id).first()
        if not plan:
            return None

        before_loss = ResiliencePortfolioService.calculate_before_state(plan_id, org_id)
        after_loss = ResiliencePortfolioService.calculate_after_state(plan_id, org_id)
        reduction = ResiliencePortfolioService.calculate_risk_reduction(plan_id, org_id)
        res_improvement = ResiliencePortfolioService.calculate_resilience_improvement(plan_id, org_id)

        eff = ResiliencePortfolioService.calculate_efficiency(plan_id, org_id)
        align = ResiliencePortfolioService.calculate_appetite_alignment(plan_id, org_id)

        metric = ResiliencePortfolioMetric(
            plan_id=plan_id,
            total_budget=plan.budget_limit,
            allocated_budget=ResiliencePlanningService.calculate_budget_usage(plan_id, org_id),
            expected_loss_before=before_loss,
            expected_loss_after=after_loss,
            risk_reduction_percentage=reduction,
            resilience_before=85.0,
            resilience_after=85.0 + res_improvement,
            portfolio_efficiency_score=eff,
            risk_appetite_alignment_score=align,
            measured_at=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(metric)
        db.session.commit()
        return metric

    @staticmethod
    def portfolio_summary(org_id):
        metrics = ResiliencePortfolioMetric.query.filter_by(organization_id=org_id).all()
        if not metrics:
            return {"total_tracked_plans": 0, "avg_efficiency_score": 0.0}
        avg_eff = sum(m.portfolio_efficiency_score for m in metrics) / len(metrics)
        return {
            "total_tracked_plans": len(metrics),
            "avg_efficiency_score": round(avg_eff, 2)
        }
