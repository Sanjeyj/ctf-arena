"""
VendorRiskService - Phase 25 Cyber Resilience & Digital Enterprise.
Monitors and updates third-party supply chain risks and compliance audits.
"""
from app.extensions import db
from app.models.third_party_vendor import ThirdPartyVendor
from app.models.vendor_assessment import VendorAssessment

class VendorRiskService:
    @staticmethod
    def assess_vendor(vendor_name: str, service_type: str, initial_risk: float, organization_id: int) -> ThirdPartyVendor:
        """Add a new third-party supplier profile."""
        vendor = ThirdPartyVendor(
            vendor_name=vendor_name,
            service_type=service_type,
            risk_score=initial_risk,
            contract_status='active',
            organization_id=organization_id
        )
        db.session.add(vendor)
        db.session.commit()
        return vendor

    @staticmethod
    def update_score(vendor_id: int, compliance_score: float, assessment_score: float) -> ThirdPartyVendor:
        """Create an audit assessment entry and adjust the vendor overall risk score."""
        vendor = ThirdPartyVendor.query.get(vendor_id)
        if not vendor:
            return None

        # Record detailed assessment logs
        assessment = VendorAssessment(
            vendor_id=vendor_id,
            compliance_score=compliance_score,
            assessment_score=assessment_score,
            recommendations=f"Compliance check yielded {compliance_score}%. Assessment yielded {assessment_score}%.",
            organization_id=vendor.organization_id
        )
        db.session.add(assessment)

        # Recalculate vendor risk: risk decreases as compliance and assessment scores increase
        # Perfect compliance & assessment = 0 risk; Worst = 100 risk.
        calculated_risk = 100.0 - (compliance_score * 0.5 + assessment_score * 0.5)
        vendor.risk_score = max(0.0, min(100.0, calculated_risk))
        
        db.session.commit()
        return vendor

    @staticmethod
    def calculate_risk(vendor_id: int) -> float:
        """Retrieve vendor risk rating directly or compute standard defaults."""
        vendor = ThirdPartyVendor.query.get(vendor_id)
        return vendor.risk_score if vendor else 0.0
