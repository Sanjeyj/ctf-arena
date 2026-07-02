"""
SOC API Blueprint — Phase 18 Enterprise SOC & Threat Intelligence.
All endpoints simulate SOC operations — no live infrastructure actions.
"""
import datetime
import json
from flask import request, jsonify
from flask_login import current_user
from app.soc import soc_bp
from app.extensions import db

from app.models.ioc import IOC, IOC_TYPES, IOC_SEVERITIES
from app.models.alert import Alert, ALERT_STATUSES, ALERT_SEVERITIES
from app.models.case import Case, CASE_PRIORITIES, CASE_STATUSES
from app.models.hunt import Hunt, HUNT_TYPES
from app.models.sigma_rule import SigmaRule
from app.models.yara_rule import YaraRule

from app.services.threat_intelligence_service import ThreatIntelligenceService
from app.services.siem_service import SIEMService
from app.services.case_service import CaseService
from app.services.hunt_service import HuntService
from app.services.sigma_service import SigmaService
from app.services.yara_service import YaraService
from app.services.soc_ai_service import SOCAIService
from app.services.playbook_service import PlaybookService


# ─────────────────────────────────────────────────────────────────────────────
# IOC Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@soc_bp.route('/api/v1/iocs', methods=['GET'])
def list_iocs():
    org_id = request.args.get('org_id', type=int)
    ioc_type = request.args.get('type')
    severity = request.args.get('severity')
    iocs = ThreatIntelligenceService.list_iocs(
        org_id=org_id, ioc_type=ioc_type, severity=severity
    )
    return jsonify({'iocs': [i.to_dict() for i in iocs], 'count': len(iocs)}), 200


