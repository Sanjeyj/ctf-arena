"""
Cloud REST API and Admin Routes - Phase 24 Global Cyber Security Cloud.
Handles endpoints for cloud regions, nodes, security mesh, threat reputation, and federated AI.
"""
import base64
import hmac
import hashlib
import json
from functools import wraps
from flask import request, jsonify, current_app, render_template
from flask_login import current_user

from app.cloud import cloud_bp
from app.extensions import db
from app.utils.decorators import require_admin

# Import new Phase 24 models
from app.models.cloud_region import CloudRegion
from app.models.cloud_node import CloudNode
from app.models.security_mesh import SecurityMesh
from app.models.mesh_route import MeshRoute
from app.models.threat_reputation import ThreatReputation
from app.models.agent_node import AgentNode
from app.models.resilience_score import ResilienceScore
from app.models.cloud_service import CloudService

# Import services
from app.services.cloud_service_manager import CloudServiceManager
from app.services.mesh_service import MeshService
from app.services.reputation_cloud_service import ReputationCloudService
from app.services.resilience_service import ResilienceService
from app.services.federated_ai_service import FederatedAIService

# ─────────────────────────────────────────────────────────────────────────────
# Lightweight JWT Crypto Helpers (Standard Library only)
# ─────────────────────────────────────────────────────────────────────────────

def decode_jwt(token: str, secret: str) -> dict:
    """Decode and verify signature of an HS256 JWT token."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        
        # Verify signature
        signature_input = f"{header_b64}.{payload_b64}"
        sig = hmac.new(secret.encode(), signature_input.encode(), hashlib.sha256).digest()
        
        def add_padding(val):
            return val + "=" * (4 - len(val) % 4)
            
        expected_sig_b64 = base64.urlsafe_b64encode(sig).decode().rstrip("=")
        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            return None
            
        payload_json = base64.urlsafe_b64decode(add_padding(payload_b64)).decode()
        return json.loads(payload_json)
    except Exception:
        return None


def jwt_required(f):
    """Decorator to enforce JWT Bearer token authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid authorization header"}), 401
        
        token = auth_header.split(' ')[1]
        secret = current_app.config.get('SECRET_KEY', 'default_secret')
        payload = decode_jwt(token, secret)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
            
        request.jwt_payload = payload
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────────────────────────────────────
# Admin Dashboards
# ─────────────────────────────────────────────────────────────────────────────

@cloud_bp.route('/admin/cloud', methods=['GET'])
@require_admin
def admin_cloud():
    """Render admin cloud control panel dashboard."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int)
    regions = CloudServiceManager.get_regions(org_id)
    nodes = CloudServiceManager.get_nodes(org_id)
    services = CloudServiceManager.get_services(org_id)
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_cloud.html',
        regions=regions,
        nodes=nodes,
        services=services,
        current_org_id=org_id,
        stats=stats,
        challenges=challenges,
        leaderboard=[]
    )


@cloud_bp.route('/admin/cloud/regions', methods=['GET'])
@require_admin
def admin_regions():
    """Render detailed admin cloud regions dashboard."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int)
    regions = CloudServiceManager.get_regions(org_id)
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_regions.html',
        regions=regions,
        current_org_id=org_id,
        stats=stats,
        challenges=challenges,
        leaderboard=[]
    )


@cloud_bp.route('/admin/cloud/mesh', methods=['GET'])
@require_admin
def admin_mesh():
    """Render admin security mesh dashboard."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int)
    meshes = MeshService.get_meshes(org_id)
    routes = MeshService.get_routes(org_id)
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_mesh.html',
        meshes=meshes,
        routes=routes,
        current_org_id=org_id,
        stats=stats,
        challenges=challenges,
        leaderboard=[]
    )


@cloud_bp.route('/admin/cloud/resilience', methods=['GET'])
@require_admin
def admin_resilience():
    """Render admin organization resilience scores dashboard."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int) or 1
    score = ResilienceService.get_latest_score(org_id)
    history = ResilienceService.get_history(org_id)
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_resilience.html',
        score=score,
        history=history,
        current_org_id=org_id,
        stats=stats,
        challenges=challenges,
        leaderboard=[]
    )


