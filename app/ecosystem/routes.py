"""
Ecosystem REST API Routes - Phase 20 Global Cybersecurity Ecosystem.
Handles bug bounties, researcher lookups, marketplace assets, trust federation, and reputation tiers.
JWT-protected.
"""
import base64
import hmac
import hashlib
import json
import datetime
from functools import wraps
from flask import request, jsonify, current_app
from app.ecosystem import ecosystem_bp
from app.extensions import db

from app.models.program import Program
from app.models.vulnerability_report import VulnerabilityReport
from app.models.researcher_profile import ResearcherProfile
from app.models.marketplace_item import MarketplaceItem
from app.models.marketplace_category import MarketplaceCategory
from app.models.organization_trust import OrganizationTrust

from app.services.researcher_service import ResearcherService
from app.services.reputation_service import ReputationService
from app.services.marketplace_service import MarketplaceService


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
# Bug Bounty Program & Report Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@ecosystem_bp.route('/api/v1/bounties', methods=['GET'])
@jwt_required
def list_bounties():
    """Retrieve all reports for the request org or researcher."""
    org_id = request.args.get('org_id', type=int)
    q = VulnerabilityReport.query
    if org_id:
        q = q.filter_by(organization_id=org_id)
    reports = q.all()
    return jsonify({"vulnerability_reports": [r.to_dict() for r in reports], "count": len(reports)}), 200


@ecosystem_bp.route('/api/v1/bounties', methods=['POST'])
@jwt_required
def submit_bounty():
    """Submit a new vulnerability report to a bounty program."""
    data = request.get_json(silent=True) or {}
    required = ['program_id', 'title', 'description']
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
            
    program = db.session.get(Program, data['program_id'])
    if not program:
        return jsonify({"error": f"Program {data['program_id']} not found"}), 404

    # Determine CVSS & Severity
    cvss = data.get('cvss_score', 5.0)
    if cvss >= 9.0:
        sev = 'critical'
    elif cvss >= 7.0:
        sev = 'high'
    elif cvss >= 4.0:
        sev = 'medium'
    else:
        sev = 'low'

    report = VulnerabilityReport(
        program_id=program.id,
        researcher_id=data.get('researcher_id'),
        title=data['title'],
        description=data['description'],
        cvss_score=cvss,
        severity=sev,
        status='submitted',
        reputation_points=int(cvss * 10),
        organization_id=data.get('org_id')
    )
    db.session.add(report)
    db.session.commit()
    return jsonify({"vulnerability_report": report.to_dict()}), 201


# ─────────────────────────────────────────────────────────────────────────────
# Researcher Profiles Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@ecosystem_bp.route('/api/v1/researchers', methods=['GET'])
@jwt_required
def get_researchers():
    org_id = request.args.get('org_id', type=int)
    q = ResearcherProfile.query
    if org_id:
        q = q.filter_by(organization_id=org_id)
    profiles = q.all()
    return jsonify({"researchers": [p.to_dict() for p in profiles], "count": len(profiles)}), 200


# ─────────────────────────────────────────────────────────────────────────────
# Cyber Reputation Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@ecosystem_bp.route('/api/v1/reputation', methods=['GET'])
@jwt_required
def get_reputation():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({"error": "Missing user_id query parameter"}), 400
    rep = ReputationService.calculate_reputation(user_id)
    return jsonify({"reputation": rep}), 200


# ─────────────────────────────────────────────────────────────────────────────
# Marketplace Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@ecosystem_bp.route('/api/v1/marketplace', methods=['GET'])
@jwt_required
def list_marketplace_items():
    org_id = request.args.get('org_id', type=int)
    q = MarketplaceItem.query
    if org_id:
        q = q.filter_by(organization_id=org_id)
    items = q.all()
    return jsonify({"marketplace_items": [i.to_dict() for i in items], "count": len(items)}), 200


# ─────────────────────────────────────────────────────────────────────────────
# Federation Trust Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@ecosystem_bp.route('/api/v1/federation', methods=['GET'])
@jwt_required
def list_federations():
    org_id = request.args.get('org_id', type=int)
    q = OrganizationTrust.query
    if org_id:
        q = q.filter((OrganizationTrust.source_org_id == org_id) | (OrganizationTrust.target_org_id == org_id))
    trusts = q.all()
    return jsonify({"federation_links": [t.to_dict() for t in trusts], "count": len(trusts)}), 200
