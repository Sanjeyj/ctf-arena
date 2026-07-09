"""
RiskSimulationService - Phase 36 Cyber Risk Quantification.
"""
import random
import datetime
from app.extensions import db
from app.models.risk_simulation_run import RiskSimulationRun
from app.models.quantitative_risk_scenario import QuantitativeRiskScenario
from app.services.frequency_model_service import FrequencyModelService
from app.services.loss_model_service import LossModelService
from app.services.hook_service import HookService


class RiskSimulationService:
    @staticmethod
    def create_run(scenario_id, simulation_type, iteration_count, random_seed, org_id):
        scenario = QuantitativeRiskScenario.query.filter_by(id=scenario_id, organization_id=org_id).first()
        if not scenario:
            raise ValueError("Scenario not found or access denied")

        # Cap iterations to 100,000 hard limit
        if iteration_count > 100000:
            iteration_count = 100000
        if iteration_count <= 0:
            iteration_count = 100

        run = RiskSimulationRun(
            scenario_id=scenario_id,
            simulation_type=simulation_type,
            iteration_count=iteration_count,
            random_seed=random_seed,
            status='pending',
            organization_id=org_id
        )
        db.session.add(run)
        db.session.commit()
        return run

    @staticmethod
    def simulate_deterministic(run_id, org_id):
        run = RiskSimulationRun.query.filter_by(id=run_id, organization_id=org_id).first()
        if not run:
            return None

        # Hook trigger
        HookService.trigger_hook('before_loss_simulation', run_id=run_id, org_id=org_id)

        scenario = QuantitativeRiskScenario.query.get(run.scenario_id)

        # EAL = frequency * loss magnitude
        freq_est = scenario.frequency_estimates.first()
        loss_ests = scenario.loss_estimates.all()

        freq = freq_est.annual_rate if freq_est else 1.0
        tot_loss = sum(LossModelService.calculate_expected_loss(l) for l in loss_ests) if loss_ests else 5000.0

        eal = freq * tot_loss

        run.status = 'completed'
        run.expected_loss = round(eal, 2)
        run.median_loss = round(eal, 2)
        run.p90_loss = round(eal, 2)
        run.p95_loss = round(eal, 2)
        run.maximum_simulated_loss = round(eal, 2)
        run.completed_at = datetime.datetime.utcnow()
        db.session.commit()

        HookService.trigger_hook('after_loss_simulation', run_id=run_id, org_id=org_id, expected_loss=run.expected_loss)
        return run

    @staticmethod
    def simulate_monte_carlo(run_id, org_id):
        run = RiskSimulationRun.query.filter_by(id=run_id, organization_id=org_id).first()
        if not run:
            return None

        # Hook trigger
        HookService.trigger_hook('before_loss_simulation', run_id=run_id, org_id=org_id)

        scenario = QuantitativeRiskScenario.query.get(run.scenario_id)
        freq_est = scenario.frequency_estimates.first()
        loss_ests = scenario.loss_estimates.all()

        if not freq_est or not loss_ests:
            # Fallback to deterministic if estimates are missing
            return RiskSimulationService.simulate_deterministic(run_id, org_id)

        # Seed pseudo-random generator to ensure deterministic behavior
        random.seed(run.random_seed)

        losses = []
        for _ in range(run.iteration_count):
            # Sample annual frequency
            f_sample = FrequencyModelService.sample_frequency(freq_est)

            # Sample component losses and sum
            l_sum = 0.0
            for l in loss_ests:
                # Triangular loss sample
                l_sum += random.triangular(l.minimum_loss, l.maximum_loss, l.most_likely_loss)

            yearly_loss = f_sample * l_sum
            losses.append(yearly_loss)

        # Sort values to extract percentiles
        losses.sort()

        expected = sum(losses) / len(losses)
        median = RiskSimulationService.calculate_percentiles(losses, 50)
        p90 = RiskSimulationService.calculate_percentiles(losses, 90)
        p95 = RiskSimulationService.calculate_percentiles(losses, 95)
        maximum = losses[-1]

        # Safety assertions check
        assert median <= p90 <= p95 <= maximum

        run.status = 'completed'
        run.expected_loss = round(expected, 2)
        run.median_loss = round(median, 2)
        run.p90_loss = round(p90, 2)
        run.p95_loss = round(p95, 2)
        run.maximum_simulated_loss = round(maximum, 2)
        run.completed_at = datetime.datetime.utcnow()
        db.session.commit()

        HookService.trigger_hook('after_loss_simulation', run_id=run_id, org_id=org_id, expected_loss=run.expected_loss)
        return run

    @staticmethod
    def calculate_percentiles(sorted_list, percentile):
        if not sorted_list:
            return 0.0
        k = (len(sorted_list) - 1) * (percentile / 100.0)
        f = int(k)
        c = f + 1
        if c < len(sorted_list):
            return sorted_list[f] + (sorted_list[c] - sorted_list[f]) * (k - f)
        else:
            return sorted_list[f]

    @staticmethod
    def calculate_expected_annual_loss(scenario_id, org_id):
        # Queries the latest completed run to get the Expected Annual Loss (EAL)
        run = RiskSimulationRun.query.filter_by(
            scenario_id=scenario_id, organization_id=org_id, status='completed'
        ).order_by(RiskSimulationRun.id.desc()).first()
        if run:
            return run.expected_loss

        # Fallback to analytical calculation: Frequency Mean * Loss Expected Mean
        scenario = QuantitativeRiskScenario.query.filter_by(id=scenario_id, organization_id=org_id).first()
        if not scenario:
            return 0.0
        freq_est = scenario.frequency_estimates.first()
        loss_ests = scenario.loss_estimates.all()

        freq = freq_est.annual_rate if freq_est else 1.0
        tot_loss = sum(LossModelService.calculate_expected_loss(l) for l in loss_ests) if loss_ests else 5000.0
        return round(freq * tot_loss, 2)

    @staticmethod
    def complete_run(run_id, expected_loss, median, p90, p95, maximum, org_id):
        run = RiskSimulationRun.query.filter_by(id=run_id, organization_id=org_id).first()
        if not run:
            return None
        run.status = 'completed'
        run.expected_loss = expected_loss
        run.median_loss = median
        run.p90_loss = p90
        run.p95_loss = p95
        run.maximum_simulated_loss = maximum
        run.completed_at = datetime.datetime.utcnow()
        db.session.commit()
        return run

    @staticmethod
    def simulation_summary(run_id, org_id):
        run = RiskSimulationRun.query.filter_by(id=run_id, organization_id=org_id).first()
        if not run:
            return None
        return {
            "run_id": run.id,
            "status": run.status,
            "expected_loss": run.expected_loss,
            "median_loss": run.median_loss,
            "p90_loss": run.p90_loss,
            "p95_loss": run.p95_loss,
            "maximum_simulated_loss": run.maximum_simulated_loss
        }
