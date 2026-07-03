"""
ExecutiveCivilizationAI - Phase 28 Cyber Civilization Platform.
Provides AI advising, summarizing, and strategic policy recommendations.
"""
from app.services.civilization_service import CivilizationService
from app.services.economy_service import EconomyService
from app.models.cyber_nation import CyberNation


class ExecutiveCivilizationAI:
    @staticmethod
    def summarize(org_id: int) -> str:
        """Generate an AI summary of the Cyber Civilization state."""
        nations = CyberNation.query.filter_by(organization_id=org_id).all()
        composite = CivilizationService.calculate(org_id)
        
        summary = (
            f"Cyber Civilization Status Report: {len(nations)} cyber nation(s) under observation. "
            f"Composite maturity score of {composite:.2f}. "
        )
        if composite >= 0.7:
            summary += "Ecosystem is highly secure and mature."
        else:
            summary += "Ecosystem requires strategic investment in autonomous defense grids."
        return summary

    @staticmethod
    def advise(topic: str) -> str:
        """Get AI-generated advice text for a specific strategic topic."""
        advices = {
            'alliances': "Policy recommendation: Expand defense alliances to include trans-regional cyber partners. High trust indices lead to direct security correlation advantages.",
            'economy': "Policy recommendation: Increase R&D and workforce certification budgets. High workforce skill levels correlate with long-term ecosystem stability.",
            'grid': "Policy recommendation: Deploy additional autonomous defense grid endpoints to scale system readiness indices and limit containment degradation."
        }
        return advices.get(topic.lower(), f"Advisory on {topic!r}: Focus on continuous compliance alignment and defense-grid capacity scale-up.")

    @staticmethod
    def recommend(org_id: int) -> list:
        """Generate high-impact policy recommendations."""
        composite = CivilizationService.calculate(org_id)
        econ_info = EconomyService.workforce(org_id)
        
        recs = []
        if composite < 0.65:
            recs.append("CRITICAL: Strategic baseline index is below standard (0.65). Immediately build out extra R&D innovation projects.")
        if econ_info["total_workforce"] < 5:
            recs.append("HIGH PRIORITY: Certify and deploy more cybersecurity analysts to boost workforce readiness index.")
        
        recs.append("MONITOR: Synchronize trans-national defense grids weekly to ensure zero health drift.")
        return recs
