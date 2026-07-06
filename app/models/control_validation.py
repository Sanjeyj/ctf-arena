"""
ControlValidation model - Phase 32 Cyber Trust, Assurance & Verification Fabric.
Stores simulated control validation runs.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class ControlValidation(db.Model, TimestampMixin, TenantMixin):
    """ControlValidation model."""
    __tablename__ = 'control_validations'

    id = db.Column(db.Integer, primary_key=True)
    control_reference = db.Column(db.String(120), nullable=False, index=True)  # NIST-800-53 reference, etc.
    validation_type = db.Column(db.String(64), nullable=False)  # automated, manual, peer_review
    expected_result = db.Column(db.String(120), nullable=False)
    actual_result = db.Column(db.String(120), nullable=False)
    effectiveness_score = db.Column(db.Float, default=1.0, nullable=False)  # 0.0 to 1.0
    status = db.Column(db.String(64), default='passed', nullable=False)  # passed, partially_effective, failed, not_tested
    tested_at = db.Column(db.DateTime, nullable=False, index=True)
    evidence_record_id = db.Column(db.Integer, db.ForeignKey('evidence_records.id', ondelete='SET NULL'), nullable=True)

    def __repr__(self):
        return f'<ControlValidation ref={self.control_reference!r} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'control_reference': self.control_reference,
            'validation_type': self.validation_type,
            'expected_result': self.expected_result,
            'actual_result': self.actual_result,
            'effectiveness_score': self.effectiveness_score,
            'status': self.status,
            'tested_at': self.tested_at.isoformat() if self.tested_at else None,
            'evidence_record_id': self.evidence_record_id,
            'organization_id': self.organization_id,
        }
