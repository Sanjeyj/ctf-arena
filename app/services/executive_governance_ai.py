from app.services.ai_service import AIService
from app.services.decision_intelligence_service import DecisionIntelligenceService
from app.services.policy_conflict_service import PolicyConflictService
from app.services.governance_scorecard_service import GovernanceScorecardService
from app.services.decision_outcome_service import DecisionOutcomeService
from app.services.governance_drift_service import GovernanceDriftService


class ExecutiveGovernanceAI:

    @staticmethod
    def _sanitize(text: str) -> str:
        jailbreaks = ["ignore previous", "bypass filter", "system prompt", "jailbreak", "do anything now"]
        for j in jailbreaks:
            if j in text.lower():
                raise ValueError("Prompt injection detected")
        return text

    @staticmethod
    def summarize_decision_landscape(org_id):
        summary = DecisionIntelligenceService.decision_summary(org_id)
        prompt = f"Summarize the enterprise security decision landscape. Total Contexts: {summary.get('total_contexts')}. Total Recommendations: {summary.get('total_recommendations')}."
        prompt = ExecutiveGovernanceAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def explain_policy_conflicts(org_id):
        summary = PolicyConflictService.conflict_summary(org_id)
        prompt = f"Explain active policy conflicts. Total Conflicts: {summary.get('total_conflicts')}. Open: {summary.get('open_conflicts')}. Critical: {summary.get('critical_conflicts')}."
        prompt = ExecutiveGovernanceAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def recommend_governance_priorities(org_id):
        prompt = "Recommend governance scorecard priorities and objective tracking optimization routes."
        prompt = ExecutiveGovernanceAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def explain_decision_outcomes(org_id):
        summary = DecisionOutcomeService.outcome_summary(org_id)
        prompt = f"Explain the variance of security decision outcomes. Total Outcomes: {summary.get('total_outcomes')}. Effective Outcomes: {summary.get('effective_outcomes')}."
        prompt = ExecutiveGovernanceAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def summarize_governance_drift(org_id):
        summary = GovernanceDriftService.drift_summary(org_id)
        prompt = f"Summarize active drift alerts. Active Drift Records: {summary.get('active_drift_records')}. Critical Drift: {summary.get('critical_governance_drift')}."
        prompt = ExecutiveGovernanceAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def compare_policy_options(org_id):
        prompt = "Compare alternative policy optimization runs and efficiency tradeoffs."
        prompt = ExecutiveGovernanceAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def generate_governance_brief(org_id):
        scorecard = GovernanceScorecardService.scorecard_summary(org_id)
        prompt = f"Compose a consolidated executive governance brief. Overall score: {scorecard.get('overall_score')}. Risk Alignment: {scorecard.get('risk_alignment')}."
        prompt = ExecutiveGovernanceAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp
