"""
PortfolioOptimizationService - Phase 37 Strategic Cyber Resilience.
"""
from app.extensions import db
from app.models.resilience_investment_plan import ResilienceInvestmentPlan
from app.models.investment_plan_item import InvestmentPlanItem
from app.services.hook_service import HookService


class PortfolioOptimizationService:
    @staticmethod
    def optimize_budget(plan_id, org_id):
        plan = ResilienceInvestmentPlan.query.filter_by(id=plan_id, organization_id=org_id).first()
        if not plan:
            raise ValueError("Plan not found or access denied")

        HookService.trigger_hook('before_portfolio_optimization', plan_id=plan_id, org_id=org_id)

        candidates = plan.items.all()
        # Knapsack dynamic/greedy optimization
        # Rank by: (expected_loss_reduction + expected_resilience_improvement) / allocated_budget
        ranked = sorted(
            candidates,
            key=lambda x: (x.expected_loss_reduction + x.expected_resilience_improvement) / x.allocated_budget if x.allocated_budget > 0 else 0.0,
            reverse=True
        )

        budget_remaining = plan.budget_limit
        selected = []
        for c in ranked:
            if c.allocated_budget < 0:
                continue
            if c.allocated_budget <= budget_remaining:
                c.status = 'selected'
                budget_remaining -= c.allocated_budget
                selected.append(c)
            else:
                c.status = 'deferred'

        db.session.commit()

        HookService.trigger_hook('after_portfolio_optimization', plan_id=plan_id, org_id=org_id)
        return selected

    @staticmethod
    def rank_candidates(plan_id, org_id):
        plan = ResilienceInvestmentPlan.query.filter_by(id=plan_id, organization_id=org_id).first()
        if not plan:
            return []
        items = plan.items.all()
        return sorted(
            items,
            key=lambda x: (x.expected_loss_reduction + x.expected_resilience_improvement) / x.allocated_budget if x.allocated_budget > 0 else 0.0,
            reverse=True
        )

    @staticmethod
    def calculate_efficiency(plan_id, org_id):
        plan = ResilienceInvestmentPlan.query.filter_by(id=plan_id, organization_id=org_id).first()
        if not plan:
            return 0.0
        selected = plan.items.filter_by(status='selected').all()
        cost = sum(x.allocated_budget for x in selected)
        benefit = sum(x.expected_loss_reduction + x.expected_resilience_improvement * 1000 for x in selected)  # Resilience scaled to comparable dollar unit
        if cost == 0:
            return round(benefit, 2)
        return round(benefit / cost, 2)

    @staticmethod
    def calculate_marginal_risk_reduction(plan_id, item_id, org_id):
        item = InvestmentPlanItem.query.filter_by(id=item_id, plan_id=plan_id, organization_id=org_id).first()
        if not item:
            return 0.0
        return item.expected_loss_reduction

    @staticmethod
    def calculate_resilience_gain(plan_id, item_id, org_id):
        item = InvestmentPlanItem.query.filter_by(id=item_id, plan_id=plan_id, organization_id=org_id).first()
        if not item:
            return 0.0
        return item.expected_resilience_improvement

    @staticmethod
    def compare_portfolios(plan_id1, plan_id2, org_id):
        p1 = ResilienceInvestmentPlan.query.filter_by(id=plan_id1, organization_id=org_id).first()
        p2 = ResilienceInvestmentPlan.query.filter_by(id=plan_id2, organization_id=org_id).first()
        if not p1 or not p2:
            return None

        e1 = PortfolioOptimizationService.calculate_efficiency(plan_id1, org_id)
        e2 = PortfolioOptimizationService.calculate_efficiency(plan_id2, org_id)

        return {
            "plan1": {"id": plan_id1, "efficiency": e1},
            "plan2": {"id": plan_id2, "efficiency": e2}
        }

    @staticmethod
    def recommend_portfolio(plan_id, org_id):
        # Solves budget knapsack and returns optimized plan dictionary
        PortfolioOptimizationService.optimize_budget(plan_id, org_id)
        plan = ResilienceInvestmentPlan.query.get(plan_id)
        plan.status = 'recommended'
        db.session.commit()
        return plan
