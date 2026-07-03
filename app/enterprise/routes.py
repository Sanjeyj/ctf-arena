"""
Enterprise REST API and Admin Routes - Phase 26 Autonomous Cyber Enterprise.
Defines endpoints for autonomous agents, agent tasks, decisions, self-healing, workflows, and goals.
"""
import base64
import hmac
import hashlib
import json
from functools import wraps
from flask import request, jsonify, current_app, render_template
from flask_login import current_user

from app.enterprise import enterprise_bp
from app.extensions import db
from app.utils.decorators import require_admin

# Import services
from app.services.autonomous_agent_service import AutonomousAgentService
from app.services.decision_engine_service import DecisionEngineService
from app.services.remediation_service import RemediationService
from app.services.compliance_monitor_service import ComplianceMonitorService
from app.services.orchestration_service import OrchestrationService
from app.services.executive_ai_orchestrator import ExecutiveAIOrchestrator

# Import models
from app.models.autonomous_agent import AutonomousAgent
from app.models.agent_task import AgentTask
from app.models.autonomous_decision import AutonomousDecision
from app.models.remediation_action import RemediationAction
from app.models.compliance_monitor import ComplianceMonitor
from app.models.security_workflow import SecurityWorkflow
from app.models.enterprise_goal import EnterpriseGoal
from app.models.digital_worker import DigitalWorker

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
# Admin Dashboard HTML Pages
# ─────────────────────────────────────────────────────────────────────────────

@enterprise_bp.route('/admin/enterprise/agents', methods=['GET'])
@require_admin
def admin_agents():
    """Render autonomous agents status workspace."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int)
    
    agent_query = AutonomousAgent.query
    if org_id:
        agent_query = AutonomousAgent.tenant_filter(agent_query, org_id)
    agents = agent_query.all()
    
    _, stats, challenges = AdminService.get_dashboard_stats()
    
    return render_template(
        'admin_agents.html',
        agents=agents,
        current_org_id=org_id,
        stats=stats,
        challenges=challenges,
        leaderboard=[]
    )


@enterprise_bp.route('/admin/enterprise/decisions', methods=['GET'])
@require_admin
def admin_decisions():
    """Render autonomous decisions ledger & approval center."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int)
    
    decisions_query = AutonomousDecision.query
    if org_id:
        decisions_query = AutonomousDecision.tenant_filter(decisions_query, org_id)
    decisions = decisions_query.all()
    
    _, stats, challenges = AdminService.get_dashboard_stats()
    
    return render_template(
        'admin_decisions.html',
        decisions=decisions,
        current_org_id=org_id,
        stats=stats,
        challenges=challenges,
        leaderboard=[]
    )


@enterprise_bp.route('/admin/enterprise/workflows', methods=['GET'])
@require_admin
def admin_workflows():
    """Render security orchestration workflows registry."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int)
    
    workflow_query = SecurityWorkflow.query
    if org_id:
        workflow_query = SecurityWorkflow.tenant_filter(workflow_query, org_id)
    workflows = workflow_query.all()
    
    _, stats, challenges = AdminService.get_dashboard_stats()
    
    return render_template(
        'admin_workflows.html',
        workflows=workflows,
        current_org_id=org_id,
        stats=stats,
        challenges=challenges,
        leaderboard=[]
    )


@enterprise_bp.route('/admin/enterprise/reremediation', methods=['GET'])
@enterprise_bp.route('/admin/enterprise/remediation', methods=['GET'])
@require_admin
def admin_remediation():
    """Render self-healing remediation actions console."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int)
    
    remediation_query = RemediationAction.query
    if org_id:
        remediation_query = RemediationAction.tenant_filter(remediation_query, org_id)
    actions = remediation_query.all()
    
    _, stats, challenges = AdminService.get_dashboard_stats()
    
    return render_template(
        'admin_remediation.html',
        actions=actions,
        current_org_id=org_id,
        stats=stats,
        challenges=challenges,
        leaderboard=[]
    )


