"""Phase 40 — Release Baseline Model."""
import datetime
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class ReleaseBaseline(db.Model, TimestampMixin, TenantMixin):
    """Immutable snapshot of platform state at a release decision point."""
    __tablename__ = 'release_baselines'

    STATUS_CHOICES = ('draft', 'reviewing', 'approved', 'released_simulation', 'superseded')

    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(30), nullable=False)
    codename = db.Column(db.String(100), nullable=True)
    migration_revision = db.Column(db.String(40), nullable=False)
    test_count = db.Column(db.Integer, nullable=False, default=0)
    warning_count = db.Column(db.Integer, nullable=False, default=0)
    model_count = db.Column(db.Integer, nullable=False, default=0)
    service_count = db.Column(db.Integer, nullable=False, default=0)
    route_count = db.Column(db.Integer, nullable=False, default=0)
    template_count = db.Column(db.Integer, nullable=False, default=0)
    documentation_count = db.Column(db.Integer, nullable=False, default=0)
    baseline_hash = db.Column(db.String(64), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, default='draft', index=True)
    approved_by = db.Column(db.String(120), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Human approval required — never set automatically
    __table_args__ = (
        db.UniqueConstraint('version', 'organization_id', name='uq_release_baseline_version_org'),
    )

    # Gate decisions
    gate_decisions = db.relationship(
        'ReleaseGateDecision',
        backref='baseline',
        lazy='dynamic',
        cascade='all, delete-orphan',
    )

    def to_dict(self):
        return {
            'id': self.id,
            'version': self.version,
            'codename': self.codename,
            'migration_revision': self.migration_revision,
            'test_count': self.test_count,
            'warning_count': self.warning_count,
            'model_count': self.model_count,
            'service_count': self.service_count,
            'route_count': self.route_count,
            'template_count': self.template_count,
            'documentation_count': self.documentation_count,
            'baseline_hash': self.baseline_hash,
            'status': self.status,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'notes': self.notes,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
