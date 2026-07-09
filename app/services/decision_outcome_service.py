import datetime
from app.extensions import db
from app.models.decision_outcome import DecisionOutcome
from app.models.decision_recommendation import DecisionRecommendation
from app.models.strategic_decision_record import StrategicDecisionRecord


class DecisionOutcomeService:
    @staticmethod
    def record_outcome(rec_id, decision_record_id, baseline, actual, expected, org_id):
        # Validate ownership of nested elements
        rec = DecisionRecommendation.query.filter_by(id=rec_id, organization_id=org_id).first()
        dec = StrategicDecisionRecord.query.filter_by(id=decision_record_id, organization_id=org_id).first()
        if not rec or not dec:
            raise ValueError("Recommendation or StrategicDecisionRecord not found or tenant mismatch")

        delta = actual - baseline
        variance = delta - expected

        status = 'pending'
        if delta >= expected:
            status = 'effective'
        elif delta > 0:
            status = 'partially_effective'
        elif delta <= 0:
            status = 'ineffective'

        # Check regressed delta
        if delta < -5.0:
            status = 'regressed'

        outcome = DecisionOutcome(
            recommendation_id=rec_id,
            decision_record_id=decision_record_id,
            baseline_metric=baseline,
            result_metric=actual,
            improvement_delta=delta,
            expected_improvement=expected,
            variance=variance,
            outcome_status=status,
            measured_at=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(outcome)
        db.session.commit()
        return outcome

    @staticmethod
    def calculate_variance(outcome_id, org_id):
        outcome = DecisionOutcome.query.filter_by(id=outcome_id, organization_id=org_id).first()
        if not outcome:
            return 0.0
        return outcome.variance

    @staticmethod
    def evaluate_effectiveness(outcome_id, org_id):
        outcome = DecisionOutcome.query.filter_by(id=outcome_id, organization_id=org_id).first()
        if not outcome:
            return 'pending'
        return outcome.outcome_status

    @staticmethod
    def compare_expected_actual(outcome_id, org_id):
        outcome = DecisionOutcome.query.filter_by(id=outcome_id, organization_id=org_id).first()
        if not outcome:
            return None
        return {
            'expected': outcome.expected_improvement,
            'actual': outcome.improvement_delta,
            'variance': outcome.variance
        }

    @staticmethod
    def detect_negative_outcome(outcome_id, org_id):
        outcome = DecisionOutcome.query.filter_by(id=outcome_id, organization_id=org_id).first()
        if not outcome:
            return False
        # Regressed or Ineffective status represent negative outcomes
        return outcome.outcome_status in ['ineffective', 'regressed']

    @staticmethod
    def recommend_review(outcome_id, org_id):
        outcome = DecisionOutcome.query.filter_by(id=outcome_id, organization_id=org_id).first()
        if not outcome:
            return None
        if DecisionOutcomeService.detect_negative_outcome(outcome_id, org_id):
            outcome.outcome_status = 'requires_review'
            outcome.review_notes = "Automatically flag for review due to negative or regressed metric delta."
            db.session.commit()
            return True
        return False

    @staticmethod
    def outcome_summary(org_id):
        outcomes = DecisionOutcome.query.filter_by(organization_id=org_id).all()
        effective = sum(1 for o in outcomes if o.outcome_status == 'effective')
        negative = sum(1 for o in outcomes if o.outcome_status in ['ineffective', 'regressed', 'requires_review'])
        return {
            'total_outcomes': len(outcomes),
            'effective_outcomes': effective,
            'negative_outcomes': negative
        }
