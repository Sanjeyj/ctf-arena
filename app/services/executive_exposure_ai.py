"""
ExecutiveExposureAI - Phase 34 Security Architecture, Exposure & Attack Surface Management Fabric.
Composes executive summary briefings of security architecture postures, exposure metrics, and remediation timelines using AIService.
"""
from app.services.ai_service import AIService
from app.services.exposure_inventory_service import ExposureInventoryService
from app.services.control_coverage_service import ControlCoverageService
from app.services.remediation_prioritization_service import RemediationPrioritizationService
from app.services.architecture_service import ArchitectureService
from app.services.attack_path_service import AttackPathService
import json


class ExecutiveExposureAI:

    @staticmethod
    def _sanitize(text: str) -> str:
        # Prompt injection check
        jailbreaks = ["ignore previous", "bypass filter", "system prompt", "jailbreak", "do anything now"]
        for j in jailbreaks:
            if j in text.lower():
                raise ValueError("Prompt injection detected")
        return text

    @staticmethod
    def summarize_attack_surface(org_id):
        summary = ExposureInventoryService.exposure_summary(org_id)
        prompt = f"Summarize the attack surface status: total assets {summary['total_assets']}, exposed count {summary['exposed_count']}, average exposure score {summary['avg_exposure_score']}/100."
        prompt = ExecutiveExposureAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def explain_critical_path(source_id, target_id, org_id):
        ap = AttackPathService.find_critical_path(source_id, target_id, org_id)
        if not ap:
            return "No critical attack path found."

        explanation = AttackPathService.explain_path(ap.id, org_id)
        prompt = f"Explain this critical attack path and its implications: {explanation}."
        prompt = ExecutiveExposureAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def recommend_remediation_priorities(org_id):
        summary = RemediationPrioritizationService.remediation_summary(org_id)
        prompt = f"Recommend priorities for remediation: total plans {summary['total_plans']}, approved {summary['approved_plans']}, completed {summary['completed_plans']}."
        prompt = ExecutiveExposureAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def summarize_control_gaps(org_id):
        gaps = ControlCoverageService.find_coverage_gaps(org_id)
        prompt = f"Summarize control coverage gaps found: {json.dumps(gaps)}."
        prompt = ExecutiveExposureAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def explain_architecture_risk(org_id):
        summary = ArchitectureService.architecture_summary(org_id)
        prompt = f"Explain the risk in architecture boundaries: total zones {summary['total_zones']}, total boundaries {summary['total_boundaries']}, boundary violations {summary['boundary_violations']}."
        prompt = ExecutiveExposureAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def generate_exposure_brief(org_id):
        sum_exp = ExposureInventoryService.exposure_summary(org_id)
        sum_arch = ArchitectureService.architecture_summary(org_id)
        prompt = f"Generate a brief for executives combining: avg exposure score {sum_exp['avg_exposure_score']} and boundary violations {sum_arch['boundary_violations']}."
        prompt = ExecutiveExposureAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp
