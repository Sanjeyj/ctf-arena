"""
ExecutiveUniverseAI - Phase 30 Unified Cyber Defense Universe.
Provides AI decision guidance brief summaries, priority recommendations, and what-if simulation comparison guides.
"""
from app.extensions import db
from app.models.defense_universe import DefenseUniverse
from app.services.ai_service import AIService


class ExecutiveUniverseAI:
    @staticmethod
    def summarize(universe_id: int, org_id: int) -> str:
        """Generate AI executive defense universe brief summary."""
        uni = db.session.get(DefenseUniverse, universe_id)
        if not uni or uni.organization_id != org_id:
            return "Unauthorized or missing universe."
        prompt = (
            f"Write a concise executive summary for defense universe: {uni.name}. "
            f"Readiness score is {uni.readiness_score}, risk score is {uni.risk_score}, "
            f"resilience score is {uni.resilience_score}."
        )
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def explain_risk(universe_id: int, org_id: int) -> str:
        """Retrieve AI assessment of current platform risks."""
        uni = db.session.get(DefenseUniverse, universe_id)
        if not uni or uni.organization_id != org_id:
            return "Unauthorized or missing universe."
        prompt = f"Analyze and explain risks associated with risk score: {uni.risk_score}."
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def recommend_priorities(universe_id: int, org_id: int) -> str:
        """Provide prioritized list of remediation suggestions."""
        uni = db.session.get(DefenseUniverse, universe_id)
        if not uni or uni.organization_id != org_id:
            return "Unauthorized or missing universe."
        prompt = f"Recommend security defense priorities for a universe with readiness: {uni.readiness_score}."
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def compare_scenarios(scenario_id_1: int, scenario_id_2: int, org_id: int) -> str:
        """Trace AI comparison across threat models configurations."""
        prompt = f"Compare scenario execution impact for ID {scenario_id_1} and ID {scenario_id_2} under org {org_id}."
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def generate_brief(universe_id: int, org_id: int) -> str:
        """Generate final operational brief guide overview."""
        uni = db.session.get(DefenseUniverse, universe_id)
        if not uni or uni.organization_id != org_id:
            return "Unauthorized or missing universe."
        prompt = (
            f"Draft a full board-ready operational cyber brief guide for {uni.name}. "
            f"Readiness: {uni.readiness_score}. Risk: {uni.risk_score}."
        )
        resp, _, _ = AIService.generate(prompt)
        return resp
