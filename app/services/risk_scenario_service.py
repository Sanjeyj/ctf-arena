"""
RiskScenarioService - Phase 36 Cyber Risk Quantification.
"""
from app.extensions import db
from app.models.quantitative_risk_scenario import QuantitativeRiskScenario
from app.models.business_process import BusinessProcess
from app.services.hook_service import HookService


class RiskScenarioService:
    @staticmethod
    def create_scenario(name, description, scenario_type, asset_ref_type, asset_ref_id, business_process_id, threat_category, org_id):
        allowed_types = [
            'ransomware', 'data_breach', 'cloud_outage', 'supply_chain_failure',
            'insider_risk', 'service_disruption', 'control_failure', 'third_party_failure'
        ]
        if scenario_type not in allowed_types:
            raise ValueError(f"Invalid scenario_type. Must be one of: {allowed_types}")

        # Validate BusinessProcess relationship ownership
        if business_process_id:
            bp = BusinessProcess.query.filter_by(id=business_process_id, organization_id=org_id).first()
            if not bp:
                raise ValueError("Business process not found or access denied")

        scenario = QuantitativeRiskScenario(
            name=name,
            description=description,
            scenario_type=scenario_type,
            asset_reference_type=asset_ref_type,
            asset_reference_id=asset_ref_id,
            business_process_id=business_process_id,
            threat_category=threat_category,
            likelihood_score=50.0,  # default
            impact_score=50.0,
            inherent_risk_score=50.0,
            residual_risk_score=50.0,
            status='draft',
            organization_id=org_id
        )
        db.session.add(scenario)
        db.session.commit()
        return scenario

    @staticmethod
    def activate_scenario(scenario_id, org_id):
        scenario = QuantitativeRiskScenario.query.filter_by(id=scenario_id, organization_id=org_id).first()
        if not scenario:
            return None
        scenario.status = 'active'
        db.session.commit()
        return scenario

    @staticmethod
    def link_asset(scenario_id, asset_ref_type, asset_ref_id, org_id):
        scenario = QuantitativeRiskScenario.query.filter_by(id=scenario_id, organization_id=org_id).first()
        if not scenario:
            return None
        scenario.asset_reference_type = asset_ref_type
        scenario.asset_reference_id = asset_ref_id
        db.session.commit()
        return scenario

    @staticmethod
    def link_business_process(scenario_id, business_process_id, org_id):
        scenario = QuantitativeRiskScenario.query.filter_by(id=scenario_id, organization_id=org_id).first()
        if not scenario:
            return None
        bp = BusinessProcess.query.filter_by(id=business_process_id, organization_id=org_id).first()
        if not bp:
            raise ValueError("Business process not found or access denied")
        scenario.business_process_id = business_process_id
        db.session.commit()
        return scenario

    @staticmethod
    def calculate_likelihood(scenario_id, org_id):
        scenario = QuantitativeRiskScenario.query.filter_by(id=scenario_id, organization_id=org_id).first()
        if not scenario:
            return 0.0
        # Calculate likelihood based on associated frequency estimate
        estimates = scenario.frequency_estimates.all()
        if not estimates:
            return 50.0
        avg_rate = sum(e.annual_rate for e in estimates) / len(estimates)
        # Convert rate to a 0-100 score (e.g. rate * 20 clamped)
        score = min(100.0, max(0.0, avg_rate * 20.0))
        scenario.likelihood_score = round(score, 2)
        db.session.commit()
        return scenario.likelihood_score

    @staticmethod
    def calculate_impact(scenario_id, org_id):
        scenario = QuantitativeRiskScenario.query.filter_by(id=scenario_id, organization_id=org_id).first()
        if not scenario:
            return 0.0
        losses = scenario.loss_estimates.all()
        if not losses:
            return 50.0
        # Average impact score normalized (e.g. most likely loss normalized to 0-100 scale where 500k is 100)
        avg_loss = sum(l.most_likely_loss for l in losses) / len(losses)
        score = min(100.0, max(0.0, (avg_loss / 5000.0)))
        scenario.impact_score = round(score, 2)
        db.session.commit()
        return scenario.impact_score

    @staticmethod
    def calculate_inherent_risk(scenario_id, org_id):
        scenario = QuantitativeRiskScenario.query.filter_by(id=scenario_id, organization_id=org_id).first()
        if not scenario:
            return 0.0

        HookService.trigger_hook('before_risk_quantification', scenario_id=scenario_id, org_id=org_id)

        l_score = RiskScenarioService.calculate_likelihood(scenario_id, org_id)
        i_score = RiskScenarioService.calculate_impact(scenario_id, org_id)

        # Inherent Risk = (likelihood * impact) / 100 (or customized formula clamped to 0-100)
        inherent = min(100.0, max(0.0, (l_score * i_score) / 100.0))
        scenario.inherent_risk_score = round(inherent, 2)
        scenario.status = 'analyzed'
        db.session.commit()

        HookService.trigger_hook('after_risk_quantification', scenario_id=scenario_id, org_id=org_id, inherent_risk_score=scenario.inherent_risk_score)
        return scenario.inherent_risk_score

    @staticmethod
    def scenario_summary(scenario_id, org_id):
        scenario = QuantitativeRiskScenario.query.filter_by(id=scenario_id, organization_id=org_id).first()
        if not scenario:
            return None
        return {
            "scenario_id": scenario.id,
            "name": scenario.name,
            "scenario_type": scenario.scenario_type,
            "likelihood_score": scenario.likelihood_score,
            "impact_score": scenario.impact_score,
            "inherent_risk_score": scenario.inherent_risk_score,
            "residual_risk_score": scenario.residual_risk_score,
            "status": scenario.status
        }
