"""
Autonomous REST API Routes - Phase 21 Autonomous Security Operations Platform.
Handles AI agent triage, threat hunts, playbooks execution, and prediction engines.
JWT-protected.
"""
import base64
import hmac
import hashlib
import json
import datetime
from functools import wraps
from flask import request, jsonify, current_app
from app.autonomous import autonomous_bp
from app.extensions import db

from app.models.soc_agent import SocAgent
from app.models.threat_hunt_session import ThreatHuntSession
from app.models.playbook import Playbook
from app.models.playbook_execution import PlaybookExecution

from app.services.soc_agent_service import SocAgentService
from app.services.playbook_engine_service import PlaybookEngineService
from app.services.prediction_service import PredictionService
from app.services.knowledge_graph_service import KnowledgeGraphService


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
# AI SOC Agent Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@autonomous_bp.route('/api/v1/agents', methods=['GET'])
@jwt_required
def list_agents():
    org_id = request.args.get('org_id', type=int)
    agents = SocAgentService.list_agents(org_id=org_id)
    return jsonify({"agents": [a.to_dict() for a in agents], "count": len(agents)}), 200


@autonomous_bp.route('/api/v1/agents', methods=['POST'])
@jwt_required
def create_agent():
    data = request.get_json(silent=True) or {}
    if 'name' not in data:
        return jsonify({"error": "Missing required field: name"}), 400
        
    agent = SocAgentService.create_agent(
        name=data['name'],
        role=data.get('role', 'analyst'),
        confidence=data.get('confidence', 0.85),
        model=data.get('model', 'gemini-2.0-pro'),
        org_id=data.get('org_id')
    )
    return jsonify({"agent": agent.to_dict()}), 201


# ─────────────────────────────────────────────────────────────────────────────
# AI Threat Hunter Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@autonomous_bp.route('/api/v1/hunts', methods=['GET'])
@jwt_required
def list_hunt_sessions():
    org_id = request.args.get('org_id', type=int)
    q = ThreatHuntSession.query
    if org_id:
        q = q.filter_by(organization_id=org_id)
    sessions = q.all()
    return jsonify({"hunt_sessions": [s.to_dict() for s in sessions], "count": len(sessions)}), 200


@autonomous_bp.route('/api/v1/hunts', methods=['POST'])
@jwt_required
def create_hunt_session():
    data = request.get_json(silent=True) or {}
    hunt_type = data.get('hunt_type', 'ioc')
    
    session = ThreatHuntSession(
        hunt_type=hunt_type,
        confidence=data.get('confidence', 0.85),
        findings=data.get('findings', 'Threat Hunt Scan completed. No active compromise vectors identified.'),
        recommendations=data.get('recommendations', 'Review host log configurations.'),
        organization_id=data.get('org_id')
    )
    db.session.add(session)
    db.session.commit()
    return jsonify({"hunt_session": session.to_dict()}), 201


# ─────────────────────────────────────────────────────────────────────────────
# Playbook Engine Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@autonomous_bp.route('/api/v1/playbooks', methods=['GET'])
@jwt_required
def list_playbooks():
    org_id = request.args.get('org_id', type=int)
    q = Playbook.query
    if org_id:
        q = q.filter_by(organization_id=org_id)
    playbooks = q.all()
    return jsonify({"playbooks": [p.to_dict() for p in playbooks], "count": len(playbooks)}), 200


@autonomous_bp.route('/api/v1/playbooks', methods=['POST'])
@jwt_required
def trigger_playbook():
    """Trigger simulated execution of a playbook."""
    data = request.get_json(silent=True) or {}
    playbook_id = data.get('playbook_id')
    if not playbook_id:
        return jsonify({"error": "Missing required field: playbook_id"}), 400
        
    try:
        execution = PlaybookEngineService.execute_playbook(
            playbook_id=playbook_id,
            alert_id=data.get('alert_id'),
            org_id=data.get('org_id')
        )
        return jsonify({"execution": execution.to_dict()}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ─────────────────────────────────────────────────────────────────────────────
# Threat Prediction Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@autonomous_bp.route('/api/v1/predictions', methods=['GET'])
@jwt_required
def get_predictions():
    org_id = request.args.get('org_id', type=int)
    predictions = PredictionService.forecast_threats(org_id=org_id)
    return jsonify({"predictions": predictions}), 200


# ─────────────────────────────────────────────────────────────────────────────
# Security Knowledge Graph Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@autonomous_bp.route('/api/v1/knowledge', methods=['GET'])
@jwt_required
def get_knowledge_graph():
    org_id = request.args.get('org_id', type=int)
    graph = KnowledgeGraphService.get_full_graph(org_id=org_id)
    return jsonify({"graph": graph}), 200
