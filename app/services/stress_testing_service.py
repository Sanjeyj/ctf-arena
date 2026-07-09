"""
StressTestingService - Phase 37 Cyber Resilience Stress Testing.
"""
import json
import random
import datetime
from app.extensions import db
from app.models.stress_test_scenario import StressTestScenario
from app.models.stress_test_run import StressTestRun
from app.services.risk_portfolio_service import RiskPortfolioService
from app.services.hook_service import HookService


class StressTestingService:
    @staticmethod
    def create_scenario(name, description, scenario_category, severity, duration_hours, affected_domains, probability, impact_multiplier, org_id):
        allowed_categories = [
            'ransomware_disruption', 'cloud_region_failure', 'identity_compromise',
            'supply_chain_disruption', 'data_breach', 'critical_service_outage',
            'multi_domain_failure', 'control_degradation'
        ]
        if scenario_category not in allowed_categories:
            raise ValueError(f"Invalid scenario category. Must be one of: {allowed_categories}")

        if not (0.0 <= probability <= 1.0):
            raise ValueError("probability must be between 0.0 and 1.0")
        if duration_hours < 0:
            raise ValueError("duration_hours cannot be negative")

        scenario = StressTestScenario(
            name=name,
            description=description,
            scenario_category=scenario_category,
            severity=severity,
            duration_hours=duration_hours,
            affected_domains_json=json.dumps(affected_domains or []),
            probability=probability,
            impact_multiplier=impact_multiplier,
            status='draft',
            organization_id=org_id
        )
        db.session.add(scenario)
        db.session.commit()
        return scenario

    @staticmethod
    def validate_scenario(scenario):
        if not scenario.name:
            return False
        if not (0.0 <= scenario.probability <= 1.0):
            return False
        if scenario.duration_hours < 0:
            return False
        return True

    @staticmethod
    def create_run(scenario_id, iteration_count, random_seed, org_id):
        scenario = StressTestScenario.query.filter_by(id=scenario_id, organization_id=org_id).first()
        if not scenario:
            raise ValueError("Stress scenario not found or access denied")

        run = StressTestRun(
            scenario_id=scenario_id,
            status='pending',
            random_seed=random_seed,
            iteration_count=iteration_count,
            organization_id=org_id
        )
        db.session.add(run)
        db.session.commit()
        return run

    @staticmethod
    def simulate_stress(run_id, org_id):
        run = StressTestRun.query.filter_by(id=run_id, organization_id=org_id).first()
        if not run:
            return None

        HookService.trigger_hook('before_stress_test', scenario_id=run.scenario_id, org_id=org_id)

        scenario = StressTestScenario.query.get(run.scenario_id)

        # Baseline calculations
        base_loss = RiskPortfolioService.calculate_expected_annual_loss(org_id)
        # Fallback if no EAL exists
        if base_loss == 0:
            base_loss = 25000.0

        run.baseline_loss = base_loss
        run.baseline_resilience = 85.0  # default baseline

        random.seed(run.random_seed)

        # Iteration simulations
        losses = []
        resiliences = []
        sev_map = {'low': 5.0, 'medium': 15.0, 'high': 30.0, 'critical': 50.0}
        base_degradation = sev_map.get(scenario.severity, 15.0)

        for _ in range(run.iteration_count):
            fluct = random.uniform(0.8, 1.2)
            losses.append(base_loss * scenario.impact_multiplier * fluct)
            resiliences.append(max(0.0, min(100.0, run.baseline_resilience - (base_degradation * fluct))))

        # Compute averages
        run.stressed_loss = round(sum(losses) / len(losses), 2)
        run.stressed_resilience = round(sum(resiliences) / len(resiliences), 2)
        run.recovery_time_hours = round(scenario.duration_hours * scenario.impact_multiplier, 2)

        # Risk appetite check
        appetite = RiskPortfolioService.check_risk_appetite(org_id)
        # Check if stressed loss exceeds maximum annualized loss limit
        limit = appetite.get('maximum_annualized_loss_limit', 1000000.0)
        run.risk_appetite_breached = run.stressed_loss > limit

        run.status = 'completed'
        run.completed_at = datetime.datetime.utcnow()
        run.result_summary = (
            f"Stress run completed successfully. Stressed expected loss increased to {run.stressed_loss} USD "
            f"(baseline: {run.baseline_loss}). Stressed resilience index degraded to {run.stressed_resilience}%."
        )
        db.session.commit()

        HookService.trigger_hook('after_stress_test', run_id=run.id, org_id=org_id)
        return run

    @staticmethod
    def calculate_stressed_loss(run_id, org_id):
        run = StressTestRun.query.filter_by(id=run_id, organization_id=org_id).first()
        return run.stressed_loss if run else 0.0

    @staticmethod
    def calculate_resilience_degradation(run_id, org_id):
        run = StressTestRun.query.filter_by(id=run_id, organization_id=org_id).first()
        return run.baseline_resilience - run.stressed_resilience if run else 0.0

    @staticmethod
    def calculate_recovery_time(run_id, org_id):
        run = StressTestRun.query.filter_by(id=run_id, organization_id=org_id).first()
        return run.recovery_time_hours if run else 0.0

    @staticmethod
    def check_appetite_breach(run_id, org_id):
        run = StressTestRun.query.filter_by(id=run_id, organization_id=org_id).first()
        return run.risk_appetite_breached if run else False

    @staticmethod
    def stress_summary(org_id):
        runs = StressTestRun.query.filter_by(organization_id=org_id, status='completed').all()
        if not runs:
            return {"total_runs": 0, "avg_stressed_loss": 0.0, "breach_count": 0}
        avg_loss = sum(r.stressed_loss for r in runs) / len(runs)
        breaches = sum(1 for r in runs if r.risk_appetite_breached)
        return {
            "total_runs": len(runs),
            "avg_stressed_loss": round(avg_loss, 2),
            "breach_count": breaches
        }
