"""
InsuranceService - Phase 25 Cyber Resilience & Digital Enterprise.
Models cyber coverage plans, deductibles, downtime loss exposures, and guidelines.
"""
from app.extensions import db
from app.models.business_impact_analysis import BusinessImpactAnalysis
from app.models.insurance_policy import InsurancePolicy

class InsuranceService:
    @staticmethod
    def estimate_losses(organization_id: int) -> float:
        """Estimate total downtime financial loss exposure based on BIA parameters."""
        bia_query = BusinessImpactAnalysis.query
        if organization_id:
            bia_query = BusinessImpactAnalysis.tenant_filter(bia_query, organization_id)
        bias = bia_query.all()

        # Each financial impact level represents $100,000 in simulated business risk exposure
        total_loss = sum(bia.financial_impact * 100000.0 for bia in bias)
        return total_loss if total_loss > 0 else 250000.0 # Default baseline exposure

    @staticmethod
    def estimate_coverage(organization_id: int) -> float:
        """Estimate the sum of cyber insurance coverage currently active."""
        policy_query = InsurancePolicy.query
        if organization_id:
            policy_query = InsurancePolicy.tenant_filter(policy_query, organization_id)
        policies = policy_query.all()

        return sum(policy.coverage for policy in policies)

    @staticmethod
    def recommend_policy(organization_id: int) -> dict:
        """Recommend premium coverage and policy requirements based on simulated financial gap."""
        losses = InsuranceService.estimate_losses(organization_id)
        current_coverage = InsuranceService.estimate_coverage(organization_id)

        coverage_gap = max(0.0, losses - current_coverage)
        
        # Calculate suggested premium (e.g. 1.5% of coverage gap as simulated premium)
        recommended_premium = coverage_gap * 0.015
        recommended_deductible = coverage_gap * 0.05

        recommendations = []
        if coverage_gap > 0:
            recommendations.append(f"Acquire additional ${coverage_gap:,.2f} cyber risk transfer coverage.")
            recommendations.append("Implement automated business backups to reduce insurance deductibles by up to 20%.")
        else:
            recommendations.append("Active cyber insurance coverage meets estimated business loss exposures.")

        return {
            'organization_id': organization_id,
            'estimated_losses': losses,
            'current_coverage': current_coverage,
            'coverage_gap': coverage_gap,
            'recommended_additional_coverage': coverage_gap,
            'recommended_premium_estimate': recommended_premium,
            'recommended_deductible': recommended_deductible,
            'recommendations': recommendations
        }
