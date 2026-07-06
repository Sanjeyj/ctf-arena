"""
ExecutiveAssuranceAI - Phase 32 Cyber Trust, Assurance & Verification Fabric.
AI summaries, explanations, recommendations, and briefs reusing the existing AIService interface.
"""
from app.services.ai_service import AIService


class ExecutiveAssuranceAI:
    @staticmethod
    def summarize_trust_posture(org_id: int) -> str:
        """Generate trust posture summaries for organization."""
        prompt = f"Summarize zero trust posture and compliance status for organization {org_id}."
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def explain_failed_assurance(case_id: int, org_id: int) -> str:
        """Explain reasons for failed or low confidence assurance claims."""
        prompt = f"Explain low confidence or evidence gaps for assurance case ID {case_id} under organization {org_id}."
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def recommend_evidence_priorities(org_id: int) -> str:
        """Prioritize missing evidence collections recommendations."""
        prompt = f"Recommend priority evidence attachments for assurance validation under organization {org_id}."
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def summarize_supply_chain_risk(org_id: int) -> str:
        """Summarize SBOM and attestation risk analysis overview."""
        prompt = f"Summarize supply chain risk metrics, attestations, and SBOM status for organization {org_id}."
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def generate_assurance_brief(org_id: int) -> str:
        """Generate executive security trust wargame validation brief document."""
        prompt = f"Draft an executive security assurance and trust wargame validation brief for organization {org_id}."
        resp, _, _ = AIService.generate(prompt)
        return resp