@enterprise_bp.route('/admin/enterprise/dashboard', methods=['GET'])
@require_admin
def admin_enterprise():
    """Render executive autonomous dashboard summary."""
    from app.services.admin_service import AdminService
    org_id = request.args.get('org_id', type=int)
    
    summary = ExecutiveAIOrchestrator.summarize_enterprise(org_id)
    recommendations = ExecutiveAIOrchestrator.recommend_priorities(org_id)
    
    goals_query = EnterpriseGoal.query
    if org_id:
        goals_query = EnterpriseGoal.tenant_filter(goals_query, org_id)
    goals = goals_query.all()
    
    workers_query = DigitalWorker.query
    if org_id:
        workers_query = DigitalWorker.tenant_filter(workers_query, org_id)
    workers = workers_query.all()
    
    _, stats, challenges = AdminService.get_dashboard_stats()
    
    return render_template(
        'admin_enterprise.html',
        summary=summary,
        recommendations=recommendations,
        goals=goals,
        workers=workers,
        current_org_id=org_id,
        stats=stats,
        challenges=challenges,
        leaderboard=[]
    )


# ─────────────────────────────────────────────────────────────────────────────
# REST API Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@enterprise_bp.route('/api/v1/agents', methods=['GET'])
@jwt_required
def api_get_agents():
    """Retrieve all autonomous agents."""
    org_id = request.args.get('org_id', type=int)
    query = AutonomousAgent.query
    if org_id:
        query = AutonomousAgent.tenant_filter(query, org_id)
    agents = [a.to_dict() for a in query.all()]
    return jsonify(agents), 200


@enterprise_bp.route('/api/v1/agents', methods=['POST'])
@jwt_required
def api_create_agent():
    """Deploy a new autonomous agent."""
    data = request.get_json() or {}
    if not data.get('name') or not data.get('role'):
        return jsonify({'error': 'name and role are required'}), 400
        
    agent = AutonomousAgent(
        name=data['name'],
        role=data['role'],
        model=data.get('model', 'gpt-4'),
        confidence=float(data.get('confidence', 0.9)),
        status=data.get('status', 'idle'),
        organization_id=data.get('organization_id')
    )
    db.session.add(agent)
    db.session.commit()
    return jsonify(agent.to_dict()), 201


@enterprise_bp.route('/api/v1/tasks', methods=['GET'])
@jwt_required
def api_get_tasks():
    """Retrieve tasks scheduled for autonomous agents."""
    org_id = request.args.get('org_id', type=int)
    query = AgentTask.query
    if org_id:
        query = AgentTask.tenant_filter(query, org_id)
    tasks = [t.to_dict() for t in query.all()]
    return jsonify(tasks), 200


@enterprise_bp.route('/api/v1/tasks', methods=['POST'])
@jwt_required
def api_post_task():
    """Schedule work task for an agent."""
    data = request.get_json() or {}
    if not data.get('agent_id') or not data.get('task_type'):
        return jsonify({'error': 'agent_id and task_type are required'}), 400
        
    task = AutonomousAgentService.schedule(
        agent_id=data['agent_id'],
        task_type=data['task_type'],
        priority=data.get('priority', 'medium'),
        organization_id=data.get('organization_id')
    )
    return jsonify(task.to_dict()), 201


@enterprise_bp.route('/api/v1/decisions', methods=['GET'])
@jwt_required
def api_get_decisions():
    """Retrieve autonomous decisions."""
    org_id = request.args.get('org_id', type=int)
    query = AutonomousDecision.query
    if org_id:
        query = AutonomousDecision.tenant_filter(query, org_id)
    decisions = [d.to_dict() for d in query.all()]
    return jsonify(decisions), 200


@enterprise_bp.route('/api/v1/remediation', methods=['GET'])
@jwt_required
def api_get_reremediation():
    """Retrieve self-healing actions list."""
    org_id = request.args.get('org_id', type=int)
    query = RemediationAction.query
    if org_id:
        query = RemediationAction.tenant_filter(query, org_id)
    actions = [a.to_dict() for a in query.all()]
    return jsonify(actions), 200


@enterprise_bp.route('/api/v1/workflows', methods=['GET'])
@jwt_required
def api_get_workflows():
    """Retrieve orchestration workflows."""
    org_id = request.args.get('org_id', type=int)
    query = SecurityWorkflow.query
    if org_id:
        query = SecurityWorkflow.tenant_filter(query, org_id)
    workflows = [w.to_dict() for w in query.all()]
    return jsonify(workflows), 200


@enterprise_bp.route('/api/v1/goals', methods=['GET'])
@jwt_required
def api_get_goals():
    """Retrieve strategic objectives and goals."""
    org_id = request.args.get('org_id', type=int)
    query = EnterpriseGoal.query
    if org_id:
        query = EnterpriseGoal.tenant_filter(query, org_id)
    goals = [g.to_dict() for g in query.all()]
    return jsonify(goals), 200
