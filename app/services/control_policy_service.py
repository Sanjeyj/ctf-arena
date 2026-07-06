"""
ControlPolicyService - Phase 31 Cyber Platform Control Plane.
Platform governance and operational policy rules evaluation.
"""
from app.extensions import db
from app.models.control_policy import ControlPolicy
from app.services.hook_service import HookService
import json


class ControlPolicyService:
    @staticmethod
    def create_policy(policy_name: str, policy_type: str, org_id: int, rule: dict = None, enforcement_mode: str = 'observe') -> ControlPolicy:
        """Create platform governance policy rule."""
        rule_str = json.dumps(rule) if rule else None
        pol = ControlPolicy(
            policy_name=policy_name,
            policy_type=policy_type,
            rule_json=rule_str,
            enforcement_mode=enforcement_mode,
            status='active',
            version='1.0.0',
            organization_id=org_id
        )
        db.session.add(pol)
        db.session.commit()
        return pol

    @staticmethod
    def evaluate(policy_id: int, context: dict, org_id: int) -> dict:
        """Evaluate policy rule against a context structure."""
        pol = db.session.get(ControlPolicy, policy_id)
        if not pol or pol.organization_id != org_id:
            return {'status': 'error', 'message': 'Policy not found'}

        # Trigger hook before policy evaluation
        HookService.trigger_hook("before_policy_evaluation", policy=pol, context=context)

        # Basic rule evaluation: check matching fields
        rule = {}
        if pol.rule_json:
            try:
                rule = json.loads(pol.rule_json)
            except Exception:
                pass

        violations = []
        for key, expected_val in rule.items():
            if key not in context:
                violations.append(f"Context missing policy field: {key}")
            elif context[key] != expected_val:
                violations.append(f"Field '{key}' value '{context[key]}' does not match expected '{expected_val}'")

        decision = 'allow'
        if violations:
            if pol.enforcement_mode == 'deny_simulation':
                decision = 'deny_simulation'
            elif pol.enforcement_mode == 'require_approval':
                decision = 'require_approval'
            elif pol.enforcement_mode == 'warn':
                decision = 'warn'
            else:
                decision = 'observe'

        result = {
            'policy_id': pol.id,
            'decision': decision,
            'violations': violations,
            'enforcement_mode': pol.enforcement_mode
        }

        # Trigger hook after policy evaluation
        HookService.trigger_hook("after_policy_evaluation", policy=pol, result=result)

        return result

    @staticmethod
    def enforce(policy_id: int, context: dict, org_id: int) -> str:
        """Shortcut method checking decision string."""
        res = ControlPolicyService.evaluate(policy_id, context, org_id)
        return res.get('decision', 'allow')

    @staticmethod
    def explain(policy_id: int, org_id: int) -> str:
        """Provide detailed human-readable description of policy constraints."""
        pol = db.session.get(ControlPolicy, policy_id)
        if not pol or pol.organization_id != org_id:
            return "Policy not found"
        return f"Policy '{pol.policy_name}' enforces '{pol.policy_type}' rules under mode '{pol.enforcement_mode}'."

    @staticmethod
    def list_violations(universe_id: int, org_id: int) -> list:
        """Identify potential policy violations for a universe (mock interface)."""
        # Search all active policies and run mock evaluations
        pols = ControlPolicy.query.filter_by(organization_id=org_id, status='active').all()
        violations = []
        for p in pols:
            # Mock evaluation context for verification
            res = ControlPolicyService.evaluate(p.id, {'readiness': 0.5}, org_id)
            if res.get('violations'):
                violations.append({
                    'policy_id': p.id,
                    'policy_name': p.policy_name,
                    'violations': res['violations']
                })
        return violations
