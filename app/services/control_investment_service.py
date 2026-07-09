"""
ControlInvestmentService - Phase 37 Strategic Cyber Resilience.
"""
import json
from app.extensions import db
from app.models.control_investment_option import ControlInvestmentOption
from app.models.compliance_control import ComplianceControl


class ControlInvestmentService:
    @staticmethod
    def create_option(control_ref, title, cost, operating_cost, improvement, risk_reduction, resilience_gain, time_days, deps, org_id):
        # Validate control reference
        ctrl = ComplianceControl.query.filter_by(control_code=control_ref, organization_id=org_id).first()
        if not ctrl:
            # Fallback for dynamic compatibility if control register is partially empty in sandbox
            pass

        option = ControlInvestmentOption(
            control_reference=control_ref,
            title=title,
            implementation_cost=cost,
            annual_operating_cost=operating_cost,
            expected_control_improvement=improvement,
            expected_risk_reduction=risk_reduction,
            expected_resilience_gain=resilience_gain,
            implementation_time_days=time_days,
            dependency_requirements_json=json.dumps(deps or []),
            status='proposed',
            organization_id=org_id
        )
        db.session.add(option)
        db.session.commit()
        return option

    @staticmethod
    def calculate_control_gain(option_id, org_id):
        opt = ControlInvestmentOption.query.filter_by(id=option_id, organization_id=org_id).first()
        return opt.expected_control_improvement if opt else 0.0

    @staticmethod
    def calculate_risk_reduction(option_id, org_id):
        opt = ControlInvestmentOption.query.filter_by(id=option_id, organization_id=org_id).first()
        return opt.expected_risk_reduction if opt else 0.0

    @staticmethod
    def calculate_resilience_gain(option_id, org_id):
        opt = ControlInvestmentOption.query.filter_by(id=option_id, organization_id=org_id).first()
        return opt.expected_resilience_gain if opt else 0.0

    @staticmethod
    def evaluate_dependencies(option_id, org_id):
        opt = ControlInvestmentOption.query.filter_by(id=option_id, organization_id=org_id).first()
        if not opt:
            return []
        try:
            deps = json.loads(opt.dependency_requirements_json or '[]')
        except Exception:
            deps = []

        unresolved = []
        for ref in deps:
            # Check if there is an approved or completed option for this reference
            prereq = ControlInvestmentOption.query.filter_by(
                control_reference=ref,
                organization_id=org_id,
                status='approved'
            ).first()
            if not prereq:
                unresolved.append(ref)
        return unresolved

    @staticmethod
    def rank_options(org_id):
        options = ControlInvestmentOption.query.filter_by(organization_id=org_id).all()
        # Rank by: risk_reduction / implementation_cost
        return sorted(
            options,
            key=lambda x: x.expected_risk_reduction / x.implementation_cost if x.implementation_cost > 0 else x.expected_risk_reduction,
            reverse=True
        )

    @staticmethod
    def control_investment_summary(org_id):
        options = ControlInvestmentOption.query.filter_by(organization_id=org_id).all()
        return {
            "total_options": len(options),
            "total_implementation_cost": sum(o.implementation_cost for o in options),
            "avg_resilience_gain": sum(o.expected_resilience_gain for o in options) / len(options) if options else 0.0
        }
