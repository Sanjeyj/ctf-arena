"""
Defense REST API Routes - Phase 22 Cyber Defense Operating System.
Handles endpoints for asset inventories, risk postures, reports, events, and knowledge.
JWT-protected.
"""
import base64
import hmac
import hashlib
import json
from functools import wraps
from flask import request, jsonify, current_app
from app.defense import defense_bp
from app.extensions import db

from app.models.asset import Asset
from app.models.security_event import SecurityEvent
from app.models.knowledge_article import KnowledgeArticle
from app.models.executive_report import ExecutiveReport

from app.services.asset_service import AssetService
from app.services.risk_service import RiskService
from app.services.executive_ai_service import ExecutiveAIService
from app.services.event_lake_service import EventLakeService
from app.services.knowledge_hub_service import KnowledgeHubService


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
# Asset Management Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@defense_bp.route('/api/v1/assets', methods=['GET'])
@jwt_required
def list_assets():
    org_id = request.args.get('org_id', type=int)
    q = Asset.query
    if org_id:
        q = q.filter_by(organization_id=org_id)
    assets = q.all()
    return jsonify({"assets": [a.to_dict() for a in assets], "count": len(assets)}), 200


@defense_bp.route('/api/v1/assets', methods=['POST'])
@jwt_required
def create_asset():
    data = request.get_json(silent=True) or {}
    if 'name' not in data:
        return jsonify({"error": "Missing required field: name"}), 400
        
    asset = AssetService.discover(
        name=data['name'],
        type_label=data.get('type_label', 'server'),
        criticality=data.get('criticality', 5),
        ip_address=data.get('ip_address'),
        org_id=data.get('org_id')
    )
    return jsonify({"asset": asset.to_dict()}), 201


# ─────────────────────────────────────────────────────────────────────────────
# Risk Engine Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@defense_bp.route('/api/v1/risk', methods=['GET'])
@jwt_required
def get_risk_status():
    org_id = request.args.get('org_id', type=int)
    
    org_risk = RiskService.calculate_organization_risk(org_id)
    threat_risk = RiskService.calculate_threat_risk()
    
    return jsonify({
        "organization_risk": org_risk,
        "threat_risk": threat_risk
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# Executive Reporting Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@defense_bp.route('/api/v1/executive', methods=['GET'])
@jwt_required
def get_executive_summary():
    org_id = request.args.get('org_id', type=int)
    
    # Query parameters metrics
    reports = ExecutiveReport.query.filter_by(organization_id=org_id).all() if org_id else ExecutiveReport.query.all()
    
    # Simple simulated metrics overview
    summary = {
        "open_incidents": 2,
        "risk_score": 45.0,
        "asset_health": 98.5,
        "training_status": "90% complete",
        "threat_level": "LOW",
        "reports_count": len(reports)
    }
    return jsonify({"summary": summary}), 200


# ─────────────────────────────────────────────────────────────────────────────
# Security Data Lake Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@defense_bp.route('/api/v1/events', methods=['GET'])
@jwt_required
def get_lake_events():
    org_id = request.args.get('org_id', type=int)
    event_type = request.args.get('event_type')
    
    if event_type:
        events = EventLakeService.aggregate(event_type, org_id=org_id)
    else:
        q = SecurityEvent.query
        if org_id:
            q = q.filter_by(organization_id=org_id)
        events = q.all()
        
    return jsonify({"events": [e.to_dict() for e in events], "count": len(events)}), 200


# ─────────────────────────────────────────────────────────────────────────────
# Knowledge Hub Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@defense_bp.route('/api/v1/knowledge', methods=['GET'])
@jwt_required
def search_articles():
    org_id = request.args.get('org_id', type=int)
    query = request.args.get('q')
    category = request.args.get('category')
    
    if query:
        articles = KnowledgeHubService.search(query, org_id=org_id)
    elif category:
        articles = KnowledgeHubService.recommend(category, org_id=org_id)
    else:
        q = KnowledgeArticle.query
        if org_id:
            q = q.filter_by(organization_id=org_id)
        articles = q.all()
        
    return jsonify({"articles": [a.to_dict() for a in articles], "count": len(articles)}), 200
