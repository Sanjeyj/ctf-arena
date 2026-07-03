"""
Cloud Service Manager - Phase 24 Global Cyber Security Cloud.
Handles deployment and lifecycle management of cloud regions, nodes, and service templates.
"""
from app.extensions import db
from app.models.cloud_region import CloudRegion
from app.models.cloud_node import CloudNode
from app.models.cloud_service import CloudService

class CloudServiceManager:
    @staticmethod
    def create_region(name: str, slug: str, region_code: str = None, location: str = None, organization_id: int = None) -> CloudRegion:
        """Register a new global cloud geographical region."""
        region = CloudRegion(
            name=name,
            slug=slug,
            region_code=region_code,
            location=location,
            organization_id=organization_id
        )
        db.session.add(region)
        db.session.commit()
        return region

    @staticmethod
    def get_regions(organization_id: int = None):
        """Retrieve all registered cloud regions, optionally filtered by tenant."""
        query = CloudRegion.query
        if organization_id is not None:
            query = CloudRegion.tenant_filter(query, organization_id)
        return query.all()

    @staticmethod
    def create_node(region_id: int, name: str, node_type: str = 'SOC Node', status: str = 'online', organization_id: int = None) -> CloudNode:
        """Provision a node instance inside a specified geographical region."""
        node = CloudNode(
            region_id=region_id,
            name=name,
            node_type=node_type,
            status=status,
            organization_id=organization_id
        )
        db.session.add(node)
        db.session.commit()
        return node

    @staticmethod
    def get_nodes(organization_id: int = None, region_id: int = None):
        """Retrieve regional node instances, optionally filtered by tenant or region."""
        query = CloudNode.query
        if organization_id is not None:
            query = CloudNode.tenant_filter(query, organization_id)
        if region_id is not None:
            query = query.filter_by(region_id=region_id)
        return query.all()

    @staticmethod
    def create_service(name: str, service_type: str = 'SOC', status: str = 'running', organization_id: int = None) -> CloudService:
        """Create a service mapping instance in the global security cloud."""
        service = CloudService(
            name=name,
            service_type=service_type,
            status=status,
            organization_id=organization_id
        )
        db.session.add(service)
        db.session.commit()
        return service

    @staticmethod
    def get_services(organization_id: int = None):
        """Retrieve all active cloud services, optionally filtered by tenant."""
        query = CloudService.query
        if organization_id is not None:
            query = CloudService.tenant_filter(query, organization_id)
        return query.all()

    @staticmethod
    def update_node_status(node_id: int, status: str) -> CloudNode:
        """Update node state to online, degraded, or offline."""
        node = CloudNode.query.get(node_id)
        if node:
            node.status = status
            db.session.commit()
        return node

    @staticmethod
    def update_service_status(service_id: int, status: str) -> CloudService:
        """Update service running status mapping."""
        service = CloudService.query.get(service_id)
        if service:
            service.status = status
            db.session.commit()
        return service

    @staticmethod
    def sync_replication(organization_id: int = None) -> dict:
        """Simulate global configuration replication and returns state metadata."""
        regions = CloudServiceManager.get_regions(organization_id)
        nodes = CloudServiceManager.get_nodes(organization_id)
        services = CloudServiceManager.get_services(organization_id)
        return {
            'success': True,
            'synchronized_regions': len(regions),
            'synchronized_nodes': len(nodes),
            'synchronized_services': len(services),
            'status': 'healthy'
        }
