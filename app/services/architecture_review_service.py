"""
ArchitectureReviewService - Phase 34 Security Architecture, Exposure & Attack Surface Management Fabric.
Manages compliance architectural reviews and risk assessments.
"""
from app.extensions import db
from app.models.architecture_review import ArchitectureReview
from app.models.exposure_finding import ExposureFinding
import datetime


class ArchitectureReviewService:

    @staticmethod
    def create_review(title, scope, review_type, reviewer, summary, org_id):
        review = ArchitectureReview(
            title=title,
            scope=scope,
            review_type=review_type,
            reviewer=reviewer,
            summary=summary,
            organization_id=org_id
        )
        db.session.add(review)
        db.session.commit()
        return review

    @staticmethod
    def evaluate_scope(review_id, org_id):
        review = ArchitectureReview.query.filter_by(id=review_id, organization_id=org_id).first()
        if not review:
            return {"status": "unknown"}
        # Analyze review scope mapping
        return {
            "review_id": review.id,
            "status": "ready",
            "scope": review.scope
        }

    @staticmethod
    def attach_findings(review_id, finding_ids, org_id):
        review = ArchitectureReview.query.filter_by(id=review_id, organization_id=org_id).first()
        if not review:
            return None

        # Resolve and map findings
        findings = ExposureFinding.query.filter(
            ExposureFinding.id.in_(finding_ids),
            ExposureFinding.organization_id == org_id
        ).all()

        review.findings_count = len(findings)
        # Calculate risk score
        risk = 0.0
        for f in findings:
            risk += f.impact_score * f.likelihood
        if findings:
            risk = round(risk / len(findings), 2)
        review.risk_score = risk

        db.session.commit()
        return review

    @staticmethod
    def calculate_review_risk(review_id, org_id):
        review = ArchitectureReview.query.filter_by(id=review_id, organization_id=org_id).first()
        if not review:
            return 0.0
        return review.risk_score

    @staticmethod
    def approve(review_id, reviewer, org_id):
        review = ArchitectureReview.query.filter_by(id=review_id, organization_id=org_id).first()
        if review:
            review.decision = 'approved'
            review.status = 'completed'
            review.reviewer = reviewer
            review.reviewed_at = datetime.datetime.utcnow()
            db.session.commit()
            return review
        return None

    @staticmethod
    def reject(review_id, reviewer, org_id):
        review = ArchitectureReview.query.filter_by(id=review_id, organization_id=org_id).first()
        if review:
            review.decision = 'rejected'
            review.status = 'completed'
            review.reviewer = reviewer
            review.reviewed_at = datetime.datetime.utcnow()
            db.session.commit()
            return review
        return None

    @staticmethod
    def review_summary(org_id):
        reviews = ArchitectureReview.query.filter_by(organization_id=org_id).all()
        approved = sum(1 for r in reviews if r.decision == 'approved')
        rejected = sum(1 for r in reviews if r.decision == 'rejected')

        return {
            "total_reviews": len(reviews),
            "approved_count": approved,
            "rejected_count": rejected
        }
