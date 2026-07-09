"""Phase 40 — Platform Certification Run Model."""
import datetime
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class PlatformCertificationRun(db.Model, TimestampMixin, TenantMixin):
    """Record of a platform certification audit run."""
    __tablename__ = 'platform_certification_runs'

    CERT_TYPES = (
        'release_candidate', 'security_baseline', 'architecture_baseline',
        'tenant_isolation', 'ai_safety', 'migration_integrity', 'full_platform',
    )
    STATUS_CHOICES = ('pending', 'running', 'completed', 'failed', 'cancelled')

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    certification_type = db.Column(db.String(60), nullable=False, default='full_platform', index=True)
    baseline_test_count = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(30), nullable=False, default='pending', index=True)
    overall_score = db.Column(db.Float, nullable=True)
    security_score = db.Column(db.Float, nullable=True)
    reliability_score = db.Column(db.Float, nullable=True)
    tenant_isolation_score = db.Column(db.Float, nullable=True)
    ai_safety_score = db.Column(db.Float, nullable=True)
    offline_safety_score = db.Column(db.Float, nullable=True)
    migration_integrity_score = db.Column(db.Float, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    summary = db.Column(db.Text, nullable=True)

    # Relationships
    checks = db.relationship(
        'CertificationCheck',
        backref='run',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'certification_type': self.certification_type,
            'baseline_test_count': self.baseline_test_count,
            'status': self.status,
            'overall_score': round(float(self.overall_score), 4) if self.overall_score is not None else None,
            'security_score': round(float(self.security_score), 4) if self.security_score is not None else None,
            'reliability_score': round(float(self.reliability_score), 4) if self.reliability_score is not None else None,
            'tenant_isolation_score': round(float(self.tenant_isolation_score), 4) if self.tenant_isolation_score is not None else None,
            'ai_safety_score': round(float(self.ai_safety_score), 4) if self.ai_safety_score is not None else None,
            'offline_safety_score': round(float(self.offline_safety_score), 4) if self.offline_safety_score is not None else None,
            'migration_integrity_score': round(float(self.migration_integrity_score), 4) if self.migration_integrity_score is not None else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'summary': self.summary,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
