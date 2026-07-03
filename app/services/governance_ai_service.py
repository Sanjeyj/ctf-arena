"""
Governance AI Service - Phase 23 Executive Governance AI.
Answers corporate compliance, failed control checks, and risks mitigations questions.
"""
from app.extensions import db
from app.models.compliance_control import ComplianceControl
from app.models.risk_register import RiskRegister
from app.models.policy import Policy

class GovernanceAIService:

    @staticmethod
    def answer_governance_question(question: str, org_id: int = None) -> dict:
        q_lower = question.lower()
        
        if "gap" in q_lower or "compliance" in q_lower:
            total_count = ComplianceControl.query.count()
            failed_count = ComplianceControl.query.filter_by(status='failed').count()
            summary = f"Compliance check gaps analysis: {failed_count} out of {total_count} controls are currently in failed state."
            recommendation = "Draft remedial runbooks addressing failed endpoints controls."
            chart_data = {"failed_controls": failed_count, "total_controls": total_count}
            
        elif "control" in q_lower:
            failed_controls = ComplianceControl.query.filter_by(status='failed').all()
            codes = [c.control_code for c in failed_controls]
            summary = f"Failed security controls checks: {', '.join(codes) if codes else 'None'}."
            recommendation = "Review policy version validation and mandate policy acknowledgements."
            chart_data = {"failed_count": len(codes)}
            
        elif "risk" in q_lower:
            risks = RiskRegister.query.order_by(RiskRegister.risk_score.desc()).limit(3).all()
            scenarios = [r.scenario for r in risks]
            summary = f"Identified top threat scenarios: {', '.join(scenarios) if scenarios else 'None'}."
            recommendation = "Allocate mitigation plan resources to address threat registers."
            chart_data = {"top_risks_count": len(scenarios)}
            
        elif "department" in q_lower or "training" in q_lower:
            summary = "Training gap analysis highlights SecOps and engineering need mitigation simulation runs."
            recommendation = "Activate LMS Phase 19 reverse engineering malware lab lessons."
            chart_data = {"pending_depts_count": 2}
            
        else:
            summary = "Governance AI Copilot dashboard active. Ask about failed controls or GRC gaps."
            recommendation = "Execute GRC audit checks scans."
            chart_data = {}

        return {
            "question": question,
            "summary": summary,
            "recommendation": recommendation,
            "chart_data": chart_data
        }
