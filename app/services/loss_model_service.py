"""
LossModelService - Phase 36 Cyber Risk Quantification.
"""
from app.extensions import db
from app.models.loss_magnitude_estimate import LossMagnitudeEstimate
from app.models.quantitative_risk_scenario import QuantitativeRiskScenario


class LossModelService:
    @staticmethod
    def validate_loss_range(min_loss, most_likely, max_loss):
        if min_loss < 0 or most_likely < 0 or max_loss < 0:
            raise ValueError("Loss estimates cannot be negative")
        if not (min_loss <= most_likely <= max_loss):
            raise ValueError("Invalid distribution order: min_loss <= most_likely_loss <= max_loss is required")
        return True

    @staticmethod
    def create_loss_estimate(scenario_id, loss_type, min_loss, most_likely, max_loss, confidence, org_id):
        scenario = QuantitativeRiskScenario.query.filter_by(id=scenario_id, organization_id=org_id).first()
        if not scenario:
            raise ValueError("Scenario not found or access denied")

        allowed_types = [
            'response_cost', 'recovery_cost', 'downtime_loss', 'productivity_loss',
            'legal_cost_simulation', 'notification_cost_simulation',
            'reputation_impact_simulation', 'third_party_loss_simulation'
        ]
        if loss_type not in allowed_types:
            raise ValueError(f"Invalid loss_type. Must be one of: {allowed_types}")

        LossModelService.validate_loss_range(min_loss, most_likely, max_loss)

        estimate = LossMagnitudeEstimate(
            scenario_id=scenario_id,
            loss_type=loss_type,
            minimum_loss=min_loss,
            most_likely_loss=most_likely,
            maximum_loss=max_loss,
            confidence_score=confidence,
            organization_id=org_id
        )
        db.session.add(estimate)
        db.session.commit()
        return estimate

    @staticmethod
    def calculate_expected_loss(estimate):
        # Default to PERT mean calculation for expected magnitude: (min + 4*mode + max) / 6.0
        return round((estimate.minimum_loss + 4.0 * estimate.most_likely_loss + estimate.maximum_loss) / 6.0, 2)

    @staticmethod
    def calculate_loss_components(scenario_id, org_id):
        scenario = QuantitativeRiskScenario.query.filter_by(id=scenario_id, organization_id=org_id).first()
        if not scenario:
            return {}
        estimates = scenario.loss_estimates.all()
        components = {}
        for e in estimates:
            components[e.loss_type] = {
                "minimum": e.minimum_loss,
                "most_likely": e.most_likely_loss,
                "maximum": e.maximum_loss,
                "expected": LossModelService.calculate_expected_loss(e)
            }
        return components

    @staticmethod
    def compare_loss_profiles(scenario_id1, scenario_id2, org_id):
        s1 = QuantitativeRiskScenario.query.filter_by(id=scenario_id1, organization_id=org_id).first()
        s2 = QuantitativeRiskScenario.query.filter_by(id=scenario_id2, organization_id=org_id).first()
        if not s1 or not s2:
            return None

        e1 = sum(LossModelService.calculate_expected_loss(l) for l in s1.loss_estimates.all())
        e2 = sum(LossModelService.calculate_expected_loss(l) for l in s2.loss_estimates.all())

        return {
            "scenario1": {"id": scenario_id1, "expected_loss": e1},
            "scenario2": {"id": scenario_id2, "expected_loss": e2}
        }

    @staticmethod
    def loss_summary(org_id):
        estimates = LossMagnitudeEstimate.query.filter_by(organization_id=org_id).all()
        if not estimates:
            return {"total_estimates": 0, "avg_expected_loss": 0.0}
        total_exp = sum(LossModelService.calculate_expected_loss(e) for e in estimates)
        return {
            "total_estimates": len(estimates),
            "avg_expected_loss": round(total_exp / len(estimates), 2)
        }
