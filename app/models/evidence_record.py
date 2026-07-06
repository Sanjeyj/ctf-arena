"""
EvidenceRecord model - Phase 31 Cyber Platform Control Plane.
Stores compliance and operational evidence references.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class EvidenceRecord(db.Model, TimestampMixin, TenantMixin):
    """EvidenceRecord model."""
    __tablename__ = 'evidence_records'

    id = db.Column(db.Integer, primary_key=True)
    evidence_type = db.Column(db.String(64), nullable=False)  # soc_alert, wargame_run, policy_check, feature_change
    source_module = db.Column(db.String(64), nullable=False)
    resource_type = db.Column(db.String(64), nullable=False)
    resource_id = db.Column(db.String(64), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    integrity_hash = db.Column(db.String(64), nullable=False)
    collected_at = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.String(32), default='valid', nullable=False)  # valid, tampered

    def __repr__(self):
        return f'<EvidenceRecord type={self.evidence_type} status={self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'evidence_type': self.evidence_type,
            'source_module': self.source_module,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'summary': self.summary,
            'integrity_hash': self.integrity_hash,
            'collected_at': self.collected_at.isoformat() if self.collected_at else None,
            'status': self.status,
            'organization_id': self.organization_id,
        }
