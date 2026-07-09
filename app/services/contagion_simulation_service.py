"""
ContagionSimulationService — Phase 39: Systemic Cyber Risk, Collective Resilience
& Federated Governance Fabric.

Simulates contagion propagation through the dependency graph.
All operations are OFFLINE, SIMULATION-ONLY, and TENANT-ISOLATED.
Uses explicit random seeds for deterministic reproducibility.
"""
import datetime
import random
from app.extensions import db
from app.models.contagion_scenario import ContagionScenario
from app.models.contagion_simulation_run import ContagionSimulationRun
from app.models.contagion_event import ContagionEvent
from app.models.systemic_risk_node import SystemicRiskNode
from app.models.systemic_dependency import SystemicDependency

VALID_SCENARIO_TYPES = [
    'shared_service_failure', 'vendor_failure', 'cloud_region_disruption',
    'identity_provider_failure', 'supply_chain_disruption',
    'coordinated_campaign_simulation', 'multi_region_failure',
    'correlated_dependency_failure'
]

MAX_PROPAGATION_DEPTH = 10
MAX_NODES_AFFECTED = 500


class ContagionSimulationService:

    @staticmethod
    def create_scenario(name, description, scenario_type, initial_node_id,
                        severity, initial_impact_score, propagation_depth,
                        correlation_factor, random_seed, org_id):
        if scenario_type not in VALID_SCENARIO_TYPES:
            raise ValueError(f"Invalid scenario_type: {scenario_type}")
        if not (0.0 <= initial_impact_score <= 100.0):
            raise ValueError("initial_impact_score must be 0-100")
        if not (0.0 <= correlation_factor <= 1.0):
            raise ValueError("correlation_factor must be 0-1")

        # Validate node belongs to tenant
        if initial_node_id:
            node = SystemicRiskNode.query.filter_by(id=initial_node_id, organization_id=org_id).first()
            if not node:
                raise ValueError("initial_node_id not found in this tenant")

        depth = min(max(1, propagation_depth), MAX_PROPAGATION_DEPTH)
        scenario = ContagionScenario(
            name=name,
            description=description,
            scenario_type=scenario_type,
            initial_node_id=initial_node_id,
            severity=severity,
            initial_impact_score=initial_impact_score,
            propagation_depth=depth,
            correlation_factor=max(0.0, min(1.0, correlation_factor)),
            random_seed=random_seed,
            status='draft',
            organization_id=org_id
        )
        db.session.add(scenario)
        db.session.commit()
        return scenario

    @staticmethod
    def start_simulation(scenario_id, org_id):
        """Initialize a simulation run for a scenario."""
        scenario = ContagionScenario.query.filter_by(
            id=scenario_id, organization_id=org_id
        ).first()
        if not scenario:
            raise ValueError("ContagionScenario not found")
        if scenario.status == 'archived':
            raise ValueError("Cannot simulate an archived scenario")

        run = ContagionSimulationRun(
            scenario_id=scenario_id,
            status='running',
            random_seed=scenario.random_seed,
            started_at=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(run)
        db.session.commit()

        # Propagate
        ContagionSimulationService.propagate(run.id, scenario, org_id)
        return run

    @staticmethod
    def propagate(run_id, scenario, org_id):
        """BFS-based contagion propagation with cycle protection and depth limiting."""
        rng = random.Random(scenario.random_seed)

        run = ContagionSimulationRun.query.get(run_id)
        if not run:
            return

        initial_node = None
        if scenario.initial_node_id:
            initial_node = SystemicRiskNode.query.filter_by(
                id=scenario.initial_node_id, organization_id=org_id
            ).first()

        visited = set()
        queue = []
        seq = 0
        aggregate_impact = 0.0
        max_depth = 0

        if initial_node:
            # Record initial failure event
            ContagionSimulationService.record_event(
                run_id, None, initial_node.id, seq, 'initial_failure',
                1.0, scenario.initial_impact_score, -10.0,
                f"Initial failure at {initial_node.name}", org_id
            )
            seq += 1
            aggregate_impact += scenario.initial_impact_score
            visited.add(initial_node.id)
            queue.append((initial_node.id, 0))

        # BFS propagation
        while queue and len(visited) < MAX_NODES_AFFECTED:
            current_id, depth = queue.pop(0)
            if depth >= scenario.propagation_depth:
                continue

            # Get outbound dependencies of current node
            deps = SystemicDependency.query.filter_by(
                source_node_id=current_id,
                organization_id=org_id,
                status='active'
            ).all()

            for dep in deps:
                target_id = dep.target_node_id
                if target_id in visited:
                    continue

                # Calculate effective propagation probability with correlation
                base_prob = dep.propagation_probability
                effective_prob = min(1.0, base_prob * (1.0 + scenario.correlation_factor * 0.5))

                roll = rng.random()
                if roll <= effective_prob:
                    # Impact absorbed by resilience
                    target = SystemicRiskNode.query.get(target_id)
                    absorption = (target.resilience_score / 100.0) if target else 0.0
                    impact = scenario.initial_impact_score * (1.0 - absorption) * base_prob
                    impact = max(0.0, min(100.0, impact))

                    # Check if absorbed
                    if absorption >= 0.8:
                        ContagionSimulationService.record_event(
                            run_id, current_id, target_id, seq,
                            'resilience_absorption',
                            effective_prob, impact, absorption * 10.0,
                            f"Absorbed at {target.name if target else target_id}", org_id
                        )
                    else:
                        ContagionSimulationService.record_event(
                            run_id, current_id, target_id, seq,
                            'dependency_propagation',
                            effective_prob, impact, -impact * 0.5,
                            f"Propagated from {current_id} to {target_id}", org_id
                        )
                        visited.add(target_id)
                        aggregate_impact += impact
                        queue.append((target_id, depth + 1))
                        max_depth = max(max_depth, depth + 1)
                else:
                    # Blocked by control or resilience
                    ContagionSimulationService.record_event(
                        run_id, current_id, target_id, seq,
                        'control_block',
                        effective_prob, 0.0, 0.0,
                        f"Blocked propagation to {target_id}", org_id
                    )
                seq += 1

        ContagionSimulationService.complete_simulation(
            run_id, len(visited), max_depth,
            min(100.0, aggregate_impact), org_id
        )

    @staticmethod
    def calculate_propagation_probability(base_prob, correlation_factor, resilience_score):
        """Calculate effective propagation probability clamped to [0, 1]."""
        effective = base_prob * (1.0 + correlation_factor * 0.5)
        absorption = resilience_score / 100.0
        effective *= (1.0 - absorption * 0.5)
        return max(0.0, min(1.0, effective))

    @staticmethod
    def apply_resilience_absorption(impact, resilience_score):
        """Apply resilience absorption to reduce impact. Returns absorbed impact."""
        absorption = resilience_score / 100.0
        absorbed = impact * absorption
        return max(0.0, min(impact, absorbed))

    @staticmethod
    def record_event(run_id, source_id, target_id, seq, event_type,
                     prob, impact_delta, resilience_delta, desc, org_id):
        """Persist a single contagion event."""
        event = ContagionEvent(
            simulation_run_id=run_id,
            source_node_id=source_id,
            target_node_id=target_id,
            event_sequence=seq,
            event_type=event_type,
            propagation_probability=max(0.0, min(1.0, prob)),
            impact_delta=max(0.0, min(100.0, impact_delta)),
            resilience_delta=resilience_delta,
            description=desc,
            event_time=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(event)
        db.session.commit()
        return event

    @staticmethod
    def complete_simulation(run_id, nodes_affected, max_depth,
                            aggregate_impact, org_id):
        """Mark simulation as completed and populate results."""
        run = ContagionSimulationRun.query.filter_by(id=run_id, organization_id=org_id).first()
        if not run:
            return
        run.status = 'completed'
        run.nodes_affected = nodes_affected
        run.maximum_depth_reached = max_depth
        run.aggregate_impact_score = max(0.0, min(100.0, aggregate_impact))
        run.collective_resilience_score = max(0.0, 100.0 - aggregate_impact)
        run.estimated_recovery_hours = round(aggregate_impact * 0.5, 1)
        run.result_summary = (
            f"Simulation complete: {nodes_affected} nodes affected, "
            f"max depth {max_depth}, aggregate impact {aggregate_impact:.1f}"
        )
        run.completed_at = datetime.datetime.utcnow()
        db.session.commit()

    @staticmethod
    def replay_simulation(run_id, org_id):
        """Return ordered events for a completed simulation."""
        run = ContagionSimulationRun.query.filter_by(id=run_id, organization_id=org_id).first()
        if not run:
            raise ValueError("SimulationRun not found")
        events = ContagionEvent.query.filter_by(
            simulation_run_id=run_id, organization_id=org_id
        ).order_by(ContagionEvent.event_sequence).all()
        return events

    @staticmethod
    def simulation_summary(org_id):
        """Aggregate summary across all simulation runs for this tenant."""
        runs = ContagionSimulationRun.query.filter_by(organization_id=org_id).all()
        completed = [r for r in runs if r.status == 'completed']
        avg_impact = (
            sum(r.aggregate_impact_score for r in completed) / len(completed)
            if completed else 0.0
        )
        return {
            'total_runs': len(runs),
            'completed_runs': len(completed),
            'avg_aggregate_impact': round(avg_impact, 2),
            'max_impact_seen': max((r.aggregate_impact_score for r in completed), default=0.0),
        }
