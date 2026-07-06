"""
HealthService - Phase 33 Cyber Platform Observability, Reliability & Operations Fabric.
Calculates service composite health scores, records snapshots, assesses dependencies, and evaluates status.
"""
from app.extensions import db
from app.models.service_health_snapshot import ServiceHealthSnapshot
from app.models.platform_service import PlatformService
from app.models.service_dependency import ServiceDependency
from app.services.hook_service import HookService
import datetime


class HealthService:
    @staticmethod
    def record_snapshot(platform_service_id: int, availability: float, latency_ms: float, error_rate: float, saturation: float, org_id: int) -> ServiceHealthSnapshot:
        """Record service health snapshot, triggering hooks and updating PlatformService current state."""
        # Mutation check via before_health_evaluation hook
        hook_results = HookService.trigger_hook(
            'before_health_evaluation',
            platform_service_id=platform_service_id,
            availability=availability,
            latency_ms=latency_ms,
            error_rate=error_rate,
            saturation=saturation,
            org_id=org_id
        )
        for res in hook_results:
            if isinstance(res, dict):
                if 'availability' in res:
                    availability = res['availability']
                if 'latency_ms' in res:
                    latency_ms = res['latency_ms']
                if 'error_rate' in res:
                    error_rate = res['error_rate']
                if 'saturation' in res:
                    saturation = res['saturation']

        srv = db.session.get(PlatformService, platform_service_id)
        if not srv or srv.organization_id != org_id:
            return None

        health_score = HealthService.calculate_health(availability, latency_ms, error_rate, saturation)
        status = HealthService.classify_health(health_score)

        # Update PlatformService status cache
        srv.health_score = round(health_score / 100.0, 3)  # PlatformService expects 0.0 - 1.0 range
        srv.status = status if status != 'critical' else 'unavailable'
        srv.last_heartbeat = datetime.datetime.utcnow()

        snapshot = ServiceHealthSnapshot(
            platform_service_id=platform_service_id,
            health_score=health_score,
            availability=availability,
            latency_ms=latency_ms,
            error_rate=error_rate,
            saturation=saturation,
            status=status,
            measured_at=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(snapshot)
        db.session.commit()

        HookService.trigger_hook('after_health_evaluation', snapshot=snapshot)

        return snapshot

    @staticmethod
    def calculate_health(availability: float, latency_ms: float, error_rate: float, saturation: float) -> float:
        """Calculate composite health score [0.0 - 100.0] based on Golden Signals."""
        # Golden Signals composite score formula:
        # starts at 100. Availability penalty, error rate penalty, saturation penalty, latency penalty.
        # Availability is 0.0 - 1.0 (1.0 is full). Error rate is 0.0 - 1.0. Saturation is 0.0 - 1.0.
        score = 100.0
        score -= (1.0 - max(0.0, min(1.0, availability))) * 50.0
        score -= max(0.0, min(1.0, error_rate)) * 30.0
        score -= max(0.0, min(1.0, saturation)) * 10.0
        # Latency penalty: latency above 200ms degrades health score. 1 point for every 50ms over 200ms, capped at 10 points.
        if latency_ms > 200.0:
            latency_penalty = min(10.0, (latency_ms - 200.0) / 50.0)
            score -= latency_penalty

        return max(0.0, min(100.0, round(score, 2)))

    @staticmethod
    def classify_health(health_score: float) -> str:
        """Classify health score into statuses."""
        if health_score >= 90.0:
            return 'healthy'
        elif health_score >= 75.0:
            return 'warning'
        elif health_score >= 50.0:
            return 'degraded'
        else:
            return 'critical'

    @staticmethod
    def dependency_health(service_id: int, org_id: int) -> dict:
        """Evaluate dependencies health status."""
        srv = db.session.get(PlatformService, service_id)
        if not srv or srv.organization_id != org_id:
            return {}

        deps = ServiceDependency.query.filter_by(source_service_id=service_id, organization_id=org_id).all()
        healthy_deps = []
        warning_deps = []
        degraded_deps = []
        critical_deps = []

        for dep in deps:
            target = db.session.get(PlatformService, dep.target_service_id)
            if target:
                h_score = target.health_score * 100.0  # Scale back to 100
                t_status = target.status
                dep_info = {
                    'service_name': target.service_name,
                    'health_score': h_score,
                    'status': t_status,
                    'criticality': dep.criticality
                }
                if t_status == 'healthy' or h_score >= 90.0:
                    healthy_deps.append(dep_info)
                elif t_status == 'warning' or h_score >= 75.0:
                    warning_deps.append(dep_info)
                elif t_status == 'degraded' or h_score >= 50.0:
                    degraded_deps.append(dep_info)
                else:
                    critical_deps.append(dep_info)

        return {
            'healthy': healthy_deps,
            'warning': warning_deps,
            'degraded': degraded_deps,
            'critical': critical_deps
        }

    @staticmethod
    def health_history(service_id: int, limit: int, org_id: int) -> list:
        """Retrieve recent health snapshot history for a service."""
        return ServiceHealthSnapshot.query.filter_by(
            platform_service_id=service_id,
            organization_id=org_id
        ).order_by(ServiceHealthSnapshot.measured_at.desc()).limit(limit).all()

    @staticmethod
    def health_summary(org_id: int) -> dict:
        """Aggregated stats of service health for tenant dashboard."""
        services = PlatformService.query.filter_by(organization_id=org_id).all()
        if not services:
            return {
                'total_services': 0,
                'healthy_count': 0,
                'warning_count': 0,
                'degraded_count': 0,
                'critical_count': 0,
                'avg_score': 100.0
            }

        healthy = 0
        warning = 0
        degraded = 0
        critical = 0
        total_score = 0.0

        for s in services:
            h_score = s.health_score * 100.0
            total_score += h_score
            status = HealthService.classify_health(h_score)
            if status == 'healthy':
                healthy += 1
            elif status == 'warning':
                warning += 1
            elif status == 'degraded':
                degraded += 1
            else:
                critical += 1

        return {
            'total_services': len(services),
            'healthy_count': healthy,
            'warning_count': warning,
            'degraded_count': degraded,
            'critical_count': critical,
            'avg_score': round(total_score / len(services), 2)
        }
