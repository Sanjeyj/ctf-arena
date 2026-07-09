"""
ResiliencePlanningService - Phase 37 Strategic Cyber Resilience.
"""
from app.extensions import db
from app.models.resilience_investment_plan import ResilienceInvestmentPlan
from app.models.investment_plan_item import InvestmentPlanItem
from app.models.security_investment import SecurityInvestment
from app.services.hook_service import HookService


class ResiliencePlanningService:
    @staticmethod
    def create_plan(name, description, budget_limit, horizon_months, target_reduction, target_resilience, org_id):
        if budget_limit < 0:
            raise ValueError("budget_limit cannot be negative")

        plan = ResilienceInvestmentPlan(
            name=name,
            description=description,
            budget_limit=budget_limit,
            planning_horizon_months=horizon_months,
            target_risk_reduction=target_reduction,
            target_resilience_score=target_resilience,
            status='draft',
            organization_id=org_id
        )
        db.session.add(plan)
        db.session.commit()
        return plan

    @staticmethod
    def add_candidate(plan_id, investment_id, allocated_budget, org_id):
        plan = ResilienceInvestmentPlan.query.filter_by(id=plan_id, organization_id=org_id).first()
        if not plan:
            raise ValueError("Plan not found or access denied")
        inv = SecurityInvestment.query.filter_by(id=investment_id, organization_id=org_id).first()
        if not inv:
            raise ValueError("Investment not found or access denied")

        if allocated_budget < 0:
            raise ValueError("allocated_budget cannot be negative")

        # Check if already added
        existing = InvestmentPlanItem.query.filter_by(plan_id=plan_id, security_investment_id=investment_id).first()
        if existing:
            existing.allocated_budget = allocated_budget
            db.session.commit()
            return existing

        item = InvestmentPlanItem(
            plan_id=plan_id,
            security_investment_id=investment_id,
            allocated_budget=allocated_budget,
            expected_loss_reduction=inv.expected_loss_reduction,
            expected_resilience_improvement=inv.expected_risk_reduction / 5.0,  # Proxy estimate
            priority_rank=1,
            selection_reason="Candidate for strategic planning",
            status='candidate',
            organization_id=org_id
        )
        db.session.add(item)
        db.session.commit()
        return item

    @staticmethod
    def evaluate_candidate(item_id, org_id):
        item = InvestmentPlanItem.query.filter_by(id=item_id, organization_id=org_id).first()
        if not item:
            return None
        # Evaluates individual candidate's ROSI
        inv = SecurityInvestment.query.get(item.security_investment_id)
        if inv.cost == 0:
            item.priority_rank = 1
        else:
            rosi = (item.expected_loss_reduction - item.allocated_budget) / item.allocated_budget * 100.0 if item.allocated_budget > 0 else 0.0
            item.priority_rank = int(max(1, 100 - rosi))
        db.session.commit()
        return item

    @staticmethod
    def select_investments(plan_id, org_id):
        plan = ResilienceInvestmentPlan.query.filter_by(id=plan_id, organization_id=org_id).first()
        if not plan:
            return []

        items = plan.items.all()
        # Rank by expected_loss_reduction per dollar allocated
        sorted_items = sorted(items, key=lambda x: x.expected_loss_reduction / x.allocated_budget if x.allocated_budget > 0 else 0.0, reverse=True)

        current_spent = 0.0
        selected = []
        for item in sorted_items:
            if current_spent + item.allocated_budget <= plan.budget_limit:
                item.status = 'selected'
                current_spent += item.allocated_budget
                selected.append(item)
            else:
                item.status = 'deferred'
        db.session.commit()
        return selected

    @staticmethod
    def calculate_budget_usage(plan_id, org_id):
        plan = ResilienceInvestmentPlan.query.filter_by(id=plan_id, organization_id=org_id).first()
        if not plan:
            return 0.0
        return sum(item.allocated_budget for item in plan.items.filter_by(status='selected').all())

    @staticmethod
    def calculate_expected_improvement(plan_id, org_id):
        plan = ResilienceInvestmentPlan.query.filter_by(id=plan_id, organization_id=org_id).first()
        if not plan:
            return 0.0, 0.0
        selected_items = plan.items.filter_by(status='selected').all()
        tot_loss_red = sum(x.expected_loss_reduction for x in selected_items)
        tot_res_imp = sum(x.expected_resilience_improvement for x in selected_items)
        return tot_loss_red, tot_res_imp

    @staticmethod
    def approve_plan(plan_id, approved_by, org_id):
        plan = ResilienceInvestmentPlan.query.filter_by(id=plan_id, organization_id=org_id).first()
        if not plan:
            return None

        HookService.trigger_hook('before_resilience_plan_approval', plan_id=plan_id, org_id=org_id)

        plan.status = 'approved'
        plan.approved_by = approved_by
        # Approve all selected items
        for item in plan.items.all():
            if item.status == 'selected':
                item.status = 'approved'
                # Update underlying investment status to approved
                inv = SecurityInvestment.query.get(item.security_investment_id)
                inv.status = 'approved'
        db.session.commit()

        HookService.trigger_hook('after_resilience_plan_approval', plan_id=plan_id, org_id=org_id)
        return plan

    @staticmethod
    def plan_summary(plan_id, org_id):
        plan = ResilienceInvestmentPlan.query.filter_by(id=plan_id, organization_id=org_id).first()
        if not plan:
            return None
        usage = ResiliencePlanningService.calculate_budget_usage(plan.id, org_id)
        loss_red, res_imp = ResiliencePlanningService.calculate_expected_improvement(plan.id, org_id)
        return {
            "plan_id": plan.id,
            "name": plan.name,
            "status": plan.status,
            "budget_limit": plan.budget_limit,
            "allocated_budget": usage,
            "expected_loss_reduction": loss_red,
            "expected_resilience_improvement": res_imp
        }
