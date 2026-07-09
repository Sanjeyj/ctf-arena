"""
DetectionValidation model - Phase 35 Continuous Security Validation.
Models detection rules effectiveness (Sigma, YARA, IOC matches).
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class DetectionValidation(db.Model, TimestampMixin, TenantMixin):
    """DetectionValidation representation."""
    __tablename__ = 'detection_validations'

    id = db.Column(db.Integer, primary_key=True)
    execution_id = db.Column(db.Integer, db.ForeignKey('validation_executions.id', ondelete='CASCADE'), nullable=False)
    detection_type = db.Column(db.String(64), nullable=False)  # sigma, yara_metadata, ioc_match, anomaly_rule, correlation_rule
    detection_reference = db.Column(db.String(120), nullable=False)
    synthetic_signal_type = db.Column(db.String(64), nullable=False)
    expected_detection = db.Column(db.Boolean, default=True, nullable=False)
    detected = db.Column(db.Boolean, default=False, nullable=False)
    confidence = db.Column(db.Float, default=1.0, nullable=False)
    latency_score = db.Column(db.Float, default=1.0, nullable=False)  # 0.0 to 1.0 (inverse delay index)
    coverage_score = db.Column(db.Float, default=1.0, nullable=False)  # 0.0 to 1.0

    execution = db.relationship('ValidationExecution', backref=db.backref('detection_validations', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<DetectionValidation ref={self.detection_reference!r} detected={self.detected}>'

    def to_dict(self):
        return {
            'id': self.id,
            'execution_id': self.execution_id,
            'detection_type': self.detection_type,
            'detection_reference': self.detection_reference,
            'synthetic_signal_type': self.synthetic_signal_type,
            'expected_detection': self.expected_detection,
            'detected': self.detected,
            'confidence': self.confidence,
            'latency_score': self.latency_score,
            'coverage_score': self.coverage_score,
            'organization_id': self.organization_id
        }
