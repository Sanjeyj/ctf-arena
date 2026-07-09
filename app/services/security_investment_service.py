"""
SecurityInvestmentService - Phase 36 Cyber Risk Quantification.
"""
from app.extensions import db
from app.models.security_investment import SecurityInvestment
from app.services.hook_service import HookService


class SecurityInvestmentService:
    @staticmethod
    def create_investment(title, investment_category, cost, operating_cost, loss_reduction, risk_reduction, org_id):
        allowed_categories = ['control', 'detection', 'training', 'resilience', 'architecture', 'remediation', 'assurance', 'validation']
        if investment_category not in allowed_categories:
            raise ValueError(f"Invalid category. Must be one of: {allowed_categories}")

        # Hook triggers
        hook_results = HookService.trigger_hook(
            'before_investment_evaluation',
            title=title,
            investment_category=investment_category,
            cost=cost,
            expected_loss_reduction=loss_reduction,
            expected_risk_reduction=risk_reduction,
            org_id=org_id
        )
        for res in hook_results:
            if isinstance(res, dict):
                cost = res.get('cost', cost)
                loss_reduction = res.get('expected_loss_reduction', loss_reduction)

        investment = SecurityInvestment(
            title=title,
            investment_category=investment_category,
            cost=cost,
            annual_operating_cost=operating_cost,
            expected_loss_reduction=loss_reduction,
            expected_risk_reduction=risk_reduction,
            roi_score=0.0,
            rosi_score=0.0,
            priority_score=0.0,
            status='proposed',
            organization_id=org_id
        )
        db.session.add(investment)
        db.session.commit()

        # Calculate scores
        investment.roi_score = SecurityInvestmentService.calculate_roi(investment)
        investment.rosi_score = SecurityInvestmentService.calculate_rosi(investment)
        investment.priority_score = SecurityInvestmentService.calculate_priority(investment)
        db.session.commit()

        HookService.trigger_hook(
            'after_investment_evaluation',
            investment_id=investment.id,
            org_id=org_id,
            rosi_score=investment.rosi_score
        )

        return investment

    @staticmethod
    def calculate_roi(investment):
        if investment.cost == 0:
            return investment.expected_loss_reduction
        return round((investment.expected_loss_reduction / investment.cost) * 100.0, 2)

    @staticmethod
    def calculate_rosi(investment):
        # Formula: ROSI = (Expected Loss Reduction - Investment Cost) / Investment Cost * 100
        cost = investment.cost + investment.annual_operating_cost
        if cost == 0:
            return round(investment.expected_loss_reduction, 2)
        val = (investment.expected_loss_reduction - cost) / cost * 100.0
        return round(val, 2)

    @staticmethod
    def calculate_priority(investment):
        # Weighted combination: 60% ROSI performance normalized, 40% risk reduction percentage
        rosi = max(0.0, investment.rosi_score)
        val = (rosi * 0.6) + (investment.expected_risk_reduction * 0.4)
        return round(val, 2)

    @staticmethod
    def rank_investments(org_id):
        investments = SecurityInvestment.query.filter_by(organization_id=org_id).all()
        return sorted(investments, key=lambda x: x.rosi_score, reverse=True)

    @staticmethod
    def portfolio_summary(org_id):
        investments = SecurityInvestment.query.filter_by(organization_id=org_id).all()
        if not investments:
            return {"total_cost": 0.0, "expected_savings": 0.0, "avg_rosi": 0.0}

        cost = sum(i.cost for i in investments)
        savings = sum(i.expected_loss_reduction for i in investments)
        avg_rosi = sum(i.rosi_score for i in investments) / len(investments)

        return {
            "total_cost": round(cost, 2),
            "expected_savings": round(savings, 2),
            "avg_rosi": round(avg_rosi, 2)
        }
