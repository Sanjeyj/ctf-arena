"""
PlatformRegistryService - Phase 31 Cyber Platform Control Plane.
Registry of logical services and platform capabilities.
"""
from app.extensions import db
from app.models.platform_service import PlatformService
from app.models.service_dependency import ServiceDependency
import datetime


class PlatformRegistryService:
    @staticmethod
    def register_service(service_name: str, service_type: str, org_id: int, version: str = '1.0.0', criticality: str = 'medium', owner: str = None) -> PlatformService:
        """Register a logical service or platform capability."""
        srv = PlatformService(
            service_name=service_name,
            service_type=service_type,
            version=version,
            status='healthy',
            health_score=1.0,
            criticality=criticality,
            owner=owner,
            last_heartbeat=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(srv)
        db.session.commit()
        return srv

    @staticmethod
    def update_health(service_id: int, health_score: float, status: str, org_id: int) -> PlatformService:
        """Update service health score and status state."""
        srv = db.session.get(PlatformService, service_id)
        if not srv or srv.organization_id != org_id:
            return None
        srv.health_score = max(0.0, min(1.0, health_score))
        srv.status = status
        db.session.commit()
        return srv

    @staticmethod
    def heartbeat(service_id: int, org_id: int) -> PlatformService:
        """Log simulated heartbeat timestamp update in the database."""
        srv = db.session.get(PlatformService, service_id)
        if not srv or srv.organization_id != org_id:
            return None
        srv.last_heartbeat = datetime.datetime.utcnow()
        db.session.commit()
        return srv

    @staticmethod
    def list_services(org_id: int) -> list:
        """Retrieve list of registered services."""
        return PlatformService.query.filter_by(organization_id=org_id).all()

    @staticmethod
    def dependency_status(service_id: int, org_id: int) -> dict:
        """Retrieve downstream dependencies health status map."""
        srv = db.session.get(PlatformService, service_id)
        if not srv or srv.organization_id != org_id:
            return {}
        deps = ServiceDependency.query.filter_by(source_service_id=service_id, organization_id=org_id).all()
        status_map = {}
        for dep in deps:
            target = db.session.get(PlatformService, dep.target_service_id)
            if target:
                status_map[target.service_name] = {
                    'status': target.status,
                    'health': target.health_score,
                    'criticality': dep.criticality
                }
        return status_map

    @staticmethod
    def platform_summary(org_id: int) -> dict:
        """Compute structural platform health summaries."""
        services = PlatformRegistryService.list_services(org_id)
        if not services:
            return {'total_services': 0, 'overall_health': 1.0, 'degraded_count': 0}
        avg_health = sum(s.health_score for s in services) / len(services)
        degraded = sum(1 for s in services if s.status in ['degraded', 'unavailable'])
        return {
            'total_services': len(services),
            'overall_health': round(avg_health, 3),
            'degraded_count': degraded
        }
