import random
import datetime
from app.extensions import db
from app.models.attack_event import AttackEvent
from app.models.defense_action import DefenseAction
from app.services.hook_service import HookService

DETECTION_PROBABILITIES = {
    'l1_soc': {'low': 0.6, 'medium': 0.5, 'high': 0.4, 'critical': 0.3},
    'l2_soc': {'low': 0.8, 'medium': 0.75, 'high': 0.7, 'critical': 0.6},
    'l3_soc': {'low': 0.95, 'medium': 0.9, 'high': 0.85, 'critical': 0.8},
}

RESPONSE_MULTIPLIERS = {
    'l1_soc': 1.0,
    'l2_soc': 0.5,
    'l3_soc': 0.2,
}

EFFECTIVENESS_SCORES = {
    'l1_soc': 0.6,
    'l2_soc': 0.8,
    'l3_soc': 0.95,
}

class BlueTeamAIService:
    @staticmethod
    def analyze_event(event: AttackEvent, soc_level: str = 'l1_soc') -> DefenseAction:
        """
        Analyze an AttackEvent to simulate detection, alert generation, and containment recommendation.
        Calculates Blue Team scoring points and triggers defensive hooks.
        """
        # Determine detection probability
        soc_level = soc_level.lower()
        if soc_level not in DETECTION_PROBABILITIES:
            soc_level = 'l1_soc'

        prob_map = DETECTION_PROBABILITIES[soc_level]
        prob = prob_map.get(event.severity, 0.5)

        detected = random.random() <= prob
        if not detected:
            return None

        # Hook: before_defense_action
        HookService.trigger_hook('before_defense_action', event=event, soc_level=soc_level)

        # Update event detection status
        event.detected = True
        event.detected_at = datetime.datetime.utcnow()
        db.session.commit()

        # Compute reaction metrics
        base_delay = random.randint(30, 300) # seconds
        response_time = int(base_delay * RESPONSE_MULTIPLIERS[soc_level])
        effectiveness = EFFECTIVENESS_SCORES[soc_level]

        # Calculate blue scoring points: +15 points for detection, extra bonus for speed
        speed_bonus = max(0, 10 - int(response_time / 30))
        blue_points = 15.0 + speed_bonus

        # Create DefenseAction record
        action = DefenseAction(
            event_id=event.id,
            analyst=f"ai_{soc_level}",
            action="isolate_source_and_mitigate",
            response_time=response_time,
            effectiveness=effectiveness,
            points_awarded=blue_points
        )

        mitigation_rec = "No standard recommendation."
        if event.mitre_technique and event.mitre_technique.mitigation:
            mitigation_rec = event.mitre_technique.mitigation

        action.details = {
            'classification': f'Malicious {event.tactic.replace("_", " ").title()}',
            'recommended_mitigation': mitigation_rec,
            'alert_generated': True
        }
        db.session.add(action)

        # Update Simulation Blue Team Score
        simulation = event.simulation
        if simulation:
            simulation.blue_score += blue_points

        db.session.commit()
        return action
