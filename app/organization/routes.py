from flask import request, jsonify, g
from flask_login import current_user
from app.organization import org_bp
from app.utils.decorators import require_login
from app.services.organization_service import OrganizationService
from app.services.billing_service import BillingService
from app.services.quota_service import QuotaService
from app.models.user import User

@org_bp.route('/api/v1/organization', methods=['GET'])
@require_login
def get_current_organization():
    if not g.current_org:
        return jsonify({'message': 'No organization resolved for this host (default organization context).', 'organization': None}), 200
    
    return jsonify({
        'organization': {
            'id': g.current_org.id,
            'name': g.current_org.name,
            'slug': g.current_org.slug,
            'plan_type': g.current_org.plan_type,
            'status': g.current_org.status,
        }
    }), 200


@org_bp.route('/api/v1/organization', methods=['POST'])
@require_login
def create_organization():
    data = request.get_json(silent=True) or {}
    name = data.get('name')
    slug = data.get('slug')

    if not name or not slug:
        return jsonify({'error': 'name and slug are required.'}), 400

    org, err = OrganizationService.create_org(name, slug, current_user)
    if err:
        return jsonify({'error': err}), 400

    return jsonify({
        'message': 'Organization created successfully.',
        'organization': {
            'id': org.id,
            'name': org.name,
            'slug': org.slug,
            'plan_type': org.plan_type,
        }
    }), 201


@org_bp.route('/api/v1/organization/members', methods=['GET'])
@require_login
def list_organization_members():
    if not g.current_org:
        return jsonify({'error': 'No resolved organization.'}), 404

    members = OrganizationService.get_members(g.current_org)
    return jsonify({
        'members': [
            {
                'id': m.id,
                'user_id': m.user_id,
                'username': m.user.username if m.user else None,
                'role': m.role,
                'joined_at': m.joined_at.isoformat() if m.joined_at else None,
            } for m in members
        ]
    }), 200


@org_bp.route('/api/v1/organization/invite', methods=['POST'])
@require_login
def invite_organization_member():
    if not g.current_org:
        return jsonify({'error': 'No resolved organization.'}), 404

    data = request.get_json(silent=True) or {}
    username = data.get('username')
    role = data.get('role', 'member')

    if not username:
        return jsonify({'error': 'username is required.'}), 400

    user = User.query.filter_by(username=username, is_deleted=False).first()
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    # Check user count quota
    allowed, limit, used = QuotaService.check(g.current_org, 'users')
    if not allowed:
        return jsonify({'error': f'Quota limit reached. Users quota: {limit}.'}), 429

    member, err = OrganizationService.invite_member(g.current_org, user, role, actor_id=current_user.id)
    if err:
        return jsonify({'error': err}), 400

    return jsonify({
        'message': 'User invited successfully.',
        'member': {
            'id': member.id,
            'user_id': member.user_id,
            'role': member.role,
        }
    }), 200


@org_bp.route('/api/v1/billing', methods=['GET'])
@require_login
def get_billing_state():
    if not g.current_org:
        return jsonify({'error': 'No resolved organization.'}), 404

    billing = BillingService.get_billing(g.current_org)
    return jsonify({
        'billing': {
            'plan_type': billing.plan_type,
            'status': billing.status,
            'trial_ends_at': billing.trial_ends_at.isoformat() if billing.trial_ends_at else None,
            'current_period_end': billing.current_period_end.isoformat() if billing.current_period_end else None,
        }
    }), 200


@org_bp.route('/api/v1/billing/upgrade', methods=['POST'])
@require_login
def upgrade_plan():
    if not g.current_org:
        return jsonify({'error': 'No resolved organization.'}), 404

    data = request.get_json(silent=True) or {}
    plan = data.get('plan')

    if not plan:
        return jsonify({'error': 'plan type is required.'}), 400

    success, msg = BillingService.upgrade(g.current_org, plan, actor_id=current_user.id)
    if not success:
        return jsonify({'error': msg}), 400

    return jsonify({'message': msg}), 200


@org_bp.route('/api/v1/billing/cancel', methods=['POST'])
@require_login
def cancel_subscription():
    if not g.current_org:
        return jsonify({'error': 'No resolved organization.'}), 404

    success, msg = BillingService.cancel(g.current_org, actor_id=current_user.id)
    if not success:
        return jsonify({'error': msg}), 400

    return jsonify({'message': msg}), 200


@org_bp.route('/api/v1/subscription', methods=['GET'])
@require_login
def get_subscription_details():
    if not g.current_org:
        return jsonify({'error': 'No resolved organization.'}), 404

    billing = BillingService.get_billing(g.current_org)
    
    # Generate quota usage details
    quotas = {}
    for res in ('users', 'competitions', 'challenges', 'containers', 'ai_tokens', 'storage_mb'):
        allowed, limit, used = QuotaService.check(g.current_org, res)
        quotas[res] = {
            'limit': limit,
            'used': used,
            'available': (limit - used) if limit != -1 else 'unlimited',
        }

    return jsonify({
        'subscription': {
            'plan_type': billing.plan_type,
            'status': billing.status,
            'current_period_end': billing.current_period_end.isoformat() if billing.current_period_end else None,
            'quotas': quotas,
        }
    }), 200
