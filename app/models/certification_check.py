"""Phase 40 — Certification Check Model."""
import datetime
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class CertificationCheck(db.Model, TimestampMixin, TenantMixin):
    """Individual check item within a platform certification run."""
    __tablename__ = 'certification_checks'

    STATUS_CHOICES = ('passed', 'warning', 'failed', 'not_applicable')
    CATEGORY_CHOICES = (
        'security', 'tenant_isolation', 'ai_safety', 'offline_safety',
        'migration_integrity', 'numeric_correctness', 'route_ownership',
        'documentation', 'human_approval', 'simulation_safety',
    )

    id = db.Column(db.Integer, primary_key=True)
    certification_run_id = db.Column(
        db.Integer,
        db.ForeignKey('platform_certification_runs.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    check_category = db.Column(db.String(60), nullable=False, index=True)
    check_name = db.Column(db.String(200), nullable=False)
    expected_result = db.Column(db.String(200), nullable=True)
    actual_result = db.Column(db.String(200), nullable=True)
    score = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(30), nullable=False, default='passed', index=True)
    evidence_reference = db.Column(db.String(500), nullable=True)
    details = db.Column(db.Text, nullable=True)
    checked_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'certification_run_id': self.certification_run_id,
            'check_category': self.check_category,
            'check_name': self.check_name,
            'expected_result': self.expected_result,
            'actual_result': self.actual_result,
            'score': round(float(self.score), 4) if self.score is not None else None,
            'status': self.status,
            'evidence_reference': self.evidence_reference,
            'details': self.details,
            'checked_at': self.checked_at.isoformat() if self.checked_at else None,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