@cloud_bp.route('/admin/cloud/federation', methods=['GET'])
@require_admin
def admin_global_ai():
    """Render admin federated AI coordination dashboard."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int)
    agents = FederatedAIService.get_agents(org_id)
    _, stats, challenges = AdminService.get_dashboard_stats()
    return render_template(
        'admin_global_ai.html',
        agents=agents,
        current_org_id=org_id,
        stats=stats,
        challenges=challenges,
        leaderboard=[]
    )


# ─────────────────────────────────────────────────────────────────────────────
# REST API - Cloud Management
# ─────────────────────────────────────────────────────────────────────────────

@cloud_bp.route('/api/v1/cloud', methods=['GET'])
@jwt_required
def api_get_cloud_config():
    """Get active cloud regions, nodes, and services configs."""
    org_id = request.args.get('org_id', type=int)
    regions = [r.to_dict() for r in CloudServiceManager.get_regions(org_id)]
    nodes = [n.to_dict() for n in CloudServiceManager.get_nodes(org_id)]
    services = [s.to_dict() for s in CloudServiceManager.get_services(org_id)]
    
    return jsonify({
        'regions': regions,
        'nodes': nodes,
        'services': services
    }), 200


@cloud_bp.route('/api/v1/cloud/region', methods=['POST'])
@jwt_required
def api_create_region():
    """Register a new cloud region."""
    data = request.get_json() or {}
    if not data.get('name') or not data.get('slug'):
        return jsonify({'error': 'name and slug are required'}), 400
    
    region = CloudServiceManager.create_region(
        name=data['name'],
        slug=data['slug'],
        region_code=data.get('region_code'),
        location=data.get('location'),
        organization_id=data.get('organization_id')
    )
    return jsonify(region.to_dict()), 201


@cloud_bp.route('/api/v1/cloud/node', methods=['POST'])
@jwt_required
def api_create_node():
    """Register a new cloud node instance."""
    data = request.get_json() or {}
    if not data.get('region_id') or not data.get('name'):
        return jsonify({'error': 'region_id and name are required'}), 400
    
    node = CloudServiceManager.create_node(
        region_id=data['region_id'],
        name=data['name'],
        node_type=data.get('node_type', 'SOC Node'),
        status=data.get('status', 'online'),
        organization_id=data.get('organization_id')
    )
    return jsonify(node.to_dict()), 201


@cloud_bp.route('/api/v1/cloud/service', methods=['POST'])
@jwt_required
def api_create_service():
    """Register a new cloud service template mapping."""
    data = request.get_json() or {}
    if not data.get('name'):
        return jsonify({'error': 'name is required'}), 400
    
    service = CloudServiceManager.create_service(
        name=data['name'],
        service_type=data.get('service_type', 'SOC'),
        status=data.get('status', 'running'),
        organization_id=data.get('organization_id')
    )
    return jsonify(service.to_dict()), 201


@cloud_bp.route('/api/v1/cloud/sync', methods=['POST'])
@jwt_required
def api_sync_replication():
    """Trigger configuration sync across federated regions."""
    data = request.get_json() or {}
    org_id = data.get('organization_id')
    result = CloudServiceManager.sync_replication(org_id)
    return jsonify(result), 200


# ─────────────────────────────────────────────────────────────────────────────
# REST API - Security Mesh
# ─────────────────────────────────────────────────────────────────────────────

@cloud_bp.route('/api/v1/mesh', methods=['GET'])
@jwt_required
def api_get_mesh_config():
    """Get active security mesh trust links and routes."""
    org_id = request.args.get('org_id', type=int)
    meshes = [m.to_dict() for m in MeshService.get_meshes(org_id)]
    routes = [r.to_dict() for r in MeshService.get_routes(org_id)]
    return jsonify({
        'meshes': meshes,
        'routes': routes
    }), 200


@cloud_bp.route('/api/v1/mesh/establish', methods=['POST'])
@jwt_required
def api_establish_mesh():
    """Establish trust federation mesh between two regions."""
    data = request.get_json() or {}
    if not data.get('source_region') or not data.get('destination_region'):
        return jsonify({'error': 'source_region and destination_region are required'}), 400
    
    mesh = MeshService.establish_mesh(
        source_region=data['source_region'],
        destination_region=data['destination_region'],
        trust_level=data.get('trust_level', 'trusted'),
        status=data.get('status', 'active'),
        organization_id=data.get('organization_id')
    )
    return jsonify(mesh.to_dict()), 201


@cloud_bp.route('/api/v1/mesh/route', methods=['POST'])
@jwt_required
def api_add_route():
    """Add routing details weight mapping."""
    data = request.get_json() or {}
    if not data.get('source_node') or not data.get('destination_node'):
        return jsonify({'error': 'source_node and destination_node are required'}), 400
    
    route = MeshService.add_route(
        source_node=data['source_node'],
        destination_node=data['destination_node'],
        weight=data.get('weight', 1),
        latency=data.get('latency', 15.0),
        status=data.get('status', 'active'),
        organization_id=data.get('organization_id')
    )
    return jsonify(route.to_dict()), 201


@cloud_bp.route('/api/v1/mesh/optimize', methods=['POST'])
@jwt_required
def api_optimize_path():
    """Lookup Dijkstra latency optimized routing paths."""
    data = request.get_json() or {}
    if not data.get('source_node') or not data.get('destination_node'):
        return jsonify({'error': 'source_node and destination_node are required'}), 400
    
    result = MeshService.calculate_optimal_path(
        source_node=data['source_node'],
        destination_node=data['destination_node'],
        organization_id=data.get('organization_id')
    )
    return jsonify(result), 200


# ─────────────────────────────────────────────────────────────────────────────
# REST API - Threat Reputation
# ─────────────────────────────────────────────────────────────────────────────

@cloud_bp.route('/api/v1/cloud/reputation', methods=['GET'])
@jwt_required
def api_get_reputation():
    """Get threat score ratings ranking lookup for an entity."""
    entity = request.args.get('entity')
    org_id = request.args.get('org_id', type=int)
    if not entity:
        return jsonify({'error': 'entity parameter is required'}), 400
    
    rep = ReputationCloudService.get_reputation(entity, org_id)
    if not rep:
        return jsonify({'entity_value': entity, 'score': 50, 'level': 'medium', 'category': 'unknown'}), 200
    
    return jsonify(rep.to_dict()), 200


@cloud_bp.route('/api/v1/cloud/reputation/update', methods=['POST'])
@jwt_required
def api_update_reputation():
    """Register or update a threat reputational score ranking."""
    data = request.get_json() or {}
    if not data.get('entity_value') or 'score' not in data:
        return jsonify({'error': 'entity_value and score are required'}), 400
    
    rep = ReputationCloudService.update_reputation(
        entity_value=data['entity_value'],
        score=data['score'],
        level=data.get('level'),
        category=data.get('category', 'ioc'),
        organization_id=data.get('organization_id')
    )
    return jsonify(rep.to_dict()), 200


@cloud_bp.route('/api/v1/cloud/reputation/feedback', methods=['POST'])
@jwt_required
def api_submit_reputation_feedback():
    """Feed indicator ratings to adjust global reputation index."""
    data = request.get_json() or {}
    if not data.get('entity_value') or 'rating' not in data:
        return jsonify({'error': 'entity_value and rating are required'}), 400
    
    rep = ReputationCloudService.submit_feedback(
        entity_value=data['entity_value'],
        rating=data['rating'],
        feedback_category=data.get('category', 'ioc'),
        organization_id=data.get('organization_id')
    )
    return jsonify(rep.to_dict()), 200


# ─────────────────────────────────────────────────────────────────────────────
# REST API - Organizational Resilience
# ─────────────────────────────────────────────────────────────────────────────

@cloud_bp.route('/api/v1/resilience', methods=['GET'])
@jwt_required
def api_get_resilience():
    """Get the organization's latest computed cyber resilience ratings score."""
    org_id = request.args.get('org_id', type=int)
    if not org_id:
        return jsonify({'error': 'org_id is required'}), 400
    
    score = ResilienceService.get_latest_score(org_id)
    return jsonify(score.to_dict()), 200


