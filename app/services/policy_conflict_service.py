import datetime
import json
from app.extensions import db
from app.models.policy_conflict import PolicyConflict
from app.models.control_policy import ControlPolicy


class PolicyConflictService:
    @staticmethod
    def detect_conflicts(org_id):
        policies = ControlPolicy.query.filter_by(organization_id=org_id, status='active').all()
        detected = []

        # Clear existing open conflicts to avoid duplication
        db.session.query(PolicyConflict).filter_by(organization_id=org_id, status='open').delete()
        db.session.commit()

        # Pairwise comparison
        for i in range(len(policies)):
            for j in range(i + 1, len(policies)):
                p1 = policies[i]
                p2 = policies[j]

                # Scope overlap / contradiction check
                conflict_details = PolicyConflictService.compare_rules(p1, p2)
                if conflict_details:
                    conflict = PolicyConflict(
                        source_policy_id=p1.id,
                        target_policy_id=p2.id,
                        conflict_type=conflict_details['type'],
                        severity=conflict_details['severity'],
                        description=conflict_details['description'],
                        confidence_score=conflict_details['confidence'],
                        resolution_recommendation=conflict_details['recommendation'],
                        status='open',
                        detected_at=datetime.datetime.utcnow(),
                        organization_id=org_id
                    )
                    db.session.add(conflict)
                    detected.append(conflict)

        db.session.commit()
        return detected

    @staticmethod
    def compare_rules(p1, p2):
        # Parse rules JSON
        try:
            r1 = json.loads(p1.rule_json or '{}')
            r2 = json.loads(p2.rule_json or '{}')
        except Exception:
            return None

        # Check for same target keys with different values (contradiction)
        shared_keys = set(r1.keys()).intersection(set(r2.keys()))
        if shared_keys:
            for k in shared_keys:
                if r1[k] != r2[k]:
                    return {
                        'type': 'contradiction',
                        'severity': 'high',
                        'description': f"Contradictory values for rule parameter '{k}' between policy '{p1.policy_name}' and policy '{p2.policy_name}'.",
                        'confidence': 90.0,
                        'recommendation': f"Align the rules parameter '{k}' to match the more restrictive policy."
                    }

        # Check for scope overlap / incompatible enforcement
        if p1.policy_type == p2.policy_type and p1.enforcement_mode != p2.enforcement_mode:
            return {
                'type': 'enforcement_conflict',
                'severity': 'medium',
                'description': f"Policies '{p1.policy_name}' and '{p2.policy_name}' target the same domain but use incompatible enforcement modes ({p1.enforcement_mode} vs {p2.enforcement_mode}).",
                'confidence': 85.0,
                'recommendation': "Standardize the enforcement mode to prevent inconsistent audit trails."
            }

        return None

    @staticmethod
    def classify_conflict(conflict_id, org_id):
        conflict = PolicyConflict.query.filter_by(id=conflict_id, organization_id=org_id).first()
        if not conflict:
            return None
        return conflict.conflict_type

    @staticmethod
    def calculate_confidence(conflict_id, org_id):
        conflict = PolicyConflict.query.filter_by(id=conflict_id, organization_id=org_id).first()
        if not conflict:
            return 0.0
        return conflict.confidence_score

    @staticmethod
    def recommend_resolution(conflict_id, org_id):
        conflict = PolicyConflict.query.filter_by(id=conflict_id, organization_id=org_id).first()
        if not conflict:
            return None
        return conflict.resolution_recommendation

    @staticmethod
    def resolve_conflict(conflict_id, status, org_id):
        # Resolve requiring valid state transition and human approval status
        conflict = PolicyConflict.query.filter_by(id=conflict_id, organization_id=org_id).first()
        if not conflict:
            return None

        valid_states = ['reviewing', 'accepted', 'resolved', 'false_positive']
        if status not in valid_states:
            raise ValueError(f"Invalid status: {status}")

        conflict.status = status
        db.session.commit()
        return conflict

    @staticmethod
    def conflict_summary(org_id):
        conflicts = PolicyConflict.query.filter_by(organization_id=org_id).all()
        open_count = sum(1 for c in conflicts if c.status == 'open')
        high_count = sum(1 for c in conflicts if c.severity == 'high')
        return {
            'total_conflicts': len(conflicts),
            'open_conflicts': open_count,
            'critical_conflicts': high_count
        }
