"""
RiskPortfolioService - Phase 36 Cyber Risk Quantification.
"""
import datetime
from app.extensions import db
from app.models.quantitative_risk_scenario import QuantitativeRiskScenario
from app.models.risk_simulation_run import RiskSimulationRun
from app.models.risk_appetite_profile import RiskAppetiteProfile
from app.models.risk_portfolio_metric import RiskPortfolioMetric
from app.models.security_investment import SecurityInvestment
from app.services.risk_simulation_service import RiskSimulationService
from app.services.hook_service import HookService


class RiskPortfolioService:
    @staticmethod
    def calculate_inherent_risk(org_id):
        scenarios = QuantitativeRiskScenario.query.filter_by(organization_id=org_id).all()
        if not scenarios:
            return 0.0
        return round(sum(s.inherent_risk_score for s in scenarios) / len(scenarios), 2)

    @staticmethod
    def calculate_residual_risk(org_id):
        scenarios = QuantitativeRiskScenario.query.filter_by(organization_id=org_id).all()
        if not scenarios:
            return 0.0
        return round(sum(s.residual_risk_score for s in scenarios) / len(scenarios), 2)

    @staticmethod
    def calculate_expected_annual_loss(org_id):
        scenarios = QuantitativeRiskScenario.query.filter_by(organization_id=org_id).all()
        if not scenarios:
            return 0.0
        return round(sum(RiskSimulationService.calculate_expected_annual_loss(s.id, org_id) for s in scenarios), 2)

    @staticmethod
    def calculate_portfolio_efficiency(org_id):
        # Efficiency = Total Expected Loss Reduction / Total Investment Cost
        investments = SecurityInvestment.query.filter_by(organization_id=org_id).all()
        total_cost = sum(i.cost for i in investments)
        total_reduction = sum(i.expected_loss_reduction for i in investments)
        if total_cost == 0:
            return round(total_reduction, 2)
        return round(total_reduction / total_cost, 2)

    @staticmethod
    def compare_portfolios(org_id):
        # Queries past metrics to compare deltas
        prev = RiskPortfolioMetric.query.filter_by(organization_id=org_id).order_by(RiskPortfolioMetric.id.desc()).offset(1).first()
        current = RiskPortfolioMetric.query.filter_by(organization_id=org_id).order_by(RiskPortfolioMetric.id.desc()).first()

        if not prev or not current:
            return {"delta_eal": 0.0, "delta_efficiency": 0.0}

        return {
            "delta_eal": round(current.expected_annual_loss - prev.expected_annual_loss, 2),
            "delta_efficiency": round(current.portfolio_efficiency_score - prev.portfolio_efficiency_score, 2)
        }

    @staticmethod
    def check_risk_appetite(org_id):
        profile = RiskAppetiteProfile.query.filter_by(organization_id=org_id, status='active').first()
        if not profile:
            profile = RiskAppetiteProfile.query.filter_by(organization_id=org_id).order_by(RiskAppetiteProfile.id.desc()).first()
        if not profile:
            return {"status": "no_active_profile", "appetite_breached": False}

        # Hook triggers
        HookService.trigger_hook('before_risk_appetite_check', appetite_id=profile.id, org_id=org_id)

        scenarios = QuantitativeRiskScenario.query.filter_by(organization_id=org_id).all()
        eal = RiskPortfolioService.calculate_expected_annual_loss(org_id)
        max_residual = max([s.residual_risk_score for s in scenarios]) if scenarios else 0.0

        # Check thresholds
        eal_breached = eal > profile.maximum_annualized_loss
        score_breached = max_residual > profile.maximum_residual_risk_score
        is_breached = eal_breached or score_breached

        results = {
            "profile_name": profile.name,
            "expected_annual_loss": eal,
            "maximum_annualized_loss_limit": profile.maximum_annualized_loss,
            "eal_breached": eal_breached,
            "maximum_residual_risk_score_limit": profile.maximum_residual_risk_score,
            "residual_risk_score_breached": score_breached,
            "appetite_breached": is_breached
        }

        HookService.trigger_hook('after_risk_appetite_check', appetite_id=profile.id, org_id=org_id, is_breached=is_breached)
        return results

    @staticmethod
    def portfolio_summary(org_id):
        scenarios = QuantitativeRiskScenario.query.filter_by(organization_id=org_id).all()
        eal = RiskPortfolioService.calculate_expected_annual_loss(org_id)
        avg_inherent = RiskPortfolioService.calculate_inherent_risk(org_id)
        avg_residual = RiskPortfolioService.calculate_residual_risk(org_id)
        efficiency = RiskPortfolioService.calculate_portfolio_efficiency(org_id)

        # Retrieve investments cost
        investments = SecurityInvestment.query.filter_by(organization_id=org_id).all()
        total_cost = sum(i.cost for i in investments)

        # Save metric history
        metric = RiskPortfolioMetric(
            metric_type='composite',
            total_inherent_risk=avg_inherent,
            total_residual_risk=avg_residual,
            expected_annual_loss=eal,
            risk_reduction_value=avg_inherent - avg_residual,
            investment_cost=total_cost,
            portfolio_efficiency_score=efficiency,
            measured_at=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(metric)
        db.session.commit()

        appetite = RiskPortfolioService.check_risk_appetite(org_id)

        return {
            "total_scenarios": len(scenarios),
            "expected_annual_loss": eal,
            "average_inherent_risk": avg_inherent,
            "average_residual_risk": avg_residual,
            "portfolio_efficiency_score": efficiency,
            "appetite_status": appetite
        }
