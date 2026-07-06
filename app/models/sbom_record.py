"""
SBOMRecord model - Phase 32 Cyber Trust, Assurance & Verification Fabric.
Stores Software Bill of Materials registry metrics.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class SBOMRecord(db.Model, TimestampMixin, TenantMixin):
    """SBOMRecord model."""
    __tablename__ = 'sbom_records'

    id = db.Column(db.Integer, primary_key=True)
    artifact_name = db.Column(db.String(120), nullable=False)
    artifact_version = db.Column(db.String(64), nullable=False)
    format_type = db.Column(db.String(64), default='CycloneDX', nullable=False)  # SPDX, CycloneDX, internal
    component_count = db.Column(db.Integer, default=0, nullable=False)
    dependency_count = db.Column(db.Integer, default=0, nullable=False)
    known_risk_count = db.Column(db.Integer, default=0, nullable=False)
    document_hash = db.Column(db.String(120), nullable=False, index=True)
    metadata_json = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<SBOMRecord artifact={self.artifact_name!r} format={self.format_type}>'

    def to_dict(self):
        import json
        meta = {}
        if self.metadata_json:
            try:
                meta = json.loads(self.metadata_json)
            except Exception:
                pass
        return {
            'id': self.id,
            'artifact_name': self.artifact_name,
            'artifact_version': self.artifact_version,
            'format_type': self.format_type,
            'component_count': self.component_count,
            'dependency_count': self.dependency_count,
            'known_risk_count': self.known_risk_count,
            'document_hash': self.document_hash,
            'metadata': meta,
            'organization_id': self.organization_id,
        }