@soc_bp.route('/api/v1/iocs', methods=['POST'])
def create_ioc():
    data = request.get_json(force=True) or {}
    required = ['type', 'value']
    for field in required:
        if field not in data:
            return jsonify({'error': f"Missing field: {field}"}), 400
    try:
        ioc = ThreatIntelligenceService.create_ioc(
            ioc_type=data['type'],
            value=data['value'],
            severity=data.get('severity', 'medium'),
            confidence=data.get('confidence', 50),
            source=data.get('source', 'api'),
            org_id=data.get('org_id'),
            tags=data.get('tags', ''),
            description=data.get('description', ''),
        )
        return jsonify({'ioc': ioc.to_dict()}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@soc_bp.route('/api/v1/iocs/<int:ioc_id>', methods=['GET'])
def get_ioc(ioc_id):
    ioc = ThreatIntelligenceService.get_ioc(ioc_id)
    if not ioc:
        return jsonify({'error': 'IOC not found'}), 404
    return jsonify({'ioc': ioc.to_dict()}), 200


@soc_bp.route('/api/v1/iocs/<int:ioc_id>/enrich', methods=['POST'])
def enrich_ioc(ioc_id):
    try:
        result = ThreatIntelligenceService.enrich_ioc(ioc_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


# ─────────────────────────────────────────────────────────────────────────────
# Alert Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@soc_bp.route('/api/v1/alerts', methods=['GET'])
def list_alerts():
    org_id = request.args.get('org_id', type=int)
    status = request.args.get('status')
    severity = request.args.get('severity')
    alerts = SIEMService.list_alerts(org_id=org_id, status=status, severity=severity)
    return jsonify({'alerts': [a.to_dict() for a in alerts], 'count': len(alerts)}), 200


@soc_bp.route('/api/v1/alerts', methods=['POST'])
def create_alert():
    data = request.get_json(force=True) or {}
    if 'title' not in data:
        return jsonify({'error': 'Missing field: title'}), 400
    severity = data.get('severity', 'medium')
    if severity not in ALERT_SEVERITIES:
        severity = 'medium'
    alert = Alert(
        title=data['title'],
        description=data.get('description', ''),
        severity=severity,
        event_type=data.get('event_type', 'other'),
        source_ip=data.get('source_ip'),
        dest_ip=data.get('dest_ip'),
        raw_event=json.dumps(data.get('raw_event', {})),
        organization_id=data.get('org_id'),
    )
    db.session.add(alert)
    db.session.commit()
    return jsonify({'alert': alert.to_dict()}), 201


@soc_bp.route('/api/v1/alerts/<int:alert_id>', methods=['GET'])
def get_alert(alert_id):
    alert = SIEMService.get_alert(alert_id)
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404
    return jsonify({'alert': alert.to_dict()}), 200


@soc_bp.route('/api/v1/alerts/<int:alert_id>', methods=['PATCH'])
def update_alert(alert_id):
    data = request.get_json(force=True) or {}
    try:
        alert = SIEMService.update_alert(alert_id, **{
            k: v for k, v in data.items()
            if k in ('status', 'assigned_to', 'resolution_notes')
        })
        return jsonify({'alert': alert.to_dict()}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


@soc_bp.route('/api/v1/alerts/<int:alert_id>/triage', methods=['POST'])
def triage_alert(alert_id):
    result = SOCAIService.triage_alert(alert_id)
    if 'error' in result:
        return jsonify(result), 404
    return jsonify(result), 200


# ─────────────────────────────────────────────────────────────────────────────
# Case Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@soc_bp.route('/api/v1/cases', methods=['GET'])
def list_cases():
    org_id = request.args.get('org_id', type=int)
    status = request.args.get('status')
    cases = CaseService.list_cases(org_id=org_id, status=status)
    return jsonify({'cases': [c.to_dict() for c in cases], 'count': len(cases)}), 200


@soc_bp.route('/api/v1/cases', methods=['POST'])
def create_case():
    data = request.get_json(force=True) or {}
    if 'title' not in data:
        return jsonify({'error': 'Missing field: title'}), 400
    try:
        case = CaseService.create_case(
            title=data['title'],
            description=data.get('description', ''),
            priority=data.get('priority', 'medium'),
            analyst_id=data.get('analyst_id'),
            org_id=data.get('org_id'),
            alert_id=data.get('alert_id'),
        )
        return jsonify({'case': case.to_dict()}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@soc_bp.route('/api/v1/cases/<int:case_id>', methods=['GET'])
def get_case(case_id):
    case = CaseService.get_case(case_id)
    if not case:
        return jsonify({'error': 'Case not found'}), 404
    return jsonify({'case': case.to_dict()}), 200


@soc_bp.route('/api/v1/cases/<int:case_id>', methods=['PATCH'])
def update_case(case_id):
    data = request.get_json(force=True) or {}
    try:
        if 'status' in data:
            case = CaseService.transition_case(case_id, data['status'])
        else:
            case = CaseService.get_case(case_id)
            if not case:
                return jsonify({'error': 'Case not found'}), 404
        if 'note' in data:
            CaseService.add_note(case_id, data['note'])
        return jsonify({'case': case.to_dict()}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@soc_bp.route('/api/v1/cases/<int:case_id>/timeline', methods=['GET'])
def case_timeline(case_id):
    try:
        timeline = CaseService.get_timeline(case_id)
        return jsonify({'timeline': timeline, 'count': len(timeline)}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


# ─────────────────────────────────────────────────────────────────────────────
# Hunt Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@soc_bp.route('/api/v1/hunts', methods=['GET'])
def list_hunts():
    org_id = request.args.get('org_id', type=int)
    hunts = HuntService.list_hunts(org_id=org_id)
    return jsonify({'hunts': [h.to_dict() for h in hunts], 'count': len(hunts)}), 200


@soc_bp.route('/api/v1/hunts', methods=['POST'])
def create_hunt():
    data = request.get_json(force=True) or {}
    required = ['name', 'hunt_type']
    for field in required:
        if field not in data:
            return jsonify({'error': f"Missing field: {field}"}), 400
    try:
        hunt = HuntService.create_hunt(
            name=data['name'],
            hunt_type=data['hunt_type'],
            hypothesis=data.get('hypothesis', ''),
            description=data.get('description', ''),
            analyst_id=data.get('analyst_id'),
            org_id=data.get('org_id'),
        )
        return jsonify({'hunt': hunt.to_dict()}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@soc_bp.route('/api/v1/hunts/<int:hunt_id>', methods=['GET'])
def get_hunt(hunt_id):
    hunt = HuntService.get_hunt(hunt_id)
    if not hunt:
        return jsonify({'error': 'Hunt not found'}), 404
    return jsonify({'hunt': hunt.to_dict()}), 200


@soc_bp.route('/api/v1/hunts/<int:hunt_id>/run', methods=['POST'])
def run_hunt(hunt_id):
    data = request.get_json(force=True) or {}
    hunt = HuntService.get_hunt(hunt_id)
    if not hunt:
        return jsonify({'error': 'Hunt not found'}), 404
    try:
        if hunt.hunt_type == 'ioc':
            ioc_values = data.get('ioc_values', [])
            result = HuntService.run_ioc_hunt(hunt_id, ioc_values)
        elif hunt.hunt_type == 'behavioral':
            result = HuntService.run_behavioral_hunt(hunt_id, data.get('pattern', '.*'))
        elif hunt.hunt_type == 'mitre':
            result = HuntService.run_mitre_hunt(hunt_id, data.get('technique_id', 'T1'))
        else:
            result = HuntService.run_anomaly_hunt(hunt_id, data.get('baseline'))
        return jsonify({'result': result}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


# ─────────────────────────────────────────────────────────────────────────────
# Sigma Rule Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@soc_bp.route('/api/v1/sigma-rules', methods=['GET'])
def list_sigma_rules():
    org_id = request.args.get('org_id', type=int)
    rules = SigmaService.list_rules(org_id=org_id)
    return jsonify({'rules': [r.to_dict() for r in rules], 'count': len(rules)}), 200


@soc_bp.route('/api/v1/sigma-rules', methods=['POST'])
def create_sigma_rule():
    data = request.get_json(force=True) or {}
    required = ['title', 'detection_yaml']
    for field in required:
        if field not in data:
            return jsonify({'error': f"Missing field: {field}"}), 400
    rule = SigmaService.create_rule(
        title=data['title'],
        detection_yaml=data['detection_yaml'],
        logsource=data.get('logsource', ''),
        description=data.get('description', ''),
        author=data.get('author', 'api'),
        severity=data.get('severity', 'medium'),
        org_id=data.get('org_id'),
    )
    return jsonify({'rule': rule.to_dict()}), 201


# ─────────────────────────────────────────────────────────────────────────────
# YARA Rule Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@soc_bp.route('/api/v1/yara-rules', methods=['GET'])
def list_yara_rules():
    org_id = request.args.get('org_id', type=int)
    rules = YaraService.list_rules(org_id=org_id)
    return jsonify({'rules': [r.to_dict() for r in rules], 'count': len(rules)}), 200


@soc_bp.route('/api/v1/yara-rules', methods=['POST'])
def create_yara_rule():
    data = request.get_json(force=True) or {}
    required = ['name', 'rule_text']
    for field in required:
        if field not in data:
            return jsonify({'error': f"Missing field: {field}"}), 400
    rule = YaraService.create_rule(
        name=data['name'],
        rule_text=data['rule_text'],
        description=data.get('description', ''),
        author=data.get('author', 'api'),
        org_id=data.get('org_id'),
    )
    return jsonify({'rule': rule.to_dict()}), 201
