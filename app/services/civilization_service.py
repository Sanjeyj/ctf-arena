"""
CivilizationService - Phase 28 Cyber Civilization Platform.
Evaluates civilization composite metrics, benchmarks scores, and computes maturity index.
"""
from app.extensions import db
from app.models.civilization_metric import CivilizationMetric
from app.models.cyber_nation import CyberNation


class CivilizationService:
    @staticmethod
    def evaluate(org_id: int) -> CivilizationMetric:
        """Evaluate baseline metrics and return a CivilizationMetric instance."""
        # Find existing or create default
        metric = CivilizationMetric.query.filter_by(organization_id=org_id).first()
        if not metric:
            metric = CivilizationMetric(
                maturity=0.6,
                resilience=0.65,
                intelligence=0.7,
                innovation=0.55,
                organization_id=org_id
            )
            db.session.add(metric)
            db.session.commit()
        return metric

    @staticmethod
    def benchmark(org_id: int) -> dict:
        """Benchmark organization maturity score against industry averages."""
        metric = CivilizationService.evaluate(org_id)
        # Average baseline is 0.55
        industry_avg = 0.55
        diff = round(metric.maturity - industry_avg, 3)
        status = "above_average" if diff >= 0 else "below_average"
        return {
            'organization_id': org_id,
            'maturity': metric.maturity,
            'industry_average': industry_avg,
            'variance': diff,
            'status': status
        }

    @staticmethod
    def calculate(org_id: int) -> float:
        """Compute composite index across all metric categories."""
        metric = CivilizationService.evaluate(org_id)
        composite = (metric.maturity + metric.resilience + metric.intelligence + metric.innovation) / 4.0
        return round(composite, 3)
