"""Phase 40 — Platform Readiness Service.

Calculates composite readiness posture index from sub-scores with documented weights:
  Security:     20%
  Reliability:  15%
  Governance:   15%
  Resilience:   20%
  Assurance:    15%
  Operations:   15%
  ------------------
  Total:       100%

All calculations are offline, simulation-only, and tenant-isolated.
"""
import datetime
import logging
from typing import Dict, Optional

from app.extensions import db
from app.models.platform_readiness_metric import PlatformReadinessMetric

logger = logging.getLogger(__name__)


class PlatformReadinessService:
    """Computes and captures platform domain readiness posture metrics."""

    @classmethod
    def calculate_security_readiness(cls, org_id: int) -> float:
        """Calculate dynamic security readiness index in [0, 100]."""
        # Fetch actual capabilities or status to compute score dynamically.
        # Default fallback is 75.0 if no entries exist.
        from app.models.platform_capability import PlatformCapability
        caps = PlatformCapability.query.filter_by(
            organization_id=org_id, category='security', status='active'
        ).all()
        if not caps:
            return 75.0
        scores = [c.maturity_score for c in caps if c.maturity_score is not None]
        return round(sum(scores) / len(scores), 4) if scores else 75.0

    @classmethod
    def calculate_reliability_readiness(cls, org_id: int) -> float:
        """Calculate dynamic reliability readiness index in [0, 100]."""
        from app.models.platform_capability import PlatformCapability
        caps = PlatformCapability.query.filter_by(
            organization_id=org_id, category='observability', status='active'
        ).all()
        if not caps:
            return 80.0
        scores = [c.maturity_score for c in caps if c.maturity_score is not None]
        return round(sum(scores) / len(scores), 4) if scores else 80.0

    @classmethod
    def calculate_governance_readiness(cls, org_id: int) -> float:
        """Calculate dynamic governance readiness index in [0, 100]."""
        from app.models.platform_capability import PlatformCapability
        caps = PlatformCapability.query.filter_by(
            organization_id=org_id, category='governance', status='active'
        ).all()
        if not caps:
            return 82.0
        scores = [c.maturity_score for c in caps if c.maturity_score is not None]
        return round(sum(scores) / len(scores), 4) if scores else 82.0

    @classmethod
    def calculate_resilience_readiness(cls, org_id: int) -> float:
        """Calculate dynamic resilience readiness index in [0, 100]."""
        from app.models.platform_capability import PlatformCapability
        caps = PlatformCapability.query.filter_by(
            organization_id=org_id, category='resilience', status='active'
        ).all()
        if not caps:
            return 78.0
        scores = [c.maturity_score for c in caps if c.maturity_score is not None]
        return round(sum(scores) / len(scores), 4) if scores else 78.0

    @classmethod
    def calculate_assurance_readiness(cls, org_id: int) -> float:
        """Calculate dynamic assurance readiness index in [0, 100]."""
        from app.models.platform_capability import PlatformCapability
        caps = PlatformCapability.query.filter_by(
            organization_id=org_id, category='assurance', status='active'
        ).all()
        if not caps:
            return 85.0
        scores = [c.maturity_score for c in caps if c.maturity_score is not None]
        return round(sum(scores) / len(scores), 4) if scores else 85.0

    @classmethod
    def calculate_operations_readiness(cls, org_id: int) -> float:
        """Calculate dynamic operations readiness index in [0, 100]."""
        from app.models.platform_capability import PlatformCapability
        caps = PlatformCapability.query.filter_by(
            organization_id=org_id, category='operations', status='active'
        ).all()
        if not caps:
            return 70.0
        scores = [c.maturity_score for c in caps if c.maturity_score is not None]
        return round(sum(scores) / len(scores), 4) if scores else 70.0

    @classmethod
    def calculate_overall_readiness(
        cls,
        security: float,
        reliability: float,
        governance: float,
        resilience: float,
        assurance: float,
        operations: float,
    ) -> float:
        """Calculate weighted composite readiness score.

        Asserts that the weights defined in PlatformReadinessMetric sum exactly to 1.0.
        """
        w_sec = PlatformReadinessMetric.WEIGHT_SECURITY
        w_rel = PlatformReadinessMetric.WEIGHT_RELIABILITY
        w_gov = PlatformReadinessMetric.WEIGHT_GOVERNANCE
        w_res = PlatformReadinessMetric.WEIGHT_RESILIENCE
        w_ass = PlatformReadinessMetric.WEIGHT_ASSURANCE
        w_ops = PlatformReadinessMetric.WEIGHT_OPERATIONS

        total_weight = w_sec + w_rel + w_gov + w_res + w_ass + w_ops
        assert abs(total_weight - 1.0) < 1e-9, f"Readiness weights total {total_weight} instead of 1.0"

        overall = (
            security * w_sec +
            reliability * w_rel +
            governance * w_gov +
            resilience * w_res +
            assurance * w_ass +
            operations * w_ops
        )
        return round(overall, 4)

    @classmethod
    def save_metric(
        cls,
        org_id: int,
        metric_type: str = 'on_demand',
        notes: str = '',
    ) -> Dict:
        """Evaluate, calculate and save a new readiness metric snapshot."""
        if metric_type not in PlatformReadinessMetric.METRIC_TYPES:
            raise ValueError(f"Invalid metric_type: {metric_type}")

        sec = cls.calculate_security_readiness(org_id)
        rel = cls.calculate_reliability_readiness(org_id)
        gov = cls.calculate_governance_readiness(org_id)
        res = cls.calculate_resilience_readiness(org_id)
        ass = cls.calculate_assurance_readiness(org_id)
        ops = cls.calculate_operations_readiness(org_id)

        overall = cls.calculate_overall_readiness(sec, rel, gov, res, ass, ops)

        metric = PlatformReadinessMetric(
            metric_type=metric_type,
            security_score=sec,
            reliability_score=rel,
            governance_score=gov,
            resilience_score=res,
            assurance_score=ass,
            operations_score=ops,
            overall_readiness_score=overall,
            measured_at=datetime.datetime.utcnow(),
            notes=notes,
            organization_id=org_id,
        )
        db.session.add(metric)
        db.session.commit()
        logger.info(f"[Readiness] Saved {metric_type} metric (overall={overall}) for org {org_id}")
        return metric.to_dict()

    @classmethod
    def readiness_summary(cls, org_id: int) -> Dict:
        """Get summary of readiness history."""
        metrics = PlatformReadinessMetric.query.filter_by(organization_id=org_id).order_by(
            PlatformReadinessMetric.measured_at.desc()
        ).all()
        return {
            'total_measurements': len(metrics),
            'latest': metrics[0].to_dict() if metrics else None,
        }
