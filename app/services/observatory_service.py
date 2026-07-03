"""
ObservatoryService - Phase 27 Global Security Intelligence Network.
Monitors, aggregates, and alerts on global security observatory node health.
Simulation-only: no live sensor calls.
"""
from app.extensions import db
from app.models.observatory_node import ObservatoryNode


class ObservatoryService:
    ALERT_THRESHOLD = 0.5  # default health threshold

    @staticmethod
    def monitor(org_id: int = None) -> list:
        """Return current health status for all observatory nodes."""
        q = ObservatoryNode.query
        if org_id:
            q = ObservatoryNode.tenant_filter(q, org_id)
        nodes = q.all()
        return [
            {
                'id': n.id,
                'region': n.region,
                'node_type': n.node_type,
                'status': n.status,
                'health': n.health,
            }
            for n in nodes
        ]

    @staticmethod
    def aggregate(region: str) -> dict:
        """Aggregate health metrics across all nodes in a region."""
        nodes = ObservatoryNode.query.filter_by(region=region).all()
        if not nodes:
            return {'region': region, 'node_count': 0, 'avg_health': None, 'status': 'no_data'}
        avg_health = round(sum(n.health for n in nodes) / len(nodes), 3)
        online = sum(1 for n in nodes if n.status == 'online')
        return {
            'region': region,
            'node_count': len(nodes),
            'online_count': online,
            'avg_health': avg_health,
            'status': 'healthy' if avg_health >= 0.7 else 'degraded',
        }

    @staticmethod
    def alert(node_id: int, threshold: float = None) -> dict:
        """Emit an alert if a node health drops below threshold."""
        if threshold is None:
            threshold = ObservatoryService.ALERT_THRESHOLD
        node = db.session.get(ObservatoryNode, node_id)
        if not node:
            return {'alert': False, 'reason': f'Node {node_id} not found'}
        triggered = node.health < threshold
        if triggered and node.status == 'online':
            node.status = 'degraded'
            db.session.commit()
        return {
            'alert': triggered,
            'node_id': node_id,
            'region': node.region,
            'health': node.health,
            'threshold': threshold,
            'status': node.status,
        }
