import datetime
import json
import random
from app.extensions import db
from app.models.policy_optimization_run import PolicyOptimizationRun
from app.models.control_policy import ControlPolicy


class PolicyOptimizationService:
    @staticmethod
    def create_run(policy_id, opt_type, seed, org_id):
        # Validate target policy ownership
        policy = ControlPolicy.query.filter_by(id=policy_id, organization_id=org_id).first()
        if not policy:
            raise ValueError("ControlPolicy not found or tenant mismatch")

        run = PolicyOptimizationRun(
            policy_id=policy_id,
            optimization_type=opt_type,
            baseline_score=50.0,
            optimized_score=50.0,
            risk_before=60.0,
            risk_after=60.0,
            constraint_count=0,
            random_seed=seed,
            status='pending',
            started_at=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(run)
        db.session.commit()
        return run

    @staticmethod
    def evaluate_policy(policy):
        # Static baseline calculation logic
        # High value rule configurations yield high baseline
        try:
            rules = json.loads(policy.rule_json or '{}')
        except Exception:
            rules = {}
        rule_count = len(rules)
        score = min(100.0, 30.0 + (rule_count * 10.0))
        return score

    @staticmethod
    def simulate_adjustment(run_id, org_id):
        run = PolicyOptimizationRun.query.filter_by(id=run_id, organization_id=org_id).first()
        if not run:
            return None

        policy = ControlPolicy.query.filter_by(id=run.policy_id, organization_id=org_id).first()
        if not policy:
            return None

        # Seed configuration for deterministic reproducibility
        if run.random_seed is not None:
            random.seed(run.random_seed)

        # Baseline evaluation
        baseline = PolicyOptimizationService.evaluate_policy(policy)
        run.baseline_score = baseline
        run.risk_before = max(0.0, min(100.0, 100.0 - baseline))

        # Adjust parameters deterministically or randomly based on seed
        gain = random.uniform(5.0, 25.0)
        run.optimized_score = round(max(0.0, min(100.0, baseline + gain)), 2)
        run.risk_after = round(max(0.0, min(100.0, run.risk_before - (gain * 0.8))), 2)
        run.constraint_count = random.randint(1, 5)

        # Recommendation JSON configuration
        run.recommendation_json = json.dumps({
            'parameter_adjustments': {
                'enforcement_mode': 'require_approval' if policy.enforcement_mode == 'observe' else 'deny_simulation',
                'rule_expansion': True
            },
            'expected_effectiveness_gain': round(gain, 2)
        })

        run.status = 'completed'
        run.completed_at = datetime.datetime.utcnow()
        db.session.commit()
        return run

    @staticmethod
    def calculate_improvement(run):
        return max(0.0, run.optimized_score - run.baseline_score)

    @staticmethod
    def validate_constraints(run_id, constraint_json, org_id):
        run = PolicyOptimizationRun.query.filter_by(id=run_id, organization_id=org_id).first()
        if not run:
            return False
        # Constraint limits evaluation
        try:
            constraints = json.loads(constraint_json or '{}')
        except Exception:
            return False

        max_risk = constraints.get('max_acceptable_risk', 100.0)
        if run.risk_after > max_risk:
            return False
        return True

    @staticmethod
    def recommend_adjustment(run_id, org_id):
        run = PolicyOptimizationRun.query.filter_by(id=run_id, organization_id=org_id).first()
        if not run:
            return None
        return json.loads(run.recommendation_json or '{}')

    @staticmethod
    def compare_runs(run1_id, run2_id, org_id):
        r1 = PolicyOptimizationRun.query.filter_by(id=run1_id, organization_id=org_id).first()
        r2 = PolicyOptimizationRun.query.filter_by(id=run2_id, organization_id=org_id).first()
        if not r1 or not r2:
            return None
        return {
            'run1': {'id': r1.id, 'score': r1.optimized_score, 'risk': r1.risk_after},
            'run2': {'id': r2.id, 'score': r2.optimized_score, 'risk': r2.risk_after},
            'score_diff': round(r2.optimized_score - r1.optimized_score, 2)
        }

    @staticmethod
    def optimization_summary(org_id):
        runs = PolicyOptimizationRun.query.filter_by(organization_id=org_id, status='completed').all()
        avg_baseline = sum(r.baseline_score for r in runs) / len(runs) if runs else 0.0
        avg_optimized = sum(r.optimized_score for r in runs) / len(runs) if runs else 0.0
        return {
            'total_runs': len(runs),
            'average_baseline_score': round(avg_baseline, 2),
            'average_optimized_score': round(avg_optimized, 2),
            'average_improvement': round(avg_optimized - avg_baseline, 2)
        }
