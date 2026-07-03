"""
ExecutiveResilienceAI - Phase 25 Cyber Resilience & Digital Enterprise.
Implements the Executive Resilience Copilot assistant endpoints and answering logic.
"""
from app.services.resilience_engine_service import ResilienceEngineService
from app.services.insurance_service import InsuranceService
from app.models.third_party_vendor import ThirdPartyVendor
from app.models.business_process import BusinessProcess

class ExecutiveResilienceAI:
    @staticmethod
    def summarize(organization_id: int) -> str:
        """Provide a summary of the organizational resilience posture."""
        score_info = ResilienceEngineService.calculate_resilience_score(organization_id)
        score = score_info['resilience_score']
        losses = InsuranceService.estimate_losses(organization_id)
        
        return (
            f"The organization's overall cyber resilience index is currently rated at **{score}/100**. "
            f"Estimated business downtime loss exposure is simulated at **${losses:,.2f}**. "
            f"Actions are recommended to review recovery RTO alignments and evaluate third-party risks."
        )

    @staticmethod
    def recommend(organization_id: int) -> str:
        """Suggest corrective actions based on current threat posture analysis."""
        rec_info = ResilienceEngineService.recommend_controls(organization_id)
        actions = rec_info.get('recommended_actions', [])
        if not actions:
            return "All resilience checks pass. No actions currently required."
        
        bullet_points = "\n".join(f"- {action}" for action in actions)
        return f"Based on our cyber resilience assessment, the following actions are recommended:\n{bullet_points}"

    @staticmethod
    def answer(question: str, organization_id: int) -> str:
        """Answer executive copilot questions dynamically."""
        q = question.lower()
        
        if "resilience score" in q or "our score" in q:
            score_info = ResilienceEngineService.calculate_resilience_score(organization_id)
            score = score_info['resilience_score']
            return f"Our current calculated cyber resilience score is **{score}/100**."
            
        elif "vendors" in q or "vendor risk" in q or "highest risk" in q:
            vendors = ThirdPartyVendor.query
            if organization_id:
                vendors = ThirdPartyVendor.tenant_filter(vendors, organization_id)
            high_risk = vendors.order_by(ThirdPartyVendor.risk_score.desc()).limit(3).all()
            
            if not high_risk:
                return "No high-risk vendors registered in the directory."
                
            vendor_list = ", ".join(f"{v.vendor_name} (Risk: {v.risk_score:.1f})" for v in high_risk)
            return f"The third-party vendors presenting the highest security risk are: {vendor_list}."
            
        elif "downtime loss" in q or "downtime" in q or "downtime exposure" in q:
            losses = InsuranceService.estimate_losses(organization_id)
            return f"The estimated maximum downtime business loss exposure is **${losses:,.2f}** based on current business impact analysis (BIA)."
            
        elif "assets" in q or "business continuity" in q:
            bps = BusinessProcess.query
            if organization_id:
                bps = BusinessProcess.tenant_filter(bps, organization_id)
            critical_bps = bps.filter(BusinessProcess.criticality == 'critical').all()
            
            if not critical_bps:
                return "No processes are currently labeled as 'critical' for business continuity."
                
            process_names = ", ".join(bp.name for bp in critical_bps)
            return f"The following processes directly affect business continuity: {process_names}."
            
        elif "controls" in q or "improve resilience" in q:
            return ExecutiveResilienceAI.recommend(organization_id)
            
        else:
            return (
                "Copilot is ready. Ask about 'resilience score', 'highest risk vendors', "
                "'estimated downtime loss', or 'controls to improve resilience'."
            )