@cloud_bp.route('/api/v1/resilience/calculate', methods=['POST'])
@jwt_required
def api_calculate_resilience():
    """Trigger calculation and persistent recording of resilience index."""
    data = request.get_json() or {}
    org_id = data.get('organization_id')
    if not org_id:
        return jsonify({'error': 'organization_id is required'}), 400
    
    score = ResilienceService.calculate_resilience(org_id)
    return jsonify(score.to_dict()), 200


# ─────────────────────────────────────────────────────────────────────────────
# REST API - Federated AI Coordination
# ─────────────────────────────────────────────────────────────────────────────

@cloud_bp.route('/api/v1/cloud/federation', methods=['GET'])
@jwt_required
def api_get_agents():
    """Get registered AI agents across all cloud zones."""
    org_id = request.args.get('org_id', type=int)
    agents = [a.to_dict() for a in FederatedAIService.get_agents(org_id)]
    return jsonify({'agents': agents}), 200


@cloud_bp.route('/api/v1/cloud/federation/register', methods=['POST'])
@jwt_required
def api_register_agent():
    """Register a new federated AI agent."""
    data = request.get_json() or {}
    if not data.get('name'):
        return jsonify({'error': 'name is required'}), 400
    
    agent = FederatedAIService.register_agent(
        name=data['name'],
        agent_type=data.get('agent_type', 'SOC Agent'),
        status=data.get('status', 'active'),
        organization_id=data.get('organization_id')
    )
    return jsonify(agent.to_dict()), 201


@cloud_bp.route('/api/v1/cloud/federation/correlate', methods=['POST'])
@jwt_required
def api_correlate_threat():
    """Trigger cross-region AI intelligence correlations recommendations."""
    data = request.get_json() or {}
    if not data.get('indicator'):
        return jsonify({'error': 'indicator is required'}), 400
    
    result = FederatedAIService.correlate_intelligence(
        indicator=data['indicator'],
        organization_id=data.get('organization_id')
    )
    return jsonify(result), 200
