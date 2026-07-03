"""
ForecastService - Phase 27 Global Security Intelligence Network.
Generates probabilistic threat forecasts from prediction models.
Simulation-only: no external ML runtimes.
"""
import random
from app.extensions import db
from app.models.forecast_event import ForecastEvent
from app.models.prediction_model import PredictionModel


class ForecastService:
    THREAT_TEMPLATES = {
        'ransomware':   'High probability of ransomware campaign targeting {sector} sector within 30 days.',
        'phishing':     'Spear-phishing wave expected from APT group active in {region} region.',
        'ddos':         'Distributed denial-of-service surge predicted against critical infrastructure.',
        'supply_chain': 'Supply chain compromise vector detected in third-party software updates.',
        'insider':      'Elevated insider threat probability based on behavioral anomaly signals.',
    }

    @staticmethod
    def predict(threat_type: str, org_id: int = None) -> ForecastEvent:
        """Generate a probabilistic forecast event for a given threat type."""
        template = ForecastService.THREAT_TEMPLATES.get(
            threat_type,
            f'Threat activity of type {threat_type!r} forecast based on historical patterns.'
        )
        prediction_text = template.format(sector='technology', region='EMEA')

        model = PredictionModel.query.first()
        base_confidence = model.confidence if model else 0.75
        probability = round(min(1.0, base_confidence * random.uniform(0.8, 1.1)), 3)

        impact_levels = ['low', 'medium', 'high', 'critical']
        impact = impact_levels[min(3, int(probability * 4))]

        event = ForecastEvent(
            prediction=prediction_text,
            probability=probability,
            impact=impact,
            confidence=round(base_confidence, 3),
            organization_id=org_id,
        )
        db.session.add(event)
        db.session.commit()
        return event

    @staticmethod
    def score(forecast_id: int) -> dict:
        """Calculate a composite confidence score for a forecast event."""
        event = db.session.get(ForecastEvent, forecast_id)
        if not event:
            return {'error': f'ForecastEvent {forecast_id} not found'}
        composite = round((event.probability + event.confidence) / 2, 3)
        return {
            'forecast_id': forecast_id,
            'probability': event.probability,
            'confidence': event.confidence,
            'composite_score': composite,
            'risk_level': event.impact,
        }

    @staticmethod
    def explain(forecast_id: int) -> str:
        """Return a plain-language explanation of a forecast event."""
        event = db.session.get(ForecastEvent, forecast_id)
        if not event:
            return f'Forecast {forecast_id} not found.'
        return (
            f"This forecast predicts: {event.prediction} "
            f"Estimated probability: {event.probability:.0%}. "
            f"Confidence level: {event.confidence:.0%}. "
            f"Expected impact: {event.impact.upper()}."
        )
