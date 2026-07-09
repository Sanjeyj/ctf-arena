from app.extensions import db
from app.models.governance_objective import GovernanceObjective
from app.models.enterprise_goal import EnterpriseGoal


class GovernanceObjectiveService:
    @staticmethod
    def create_objective(title, obj_type, description, target_score, weight, deadline, owner, org_id):
        valid_types = [
            'risk_reduction', 'resilience', 'compliance', 'assurance',
            'reliability', 'exposure_reduction', 'validation_effectiveness', 'investment_efficiency'
        ]
        if obj_type not in valid_types:
            raise ValueError(f"Invalid objective type: {obj_type}")
        if not (0.0 <= target_score <= 100.0):
            raise ValueError("Target score must be between 0 and 100")
        if not (0.0 <= weight <= 1.0):
            raise ValueError("Weight must be between 0.0 and 1.0")

        obj = GovernanceObjective(
            title=title,
            objective_type=obj_type,
            description=description,
            target_score=target_score,
            current_score=30.0,  # Default starting baseline score
            weight=weight,
            deadline=deadline,
            owner=owner,
            status='proposed',
            organization_id=org_id
        )
        db.session.add(obj)
        db.session.commit()
        return obj

    @staticmethod
    def calculate_progress(obj_id, org_id):
        obj = GovernanceObjective.query.filter_by(id=obj_id, organization_id=org_id).first()
        if not obj:
            return 0.0

        # Integrates with EnterpriseGoal if matching title exists
        goal = EnterpriseGoal.query.filter_by(organization_id=org_id, objective=obj.title).first()
        if goal:
            obj.current_score = goal.progress
        else:
            # Simulated progress update
            pass

        progress = (obj.current_score / obj.target_score) * 100.0 if obj.target_score > 0 else 100.0
        return round(max(0.0, min(100.0, progress)), 2)

    @staticmethod
    def evaluate_target(obj_id, score, org_id):
        obj = GovernanceObjective.query.filter_by(id=obj_id, organization_id=org_id).first()
        if not obj:
            return False
        obj.current_score = max(0.0, min(100.0, score))
        if obj.current_score >= obj.target_score:
            obj.status = 'achieved'
        else:
            obj.status = 'active'
        db.session.commit()
        return obj.current_score >= obj.target_score

    @staticmethod
    def rank_objectives(org_id):
        # Sorts objectives descending by weight
        return GovernanceObjective.query.filter_by(organization_id=org_id).order_by(GovernanceObjective.weight.desc()).all()

    @staticmethod
    def detect_stalled_objectives(org_id):
        # Objectives with current_score < 40.0 and deadline near
        objectives = GovernanceObjective.query.filter_by(organization_id=org_id).all()
        stalled = []
        for obj in objectives:
            if obj.current_score < 40.0 and obj.status not in ['achieved', 'archived']:
                stalled.append(obj)
        return stalled

    @staticmethod
    def update_status(obj_id, status, org_id):
        obj = GovernanceObjective.query.filter_by(id=obj_id, organization_id=org_id).first()
        if not obj:
            return None
        valid_statuses = ['proposed', 'active', 'achieved', 'stalled', 'archived']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}")
        obj.status = status
        db.session.commit()
        return obj

    @staticmethod
    def objective_summary(org_id):
        objectives = GovernanceObjective.query.filter_by(organization_id=org_id).all()
        stalled = GovernanceObjectiveService.detect_stalled_objectives(org_id)
        achieved = sum(1 for o in objectives if o.status == 'achieved')
        return {
            'total_objectives': len(objectives),
            'stalled_objectives': len(stalled),
            'achieved_objectives': achieved
        }
