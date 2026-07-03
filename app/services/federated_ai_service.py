"""
Federated AI Service - Phase 24 Global Cyber Security Cloud.
Resolves cross-region threat correlation and intelligence recommendations among federated agents.
"""
from app.extensions import db
from app.models.agent_node import AgentNode
from app.models.security_mesh import SecurityMesh
from app.services.reputation_cloud_service import ReputationCloudService

class FederatedAIService:
    @staticmethod
    def register_agent(name: str, agent_type: str = 'SOC Agent', status: str = 'active', organization_id: int = None) -> AgentNode:
        """Register a new federated AI agent instance in the network."""
        agent = AgentNode(
            name=name,
            agent_type=agent_type,
            status=status,
            organization_id=organization_id
        )
        db.session.add(agent)
        db.session.commit()
        return agent

    @staticmethod
    def get_agents(organization_id: int = None):
        """Retrieve registered AI agents, optionally filtered by tenant."""
        query = AgentNode.query
        if organization_id is not None:
            query = AgentNode.tenant_filter(query, organization_id)
        return query.all()

    @staticmethod
    def correlate_intelligence(indicator: str, organization_id: int = None) -> dict:
        """Correlate threat indicators across active mesh-linked agent regions."""
        # 1. Fetch active agents
        agents = FederatedAIService.get_agents(organization_id)
        active_agents_count = len([a for a in agents if a.status == 'active'])

        # 2. Fetch reputational rating
        reputation = ReputationCloudService.get_reputation(indicator, organization_id)
        reputation_score = reputation.score if reputation else 50
        reputation_level = reputation.level if reputation else 'medium'

        # 3. Check connectivity state via meshes
        meshes = SecurityMesh.query
        if organization_id is not None:
            meshes = SecurityMesh.tenant_filter(meshes, organization_id)
        active_meshes = meshes.filter_by(status='active').all()

        # Simulating cross-region detection based on score and active networks
        detected_regions = []
        if reputation_score > 70:
            detected_regions = ['us-east', 'eu-west']
        elif reputation_score > 40:
            detected_regions = ['us-east']

        recommendations = []
        if reputation_score >= 80:
            recommendations = [
                f"Block indicator {indicator} at all perimeter firewalls.",
                "Isolate nodes communicating with this entity immediately.",
                "Trigger automatic forensic collection on affected assets."
            ]
        elif reputation_score >= 50:
            recommendations = [
                f"Flag {indicator} and monitor associated connection logs.",
                "Increase logging verbosity for affected subnets."
            ]
        else:
            recommendations = [
                f"Log indicator {indicator} for future reference."
            ]

        return {
            'indicator': indicator,
            'reputation_score': reputation_score,
            'severity': reputation_level,
            'active_agent_nodes': active_agents_count,
            'active_mesh_connections': len(active_meshes),
            'detected_regions': detected_regions,
            'recommendations': recommendations,
            'correlation_status': 'complete'
        }
