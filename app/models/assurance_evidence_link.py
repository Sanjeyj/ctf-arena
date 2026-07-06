"""
AssuranceEvidenceLink model - Phase 32 Cyber Trust, Assurance & Verification Fabric.
Links EvidenceRecords to assurance claims.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class AssuranceEvidenceLink(db.Model, TimestampMixin, TenantMixin):
    """AssuranceEvidenceLink model."""
    __tablename__ = 'assurance_evidence_links'

    id = db.Column(db.Integer, primary_key=True)
    assurance_case_id = db.Column(db.Integer, db.ForeignKey('assurance_cases.id', ondelete='CASCADE'), nullable=False, index=True)
    evidence_record_id = db.Column(db.Integer, db.ForeignKey('evidence_records.id', ondelete='CASCADE'), nullable=False, index=True)
    relationship_type = db.Column(db.String(64), default='supports', nullable=False)  # supports, contradicts, contextual, compensating_control
    weight = db.Column(db.Float, default=1.0, nullable=False)  # 0.0 to 1.0
    validation_status = db.Column(db.String(64), default='pending', nullable=False)  # pending, valid, invalid

    def __repr__(self):
        return f'<AssuranceEvidenceLink case={self.assurance_case_id} evidence={self.evidence_record_id} type={self.relationship_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'assurance_case_id': self.assurance_case_id,
            'evidence_record_id': self.evidence_record_id,
            'relationship_type': self.relationship_type,
            'weight': self.weight,
            'validation_status': self.validation_status,
            'organization_id': self.organization_id,
        }
