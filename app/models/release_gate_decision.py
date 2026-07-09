"""Phase 40 — Release Gate Decision Model."""
import datetime
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class ReleaseGateDecision(db.Model, TimestampMixin, TenantMixin):
    """Individual gate decision within a release approval pipeline.

    Final release approval NEVER happens automatically.
    Human approval is mandatory via approved_by field.
    """
    __tablename__ = 'release_gate_decisions'

    GATE_TYPES = (
        'test_gate', 'security_gate', 'tenant_isolation_gate',
        'ai_safety_gate', 'migration_gate', 'documentation_gate',
        'numeric_correctness_gate', 'route_audit_gate',
    )
    DECISION_CHOICES = ('pending', 'pass', 'conditional_pass', 'fail')

    id = db.Column(db.Integer, primary_key=True)
    release_baseline_id = db.Column(
        db.Integer,
        db.ForeignKey('release_baselines.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    gate_type = db.Column(db.String(60), nullable=False, index=True)
    required_score = db.Column(db.Float, nullable=False, default=80.0)
    actual_score = db.Column(db.Float, nullable=False, default=0.0)
    decision = db.Column(db.String(30), nullable=False, default='pending', index=True)
    reason = db.Column(db.Text, nullable=True)
    approved_by = db.Column(db.String(120), nullable=True)   # Human approval required
    decided_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'release_baseline_id': self.release_baseline_id,
            'gate_type': self.gate_type,
            'required_score': round(float(self.required_score), 4),
            'actual_score': round(float(self.actual_score), 4),
            'decision': self.decision,
            'reason': self.reason,
            'approved_by': self.approved_by,
            'decided_at': self.decided_at.isoformat() if self.decided_at else None,
            'organization_id': self.organization_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
