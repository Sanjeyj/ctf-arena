"""
PostureFusionService - Phase 30 Unified Cyber Defense Universe.
Aggregates performance scores across all functional domains and tracks metrics.
"""
from app.extensions import db
from app.models.defense_universe import DefenseUniverse
from app.models.defense_domain import DefenseDomain
from app.models.universe_metric import UniverseMetric
from app.services.hook_service import HookService
import datetime


class PostureFusionService:
    @staticmethod
    def aggregate_domains(universe_id: int, org_id: int) -> dict:
        """Aggregate health and readiness statistics across universe domains."""
        domains = DefenseDomain.query.filter_by(universe_id=universe_id, organization_id=org_id).all()
        if not domains:
            return {'total_domains': 0, 'avg_health': 0.0, 'avg_readiness': 0.0}
        avg_health = sum(d.health_score for d in domains) / len(domains)
        avg_readiness = sum(d.readiness_score for d in domains) / len(domains)
        return {
            'total_domains': len(domains),
            'avg_health': round(avg_health, 3),
            'avg_readiness': round(avg_readiness, 3),
            'domain_types': list(set(d.domain_type for d in domains))
        }

    @staticmethod
    def calculate_global_score(universe_id: int, org_id: int) -> float:
        """Compute the global composite performance score, triggering posture hooks."""
        uni = db.session.get(DefenseUniverse, universe_id)
        if not uni or uni.organization_id != org_id:
            return 0.0

        # Trigger hook: before posture fusion
        HookService.trigger_hook("before_posture_fusion", universe=uni)

        agg = PostureFusionService.aggregate_domains(universe_id, org_id)
        if agg['total_domains'] == 0:
            global_score = uni.readiness_score
        else:
            global_score = round((agg['avg_health'] + agg['avg_readiness'] + uni.resilience_score) / 3.0, 3)

        uni.readiness_score = global_score
        db.session.commit()

        # Log metric history
        metric = UniverseMetric(
            universe_id=universe_id,
            metric_type='readiness',
            metric_value=global_score,
            measured_at=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(metric)
        db.session.commit()

        # Trigger hook: after posture fusion
        HookService.trigger_hook("after_posture_fusion", universe=uni, score=global_score)

        return global_score

    @staticmethod
    def identify_weak_domains(universe_id: int, org_id: int) -> list:
        """Identify domains with metrics below critical boundaries."""
        domains = DefenseDomain.query.filter_by(universe_id=universe_id, organization_id=org_id).all()
        weak = []
        for d in domains:
            if d.health_score < 0.6 or d.readiness_score < 0.6:
                weak.append({
                    'domain_id': d.id,
                    'name': d.name,
                    'health': d.health_score,
                    'readiness': d.readiness_score
                })
        return weak

    @staticmethod
    def trend(universe_id: int, org_id: int) -> list:
        """Retrieve chronological trend history of readiness metrics."""
        metrics = (
            UniverseMetric.query
            .filter_by(universe_id=universe_id, organization_id=org_id, metric_type='readiness')
            .order_by(UniverseMetric.measured_at.asc())
            .all()
        )
        return [m.to_dict() for m in metrics]

    @staticmethod
    def executive_snapshot(org_id: int) -> dict:
        """Aggregate high level snapshot parameters for executive visibility."""
        unis = DefenseUniverse.query.filter_by(organization_id=org_id).all()
        if not unis:
            return {'total_universes': 0, 'composite_readiness': 0.0}
        avg_readiness = sum(u.readiness_score for u in unis) / len(unis)
        return {
            'total_universes': len(unis),
            'composite_readiness': round(avg_readiness, 3),
            'status_counts': {
                'active': sum(1 for u in unis if u.status == 'active'),
                'draft': sum(1 for u in unis if u.status == 'draft')
            }
        }
