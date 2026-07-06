"""
SoftwareAttestation model - Phase 32 Cyber Trust, Assurance & Verification Fabric.
Stores supply chain attestations.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, TenantMixin


class SoftwareAttestation(db.Model, TimestampMixin, TenantMixin):
    """SoftwareAttestation model."""
    __tablename__ = 'software_attestations'

    id = db.Column(db.Integer, primary_key=True)
    artifact_name = db.Column(db.String(120), nullable=False)
    artifact_version = db.Column(db.String(64), nullable=False)
    artifact_digest = db.Column(db.String(120), nullable=False, index=True)  # SHA-256 hash representation
    builder_identity = db.Column(db.String(120), nullable=True)
    build_environment = db.Column(db.String(120), nullable=True)
    attestation_type = db.Column(db.String(64), default='in-toto', nullable=False)
    verification_status = db.Column(db.String(64), default='valid', nullable=False)  # valid, invalid
    metadata_json = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<SoftwareAttestation artifact={self.artifact_name!r} status={self.verification_status}>'

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
            'artifact_digest': self.artifact_digest,
            'builder_identity': self.builder_identity,
            'build_environment': self.build_environment,
            'attestation_type': self.attestation_type,
            'verification_status': self.verification_status,
            'metadata': meta,
            'organization_id': self.organization_id,
        }
