"""
ExecutiveRiskAI - Phase 36 Cyber Risk Quantification.
"""
from app.services.ai_service import AIService
from app.services.risk_portfolio_service import RiskPortfolioService
from app.models.quantitative_risk_scenario import QuantitativeRiskScenario
from app.models.risk_simulation_run import RiskSimulationRun


class ExecutiveRiskAI:

    @staticmethod
    def _sanitize(text: str) -> str:
        # Prompt injection validation
        jailbreaks = ["ignore previous", "bypass filter", "system prompt", "jailbreak", "do anything now"]
        for j in jailbreaks:
            if j in text.lower():
                raise ValueError("Prompt injection detected")
        return text

    @staticmethod
    def summarize_risk_portfolio(org_id):
        summary = RiskPortfolioService.portfolio_summary(org_id)
        prompt = f"Summarize the quantitative cyber risk portfolio. Expected Annual Loss: {summary.get('expected_annual_loss')} USD. Average Inherent Risk: {summary.get('average_inherent_risk')}."
        prompt = ExecutiveRiskAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def explain_loss_exposure(scenario_id, org_id):
        scenario = QuantitativeRiskScenario.query.filter_by(id=scenario_id, organization_id=org_id).first()
        if not scenario:
            return "No scenario found."
        prompt = f"Explain the loss exposure for scenario {scenario.name} with inherent risk score {scenario.inherent_risk_score}."
        prompt = ExecutiveRiskAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def recommend_investment_priorities(org_id):
        prompt = "Recommend security investment priorities and optimization routes based on ROSI metrics."
        prompt = ExecutiveRiskAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def explain_residual_risk(scenario_id, org_id):
        scenario = QuantitativeRiskScenario.query.filter_by(id=scenario_id, organization_id=org_id).first()
        if not scenario:
            return "No scenario found."
        prompt = f"Explain the residual risk score of {scenario.residual_risk_score} after mitigations for scenario {scenario.name}."
        prompt = ExecutiveRiskAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def summarize_risk_appetite_breaches(org_id):
        appetite = RiskPortfolioService.check_risk_appetite(org_id)
        prompt = f"Summarize the following risk appetite checks: breached status: {appetite.get('appetite_breached')}. EAL: {appetite.get('expected_annual_loss')} limit: {appetite.get('maximum_annualized_loss_limit')}."
        prompt = ExecutiveRiskAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def generate_quantitative_risk_brief(org_id):
        summary = RiskPortfolioService.portfolio_summary(org_id)
        prompt = f"Generate a brief combining: EAL {summary.get('expected_annual_loss')} and portfolio efficiency {summary.get('portfolio_efficiency_score')}."
        prompt = ExecutiveRiskAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp
