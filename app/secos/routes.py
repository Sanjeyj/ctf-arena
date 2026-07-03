"""
SecOS REST API Routes - Phase 23 Security Operating System.
Handles endpoints for compliance controls, governance policies, audits lists,
threat exchanges, and twin simulation scenarios.
JWT-protected.
"""
import base64
import hmac
import hashlib
import json
from functools import wraps
from flask import request, jsonify, current_app
from app.secos import secos_bp
from app.extensions import db

from app.models.compliance_control import ComplianceControl
from app.models.governance_framework import GovernanceFramework
from app.models.policy import Policy
from app.models.audit_finding import AuditFinding
from app.models.shared_ioc import SharedIOC
from app.models.digital_twin import DigitalTwin

from app.services.analytics_service import AnalyticsService
from app.services.threat_exchange_service import ThreatExchangeService
from app.services.warehouse_service import WarehouseService
from app.services.governance_ai_service import GovernanceAIService
from app.services.digital_twin_service import DigitalTwinService


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
# Compliance Controls Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@secos_bp.route('/api/v1/compliance', methods=['GET'])
@jwt_required
def get_compliance_stats():
    org_id = request.args.get('org_id', type=int)
    
    total = ComplianceControl.query.count()
    passed = ComplianceControl.query.filter_by(status='passed').count()
    failed = ComplianceControl.query.filter_by(status='failed').count()
    partial = ComplianceControl.query.filter_by(status='partial').count()

    score = (passed / total * 100.0) if total > 0 else 100.0

    return jsonify({
        "compliance_score": round(score, 2),
        "total_controls": total,
        "passed": passed,
        "failed": failed,
        "partial": partial
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# Governance Policies Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@secos_bp.route('/api/v1/governance', methods=['GET'])
@jwt_required
def get_governance_maturity():
    org_id = request.args.get('org_id', type=int)
    
    maturity = AnalyticsService.organization_maturity(org_id)
    training = AnalyticsService.training_score(org_id)
    
    policies = Policy.query.all()

    return jsonify({
        "maturity_index": maturity,
        "training_completion_score": training,
        "policies_count": len(policies)
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# Audit Findings Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@secos_bp.route('/api/v1/audits', methods=['GET'])
@jwt_required
def list_findings():
    org_id = request.args.get('org_id', type=int)
    q = AuditFinding.query
    if org_id:
        q = q.filter_by(organization_id=org_id)
    findings = q.all()
    return jsonify({"audit_findings": [f.to_dict() for f in findings], "count": len(findings)}), 200


# ─────────────────────────────────────────────────────────────────────────────
# Threat Exchange Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@secos_bp.route('/api/v1/exchange', methods=['GET'])
@jwt_required
def get_exchange_data():
    org_id = request.args.get('org_id', type=int)
    trust_level = request.args.get('trust_level')
    
    iocs = ThreatExchangeService.list_shared_indicators(trust_level, org_id)
    return jsonify({"shared_iocs": [i.to_dict() for i in iocs], "count": len(iocs)}), 200


# ─────────────────────────────────────────────────────────────────────────────
# Digital Twin Simulation Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@secos_bp.route('/api/v1/digital-twin', methods=['GET'])
@jwt_required
def get_digital_twin_scenarios():
    org_id = request.args.get('org_id', type=int)
    q = DigitalTwin.query
    if org_id:
        q = q.filter_by(organization_id=org_id)
    twins = q.all()
    return jsonify({"digital_twins": [t.to_dict() for t in twins], "count": len(twins)}), 200
