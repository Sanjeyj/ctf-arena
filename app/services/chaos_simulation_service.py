"""
ChaosSimulationService - Phase 33 Cyber Platform Observability, Reliability & Operations Fabric.
Simulates platform resiliency under load, latency injections, and dependency breakdowns.
Operates strictly as database-level simulation logic.
"""
from app.extensions import db
from app.models.chaos_experiment import ChaosExperiment
from app.models.platform_service import PlatformService
from app.models.operations_timeline_event import OperationsTimelineEvent
from app.services.health_service import HealthService
from app.services.hook_service import HookService
import datetime
import json


class ChaosSimulationService:
    @staticmethod
    def create_experiment(name: str, experiment_type: str, target_service: str, hypothesis: str, org_id: int, simulation_parameters_json: dict = None) -> ChaosExperiment:
        """Create a chaos experiment config configuration, invoking hooks."""
        # Mutation check via hook
        hook_results = HookService.trigger_hook(
            'before_chaos_simulation',
            name=name,
            experiment_type=experiment_type,
            target_service=target_service,
            hypothesis=hypothesis,
            simulation_parameters_json=simulation_parameters_json,
            org_id=org_id
        )
        for res in hook_results:
            if isinstance(res, dict):
                if 'name' in res:
                    name = res['name']
                if 'experiment_type' in res:
                    experiment_type = res['experiment_type']
                if 'target_service' in res:
                    target_service = res['target_service']

        exp = ChaosExperiment(
            name=name,
            experiment_type=experiment_type,
            target_service=target_service,
            hypothesis=hypothesis,
            simulation_parameters_json=json.dumps(simulation_parameters_json) if simulation_parameters_json else None,
            status='scheduled',
            baseline_score=100.0,
            result_score=100.0,
            organization_id=org_id
        )
        db.session.add(exp)
        db.session.commit()

        HookService.trigger_hook('after_chaos_simulation', experiment=exp)

        return exp

    @staticmethod
    def simulate_latency(experiment_id: int, target_service: str, org_id: int) -> float:
        """Simulate high latency injection on the service health status."""
        exp = db.session.get(ChaosExperiment, experiment_id)
        if not exp or exp.organization_id != org_id:
            return 0.0

        exp.status = 'running'
        # Log event
        evt = OperationsTimelineEvent(
            event_type='chaos_start',
            severity='warning',
            description=f"Chaos experiment '{exp.name}' started: injecting latency to {target_service}",
            source_service='ChaosSimulationService',
            score_delta=-5.0,
            event_time=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(evt)

        # Get service details
        srv = PlatformService.query.filter_by(service_name=target_service, organization_id=org_id).first()
        baseline = srv.health_score * 100.0 if srv else 100.0
        exp.baseline_score = baseline

        # Simulate degraded latency: add 500ms
        sim_latency = 600.0
        sim_availability = 0.98
        sim_error_rate = 0.05
        sim_saturation = 0.40

        result_health = HealthService.calculate_health(
            availability=sim_availability,
            latency_ms=sim_latency,
            error_rate=sim_error_rate,
            saturation=sim_saturation
        )

        # Create degraded health snapshot to simulate metric shift
        if srv:
            HealthService.record_snapshot(
                platform_service_id=srv.id,
                availability=sim_availability,
                latency_ms=sim_latency,
                error_rate=sim_error_rate,
                saturation=sim_saturation,
                org_id=org_id
            )

        exp.result_score = result_health
        exp.result_summary = f"Simulated latency injection succeeded. Health score shifted from {baseline} to {result_health} due to 600ms response delay."
        exp.status = 'completed'
        db.session.commit()

        return result_health

    @staticmethod
    def simulate_service_degradation(experiment_id: int, target_service: str, org_id: int) -> float:
        """Simulate overall service resource degradation (high saturation/errors)."""
        exp = db.session.get(ChaosExperiment, experiment_id)
        if not exp or exp.organization_id != org_id:
            return 0.0

        exp.status = 'running'
        # Log event
        evt = OperationsTimelineEvent(
            event_type='chaos_start',
            severity='warning',
            description=f"Chaos experiment '{exp.name}' started: degrading resources of {target_service}",
            source_service='ChaosSimulationService',
            score_delta=-10.0,
            event_time=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(evt)

        srv = PlatformService.query.filter_by(service_name=target_service, organization_id=org_id).first()
        baseline = srv.health_score * 100.0 if srv else 100.0
        exp.baseline_score = baseline

        # Simulate degraded resources: high saturation + high error rate
        sim_latency = 120.0
        sim_availability = 0.90
        sim_error_rate = 0.25
        sim_saturation = 0.95

        result_health = HealthService.calculate_health(
            availability=sim_availability,
            latency_ms=sim_latency,
            error_rate=sim_error_rate,
            saturation=sim_saturation
        )

        if srv:
            HealthService.record_snapshot(
                platform_service_id=srv.id,
                availability=sim_availability,
                latency_ms=sim_latency,
                error_rate=sim_error_rate,
                saturation=sim_saturation,
                org_id=org_id
            )

        exp.result_score = result_health
        exp.result_summary = f"Simulated resource exhaustion succeeded. Health score degraded from {baseline} to {result_health} (saturation={sim_saturation * 100}%, error_rate={sim_error_rate * 100}%)."
        exp.status = 'completed'
        db.session.commit()

        return result_health

    @staticmethod
    def simulate_dependency_failure(experiment_id: int, target_service: str, org_id: int) -> float:
        """Simulate dependency breakdown, causing cascading failures."""
        exp = db.session.get(ChaosExperiment, experiment_id)
        if not exp or exp.organization_id != org_id:
            return 0.0

        exp.status = 'running'
        evt = OperationsTimelineEvent(
            event_type='chaos_start',
            severity='error',
            description=f"Chaos experiment '{exp.name}' started: breaking downstream dependencies of {target_service}",
            source_service='ChaosSimulationService',
            score_delta=-15.0,
            event_time=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(evt)

        srv = PlatformService.query.filter_by(service_name=target_service, organization_id=org_id).first()
        baseline = srv.health_score * 100.0 if srv else 100.0
        exp.baseline_score = baseline

        # Simulate dependency breakdown: low availability
        sim_latency = 450.0
        sim_availability = 0.10
        sim_error_rate = 0.80
        sim_saturation = 0.90

        result_health = HealthService.calculate_health(
            availability=sim_availability,
            latency_ms=sim_latency,
            error_rate=sim_error_rate,
            saturation=sim_saturation
        )

        if srv:
            HealthService.record_snapshot(
                platform_service_id=srv.id,
                availability=sim_availability,
                latency_ms=sim_latency,
                error_rate=sim_error_rate,
                saturation=sim_saturation,
                org_id=org_id
            )

        exp.result_score = result_health
        exp.result_summary = f"Simulated cascading dependency breakdown. Health score crashed from {baseline} to {result_health} due to downstream link timeout failures."
        exp.status = 'completed'
        db.session.commit()

        return result_health

    @staticmethod
    def evaluate_hypothesis(experiment_id: int, org_id: int) -> bool:
        """Verify if the results support the resilience hypothesis."""
        exp = db.session.get(ChaosExperiment, experiment_id)
        if not exp or exp.organization_id != org_id:
            return False

        # Hypothesis passes if result score is lower than baseline (which indicates the degradation took place)
        # or matches specific simulation criteria.
        return exp.result_score < exp.baseline_score

    @staticmethod
    def complete_experiment(experiment_id: int, result_score: float, result_summary: str, org_id: int) -> ChaosExperiment:
        """Commit chaos finalization results."""
        exp = db.session.get(ChaosExperiment, experiment_id)
        if not exp or exp.organization_id != org_id:
            return None

        exp.status = 'completed'
        exp.result_score = result_score
        exp.result_summary = result_summary
        db.session.commit()
        return exp

    @staticmethod
    def experiment_summary(org_id: int) -> dict:
        """Summarize chaos experiments history."""
        exps = ChaosExperiment.query.filter_by(organization_id=org_id).all()
        if not exps:
            return {
                'total_experiments': 0,
                'completed_count': 0,
                'aborted_count': 0,
                'avg_degradation_delta': 0.0
            }

        completed = sum(1 for e in exps if e.status == 'completed')
        aborted = sum(1 for e in exps if e.status == 'aborted')

        deltas = []
        for e in exps:
            if e.status == 'completed':
                deltas.append(e.baseline_score - e.result_score)

        avg_delta = sum(deltas) / len(deltas) if deltas else 0.0

        return {
            'total_experiments': len(exps),
            'completed_count': completed,
            'aborted_count': aborted,
            'avg_degradation_delta': round(avg_delta, 2)
        }
