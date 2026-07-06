"""
ExecutiveControlAI - Phase 31 Cyber Platform Control Plane.
AI decision guidance summaries, degradation explanations, policy violation guidelines, and platform audits briefs.
"""
from app.extensions import db
from app.models.platform_service import PlatformService
from app.services.ai_service import AIService


class ExecutiveControlAI:
    @staticmethod
    def summarize_platform(org_id: int) -> str:
        """Generate platform health audit summary."""
        prompt = f"Summarize platform control health for organization {org_id}."
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def explain_degradation(service_id: int, org_id: int) -> str:
        """Explain reliability or health score degradation status."""
        srv = db.session.get(PlatformService, service_id)
        if not srv or srv.organization_id != org_id:
            return "Unauthorized or missing service."
        prompt = f"Explain degradation status for service {srv.service_name} with health {srv.health_score}."
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def recommend_priorities(org_id: int) -> str:
        """Provide prioritized list of operational changes recommendations."""
        prompt = f"Recommend priorities for control plane operations under organization {org_id}."
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def explain_policy_violation(policy_id: int, violation_desc: str, org_id: int) -> str:
        """Retrieve explanation advice guidelines for policy violations."""
        prompt = f"Explain policy violation for ID {policy_id} with description: {violation_desc}."
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def generate_governance_brief(org_id: int) -> str:
        """Draft complete executive platform security governance document brief."""
        prompt = f"Draft an executive governance brief for control plane operations under organization {org_id}."
        resp, _, _ = AIService.generate(prompt)
        return resp
