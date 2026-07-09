"""
ExecutiveStrategyAI - Phase 37 Cyber Resilience Strategic Planning.
"""
from app.services.ai_service import AIService
from app.services.stress_testing_service import StressTestingService
from app.services.resilience_portfolio_service import ResiliencePortfolioService


class ExecutiveStrategyAI:

    @staticmethod
    def _sanitize(text: str) -> str:
        # Prompt injection validation
        jailbreaks = ["ignore previous", "bypass filter", "system prompt", "jailbreak", "do anything now"]
        for j in jailbreaks:
            if j in text.lower():
                raise ValueError("Prompt injection detected")
        return text

    @staticmethod
    def summarize_stress_test_results(org_id):
        summary = StressTestingService.stress_summary(org_id)
        prompt = f"Summarize strategic cyber stress testing outcomes. Runs completed: {summary.get('total_runs')}. Average Stressed Loss: {summary.get('avg_stressed_loss')} USD."
        prompt = ExecutiveStrategyAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def explain_concentration_risk(org_id):
        prompt = "Explain concentration and dependency risk vectors within critical business processes."
        prompt = ExecutiveStrategyAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def recommend_resilience_investments(org_id):
        prompt = "Recommend strategic resilience investments and optimization paths under budget limits."
        prompt = ExecutiveStrategyAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def compare_strategic_options(org_id):
        prompt = "Compare strategic investment portfolios and efficiency gains."
        prompt = ExecutiveStrategyAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def explain_budget_tradeoffs(org_id):
        prompt = "Explain budget constraints and marginal risk reduction tradeoffs."
        prompt = ExecutiveStrategyAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def summarize_risk_appetite_alignment(org_id):
        prompt = "Summarize the alignment between cybersecurity strategic investments and executive risk appetite limits."
        prompt = ExecutiveStrategyAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def generate_strategic_resilience_brief(org_id):
        prompt = "Generate a strategic resilience brief detailing stress profiles and investment prioritizations."
        prompt = ExecutiveStrategyAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp
