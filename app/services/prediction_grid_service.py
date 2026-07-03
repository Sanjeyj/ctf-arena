"""
PredictionGridService - Phase 28 Cyber Civilization Platform.
Simulates scenarios, predictions, and scoring in the global threat prediction center.
"""
from app.extensions import db
from app.models.prediction_scenario import PredictionScenario


class PredictionGridService:
    @staticmethod
    def simulate(scenario_id: int) -> dict:
        """Simulate a prediction scenario run, updating probability and confidence parameters."""
        scenario = db.session.get(PredictionScenario, scenario_id)
        if not scenario:
            return {'error': f'Scenario {scenario_id} not found'}
        
        # Simulation drift calculation
        scenario.probability = round(max(0.0, min(1.0, scenario.probability * 1.05)), 3)
        scenario.confidence = round(max(0.0, min(1.0, scenario.confidence * 0.98)), 3)
        db.session.commit()
        
        return {
            'scenario_id': scenario_id,
            'name': scenario.scenario_name,
            'simulation_run': 'complete',
            'updated_probability': scenario.probability,
            'updated_confidence': scenario.confidence
        }

    @staticmethod
    def predict(threat_class: str, org_id: int) -> PredictionScenario:
        """Generate a new prediction scenario based on historical threat templates."""
        scenario = PredictionScenario(
            scenario_name=f"Threat-Predict-{threat_class.upper()}",
            impact_score=0.75,
            probability=0.45,
            confidence=0.8,
            organization_id=org_id
        )
        db.session.add(scenario)
        db.session.commit()
        return scenario

    @staticmethod
    def score(scenario_id: int) -> float:
        """Compute the weighted risk severity score for the scenario."""
        scenario = db.session.get(PredictionScenario, scenario_id)
        if not scenario:
            return 0.0
        weighted_score = (scenario.impact_score * 0.5) + (scenario.probability * 0.5)
        return round(weighted_score, 3)
