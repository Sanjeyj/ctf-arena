"""
ExecutiveValidationAI - Phase 35 Continuous Security Validation.
Formulates executive briefings regarding posture evaluations, detection gaps, and regressions using AIService.
"""
from app.services.ai_service import AIService
from app.services.defense_effectiveness_service import DefenseEffectivenessService
from app.services.validation_regression_service import ValidationRegressionService
from app.services.detection_validation_service import DetectionValidationService
from app.models.validation_execution import ValidationExecution


class ExecutiveValidationAI:

    @staticmethod
    def _sanitize(text: str) -> str:
        # Prompt injection check
        jailbreaks = ["ignore previous", "bypass filter", "system prompt", "jailbreak", "do anything now"]
        for j in jailbreaks:
            if j in text.lower():
                raise ValueError("Prompt injection detected")
        return text

    @staticmethod
    def summarize_validation_posture(org_id):
        summary = DefenseEffectivenessService.effectiveness_summary(org_id)
        prompt = f"Summarize the continuous security validation posture. Composite rating score: {summary.get('composite_score')}/100."
        prompt = ExecutiveValidationAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def explain_failed_validation(execution_id, org_id):
        exec_record = ValidationExecution.query.filter_by(id=execution_id, organization_id=org_id).first()
        if not exec_record:
            return "No validation execution found."
        prompt = f"Explain the failed validation execution ID {execution_id} with result score {exec_record.result_score}."
        prompt = ExecutiveValidationAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def recommend_validation_priorities(org_id):
        prompt = "Recommend continuous security validation priorities for next quarter based on gaps."
        prompt = ExecutiveValidationAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def summarize_detection_gaps(org_id):
        gaps = DetectionValidationService.find_detection_gaps(org_id)
        prompt = f"Summarize the following detection validation gaps: {gaps}."
        prompt = ExecutiveValidationAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def explain_regressions(org_id):
        summary = ValidationRegressionService.regression_summary(org_id)
        prompt = f"Explain the recent validation regressions summary: open {summary.get('open_count')} regressions."
        prompt = ExecutiveValidationAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp

    @staticmethod
    def generate_defense_effectiveness_brief(org_id):
        summary = DefenseEffectivenessService.effectiveness_summary(org_id)
        prompt = f"Generate a brief for executives combining: control effectiveness {summary.get('control_effectiveness')} and composite score {summary.get('composite_score')}."
        prompt = ExecutiveValidationAI._sanitize(prompt)
        resp, _, _ = AIService.generate(prompt)
        return resp
