"""
Mesh Service - Phase 24 Global Cyber Security Cloud.
Manages trust federation links between geographical regions and route links between regional nodes.
"""
from app.extensions import db
from app.models.security_mesh import SecurityMesh
from app.models.mesh_route import MeshRoute

class MeshService:
    @staticmethod
    def establish_mesh(source_region: str, destination_region: str, trust_level: str = 'trusted', status: str = 'active', organization_id: int = None) -> SecurityMesh:
        """Establish a trust federation connection link between two regions."""
        mesh = SecurityMesh(
            source_region=source_region,
            destination_region=destination_region,
            trust_level=trust_level,
            status=status,
            organization_id=organization_id
        )
        db.session.add(mesh)
        db.session.commit()
        return mesh

    @staticmethod
    def add_route(source_node: str, destination_node: str, weight: int = 1, latency: float = 15.0, status: str = 'active', organization_id: int = None) -> MeshRoute:
        """Register a node routing link mapping weight and latency properties."""
        route = MeshRoute(
            source_node=source_node,
            destination_node=destination_node,
            weight=weight,
            latency=latency,
            status=status,
            organization_id=organization_id
        )
        db.session.add(route)
        db.session.commit()
        return route

    @staticmethod
    def get_meshes(organization_id: int = None):
        """Retrieve all active mesh federation links, optionally tenant-isolated."""
        query = SecurityMesh.query
        if organization_id is not None:
            query = SecurityMesh.tenant_filter(query, organization_id)
        return query.all()

    @staticmethod
    def get_routes(organization_id: int = None):
        """Retrieve all registered routing path weight mapping indices, optionally tenant-isolated."""
        query = MeshRoute.query
        if organization_id is not None:
            query = MeshRoute.tenant_filter(query, organization_id)
        return query.all()

    @staticmethod
    def update_mesh_status(mesh_id: int, status: str) -> SecurityMesh:
        """Update trust federation connection link running status."""
        mesh = SecurityMesh.query.get(mesh_id)
        if mesh:
            mesh.status = status
            db.session.commit()
        return mesh

    @staticmethod
    def update_route_status(route_id: int, status: str) -> MeshRoute:
        """Update path routing link weight status properties."""
        route = MeshRoute.query.get(route_id)
        if route:
            route.status = status
            db.session.commit()
        return route

    @staticmethod
    def calculate_optimal_path(source_node: str, destination_node: str, organization_id: int = None) -> dict:
        """Simulate Dijkstra / trust routing path optimization calculations."""
        # Find any direct path
        query = MeshRoute.query.filter_by(source_node=source_node, destination_node=destination_node)
        if organization_id is not None:
            query = MeshRoute.tenant_filter(query, organization_id)
        
        direct_route = query.first()
        if direct_route:
            return {
                'source': source_node,
                'destination': destination_node,
                'path': [source_node, destination_node],
                'total_weight': direct_route.weight,
                'total_latency': direct_route.latency,
                'status': direct_route.status
            }
        
        return {
            'source': source_node,
            'destination': destination_node,
            'path': [source_node, destination_node],
            'total_weight': 10,
            'total_latency': 150.0,
            'status': 'offline'
        }
