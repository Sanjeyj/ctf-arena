"""
RiskTreatmentService - Phase 36 Cyber Risk Quantification.
"""
from app.extensions import db
from app.models.risk_treatment_option import RiskTreatmentOption
from app.models.quantitative_risk_scenario import QuantitativeRiskScenario


class RiskTreatmentService:
    @staticmethod
    def create_option(scenario_id, treatment_type, title, description, estimated_cost, expected_risk_reduction, implementation_complexity, org_id):
        scenario = QuantitativeRiskScenario.query.filter_by(id=scenario_id, organization_id=org_id).first()
        if not scenario:
            raise ValueError("Scenario not found or access denied")

        allowed_types = ['mitigate', 'avoid', 'transfer_simulation', 'accept']
        if treatment_type not in allowed_types:
            raise ValueError(f"Invalid treatment_type. Must be one of: {allowed_types}")

        if not (0.0 <= expected_risk_reduction <= 100.0):
            raise ValueError("expected_risk_reduction must be between 0 and 100")

        option = RiskTreatmentOption(
            scenario_id=scenario_id,
            treatment_type=treatment_type,
            title=title,
            description=description,
            estimated_cost=estimated_cost,
            expected_risk_reduction=expected_risk_reduction,
            implementation_complexity=implementation_complexity,
            status='proposed',
            organization_id=org_id
        )
        db.session.add(option)
        db.session.commit()
        return option

    @staticmethod
    def calculate_residual_risk(scenario_id, reduction_pct, org_id):
        scenario = QuantitativeRiskScenario.query.filter_by(id=scenario_id, organization_id=org_id).first()
        if not scenario:
            return 0.0

        inherent = scenario.inherent_risk_score
        residual = inherent * (1.0 - (reduction_pct / 100.0))
        clamped = min(100.0, max(0.0, residual))
        return round(clamped, 2)

    @staticmethod
    def compare_treatments(scenario_id, org_id):
        scenario = QuantitativeRiskScenario.query.filter_by(id=scenario_id, organization_id=org_id).first()
        if not scenario:
            return []

        options = scenario.treatment_options.all()
        result = []
        for o in options:
            cost_eff = o.expected_risk_reduction / o.estimated_cost if o.estimated_cost > 0 else o.expected_risk_reduction
            result.append({
                "option_id": o.id,
                "title": o.title,
                "cost": o.estimated_cost,
                "reduction": o.expected_risk_reduction,
                "cost_effectiveness": round(cost_eff, 4)
            })
        return sorted(result, key=lambda x: x["cost_effectiveness"], reverse=True)

    @staticmethod
    def recommend_treatment(scenario_id, org_id):
        compared = RiskTreatmentService.compare_treatments(scenario_id, org_id)
        if not compared:
            return None
        # Select highest cost effectiveness option
        best = compared[0]
        return RiskTreatmentOption.query.get(best["option_id"])

    @staticmethod
    def approve_treatment(option_id, org_id):
        option = RiskTreatmentOption.query.filter_by(id=option_id, organization_id=org_id).first()
        if not option:
            return None

        option.status = 'approved'
        # Update associated scenario residual risk score
        scenario = QuantitativeRiskScenario.query.get(option.scenario_id)
        res_score = RiskTreatmentService.calculate_residual_risk(scenario.id, option.expected_risk_reduction, org_id)
        scenario.residual_risk_score = res_score
        scenario.status = 'mitigating'
        db.session.commit()
        return option

    @staticmethod
    def treatment_summary(org_id):
        options = RiskTreatmentOption.query.filter_by(organization_id=org_id).all()
        return {
            "total_options": len(options),
            "approved_count": sum(1 for o in options if o.status == 'approved'),
            "simulated_count": sum(1 for o in options if o.status == 'simulated')
        }
