"""
FrequencyModelService - Phase 36 Cyber Risk Quantification.
"""
import random
from app.extensions import db
from app.models.risk_frequency_estimate import RiskFrequencyEstimate
from app.models.quantitative_risk_scenario import QuantitativeRiskScenario


class FrequencyModelService:
    @staticmethod
    def validate_distribution(min_freq, most_likely, max_freq):
        if min_freq < 0 or most_likely < 0 or max_freq < 0:
            raise ValueError("Frequency estimates cannot be negative")
        if not (min_freq <= most_likely <= max_freq):
            raise ValueError("Invalid distribution order: min <= most_likely <= max is required")
        return True

    @staticmethod
    def create_estimate(scenario_id, frequency_type, min_freq, most_likely, max_freq, confidence, source_basis, org_id):
        scenario = QuantitativeRiskScenario.query.filter_by(id=scenario_id, organization_id=org_id).first()
        if not scenario:
            raise ValueError("Scenario not found or access denied")

        allowed_types = ['triangular', 'pert', 'fixed', 'historical_simulation']
        if frequency_type not in allowed_types:
            raise ValueError(f"Invalid frequency_type. Must be one of: {allowed_types}")

        FrequencyModelService.validate_distribution(min_freq, most_likely, max_freq)

        estimate = RiskFrequencyEstimate(
            scenario_id=scenario_id,
            frequency_type=frequency_type,
            minimum_frequency=min_freq,
            most_likely_frequency=most_likely,
            maximum_frequency=max_freq,
            annual_rate=most_likely,  # Default, updated below
            confidence_score=confidence,
            source_basis=source_basis,
            organization_id=org_id
        )
        db.session.add(estimate)
        db.session.commit()

        # Update annual rate using standard distributions
        estimate.annual_rate = FrequencyModelService.calculate_annual_rate(estimate)
        db.session.commit()
        return estimate

    @staticmethod
    def calculate_annual_rate(estimate):
        a = estimate.minimum_frequency
        b = estimate.most_likely_frequency
        c = estimate.maximum_frequency

        if estimate.frequency_type == 'pert':
            # Beta-PERT mean = (a + 4b + c) / 6.0
            return round((a + 4.0 * b + c) / 6.0, 4)
        elif estimate.frequency_type == 'triangular':
            # Triangular mean = (a + b + c) / 3.0
            return round((a + b + c) / 3.0, 4)
        else:
            return round(b, 4)

    @staticmethod
    def sample_frequency(estimate, seed=None):
        if seed is not None:
            random.seed(seed)

        a = estimate.minimum_frequency
        b = estimate.most_likely_frequency
        c = estimate.maximum_frequency

        if estimate.frequency_type == 'fixed':
            return b

        if estimate.frequency_type == 'triangular':
            return random.triangular(a, c, b)

        if estimate.frequency_type == 'pert':
            # Simplified PERT sampler using Beta distribution approximation
            # PERT mean = (a + 4b + c)/6, alpha = 1 + 4*(b-a)/(c-a), beta = 1 + 4*(c-b)/(c-a)
            if c == a:
                return a
            alpha = 1.0 + 4.0 * (b - a) / (c - a)
            beta_val = 1.0 + 4.0 * (c - b) / (c - a)
            sample_std = random.betavariate(alpha, beta_val)
            return a + sample_std * (c - a)

        # fallback
        return b

    @staticmethod
    def compare_estimates(estimate_ids, org_id):
        estimates = RiskFrequencyEstimate.query.filter(
            RiskFrequencyEstimate.id.in_(estimate_ids),
            RiskFrequencyEstimate.organization_id == org_id
        ).all()
        return [
            {
                "id": e.id,
                "scenario_id": e.scenario_id,
                "frequency_type": e.frequency_type,
                "annual_rate": e.annual_rate
            } for e in estimates
        ]

    @staticmethod
    def frequency_summary(org_id):
        estimates = RiskFrequencyEstimate.query.filter_by(organization_id=org_id).all()
        if not estimates:
            return {"total_estimates": 0, "avg_annual_rate": 0.0}
        avg_rate = sum(e.annual_rate for e in estimates) / len(estimates)
        return {
            "total_estimates": len(estimates),
            "avg_annual_rate": round(avg_rate, 4)
        }
