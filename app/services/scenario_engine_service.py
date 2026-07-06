"""
ScenarioEngineService - Phase 30 Unified Cyber Defense Universe.
Defines abstract wargaming/simulation runs, scoring scenarios risk impacts, and recommending controls.
"""
from app.extensions import db
from app.models.universe_scenario import UniverseScenario
from app.models.universe_simulation import UniverseSimulation
from app.models.universe_event import UniverseEvent
from app.models.defense_universe import DefenseUniverse
from app.services.hook_service import HookService
import datetime
import json


class ScenarioEngineService:
    @staticmethod
    def create_scenario(universe_id: int, scenario_name: str, scenario_type: str, org_id: int, severity: str = 'medium', configuration: dict = None) -> UniverseScenario:
        """Create a threat simulation scenario."""
        config_str = json.dumps(configuration) if configuration else None
        scen = UniverseScenario(
            universe_id=universe_id,
            scenario_name=scenario_name,
            scenario_type=scenario_type,
            severity=severity,
            probability=0.5,
            impact_score=0.5,
            status='active',
            configuration_json=config_str,
            organization_id=org_id
        )
        db.session.add(scen)
        db.session.commit()
        return scen

    @staticmethod
    def validate_scenario(scenario_id: int, org_id: int) -> bool:
        """Verify scenario fields are populated and syntactically valid."""
        scen = db.session.get(UniverseScenario, scenario_id)
        if not scen or scen.organization_id != org_id:
            return False
        return bool(scen.scenario_name and scen.scenario_type)

    @staticmethod
    def simulate(scenario_id: int, org_id: int) -> UniverseSimulation:
        """Run safe wargame threat simulation, spawning simulations & events, triggering hooks."""
        scen = db.session.get(UniverseScenario, scenario_id)
        if not scen or scen.organization_id != org_id:
            return None

        uni = db.session.get(DefenseUniverse, scen.universe_id)
        if not uni:
            return None

        # Hook trigger: before simulation
        HookService.trigger_hook("before_universe_simulation", scenario=scen, universe=uni)

        sim = UniverseSimulation(
            universe_id=uni.id,
            scenario_id=scen.id,
            status='running',
            started_at=datetime.datetime.utcnow(),
            initial_score=uni.readiness_score,
            organization_id=org_id
        )
        db.session.add(sim)
        db.session.commit()

        # Simulate events based on scenario type
        score_drop = 0.15 if scen.severity == 'critical' else 0.10 if scen.severity == 'high' else 0.05
        
        event = UniverseEvent(
            simulation_id=sim.id,
            event_type='threat_triggered',
            domain=scen.scenario_type,
            severity=scen.severity,
            description=f"Simulation triggered scenario: {scen.scenario_name}.",
            score_delta=-score_drop,
            event_time=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(event)

        # Update dynamic readiness and risk scores in simulation record
        uni.readiness_score = max(0.0, round(uni.readiness_score - score_drop, 3))
        uni.risk_score = min(1.0, round(uni.risk_score + score_drop, 3))
        
        sim.status = 'complete'
        sim.completed_at = datetime.datetime.utcnow()
        sim.final_score = uni.readiness_score
        sim.result_summary = f"Threat successfully executed. Impact score was {score_drop}."
        db.session.commit()

        # Hook trigger: after simulation
        HookService.trigger_hook("after_universe_simulation", simulation=sim, outcome="success")

        return sim

    @staticmethod
    def calculate_impact(scenario_id: int, org_id: int) -> float:
        """Estimate what-if impact score across logical metrics."""
        scen = db.session.get(UniverseScenario, scenario_id)
        if not scen or scen.organization_id != org_id:
            return 0.0
        base = 0.5
        if scen.severity == 'critical':
            base += 0.4
        elif scen.severity == 'high':
            base += 0.25
        elif scen.severity == 'medium':
            base += 0.1
        return round(base * scen.probability, 3)

    @staticmethod
    def recommend_controls(scenario_id: int, org_id: int) -> list:
        """Recommend platform security controls to mitigate scenario threat."""
        scen = db.session.get(UniverseScenario, scenario_id)
        if not scen or scen.organization_id != org_id:
            return []
        recommendations = {
            'ransomware_outage': ["Deploy automated disaster recovery playbook", "Restrict local credential storage"],
            'cloud_region_failure': ["Set up multi-region fallback routes", "Synchronize mesh route tables"],
            'supply_chain_disruption': ["Run third-party vendor assess cycles", "Evaluate vendor compliance scores"],
            'credential_compromise': ["Enforce JWT expiry limits", "Configure MFA validation controls"],
        }
        return recommendations.get(scen.scenario_type, ["Standard defense-in-depth posture monitoring"])
