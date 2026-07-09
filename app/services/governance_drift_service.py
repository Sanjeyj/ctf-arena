import datetime
from app.extensions import db
from app.models.governance_drift_record import GovernanceDriftRecord
from app.models.risk_appetite_profile import RiskAppetiteProfile
from app.models.risk_portfolio_metric import RiskPortfolioMetric
from app.models.control_coverage_map import ControlCoverageMap


class GovernanceDriftService:
    @staticmethod
    def detect_drift(org_id):
        drifts = []

        # 1. Risk appetite drift: check if current residual score exceeds appetite limit
        appetite = RiskAppetiteProfile.query.filter_by(organization_id=org_id, status='active').first()
        portfolio = RiskPortfolioMetric.query.filter_by(organization_id=org_id).order_by(RiskPortfolioMetric.id.desc()).first()

        if appetite and portfolio:
            limit = appetite.maximum_residual_risk_score
            current = portfolio.total_residual_risk
            delta = current - limit
            if delta > 0:
                record = GovernanceDriftService.create_drift_record(
                    'risk_appetite', appetite.id, 'risk_appetite', limit, current, delta, org_id
                )
                drifts.append(record)

        # 2. Control coverage drift: check if overall coverage drops below a baseline (e.g. 70.0)
        coverages = ControlCoverageMap.query.filter_by(organization_id=org_id).all()
        if coverages:
            avg_coverage = sum(c.coverage_percentage for c in coverages) / len(coverages)
            if avg_coverage < 70.0:
                record = GovernanceDriftService.create_drift_record(
                    'control_coverage', None, 'control_coverage', 70.0, avg_coverage, 70.0 - avg_coverage, org_id
                )
                drifts.append(record)

        return drifts

    @staticmethod
    def calculate_delta(baseline, current):
        return current - baseline

    @staticmethod
    def classify_severity(delta):
        if abs(delta) > 30.0:
            return 'critical'
        elif abs(delta) > 15.0:
            return 'high'
        elif abs(delta) > 5.0:
            return 'medium'
        return 'low'

    @staticmethod
    def create_drift_record(res_type, res_id, drift_type, baseline, current, delta, org_id):
        severity = GovernanceDriftService.classify_severity(delta)
        action = f"Review resource {res_type} parameters to align with governance baselines."

        # Clear active matching drift record
        db.session.query(GovernanceDriftRecord).filter_by(
            organization_id=org_id, drift_type=drift_type, status='detected'
        ).delete()
        db.session.commit()

        record = GovernanceDriftRecord(
            resource_type=res_type,
            resource_id=res_id,
            drift_type=drift_type,
            baseline_value=baseline,
            current_value=current,
            drift_delta=delta,
            severity=severity,
            recommended_action=action,
            status='detected',
            detected_at=datetime.datetime.utcnow(),
            organization_id=org_id
        )
        db.session.add(record)
        db.session.commit()
        return record

    @staticmethod
    def recommend_action(drift_id, org_id):
        record = GovernanceDriftRecord.query.filter_by(id=drift_id, organization_id=org_id).first()
        if not record:
            return None
        return record.recommended_action

    @staticmethod
    def resolve_drift(drift_id, org_id):
        # Human governance resolution
        record = GovernanceDriftRecord.query.filter_by(id=drift_id, organization_id=org_id).first()
        if not record:
            return None
        record.status = 'resolved'
        db.session.commit()
        return record

    @staticmethod
    def drift_summary(org_id):
        records = GovernanceDriftRecord.query.filter_by(organization_id=org_id).all()
        active = sum(1 for r in records if r.status == 'detected')
        critical = sum(1 for r in records if r.severity == 'critical' and r.status == 'detected')
        return {
            'total_drift_records': len(records),
            'active_drift_records': active,
            'critical_governance_drift': critical
        }
