"""
EvidenceService - Phase 31 Cyber Platform Control Plane.
Stores compliance and operational evidence references, validating integrity using SHA-256.
"""
from app.extensions import db
from app.models.evidence_record import EvidenceRecord
import hashlib
import json
import re
import datetime


class EvidenceService:
    @staticmethod
    def calculate_integrity_hash(source_module: str, resource_type: str, resource_id: str, summary: str) -> str:
        """Canonicalize metadata and calculate integrity SHA-256 hash."""
        data = {
            'source_module': source_module,
            'resource_type': resource_type,
            'resource_id': str(resource_id),
            'summary': summary
        }
        canonical = json.dumps(data, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()

    @staticmethod
    def redact_secrets(text: str) -> str:
        """Redact tokens, credentials, API keys, passwords, and CTF flags."""
        text = re.sub(r'password\s*=\s*\S+', 'password=[REDACTED]', text, flags=re.IGNORECASE)
        text = re.sub(r'Bearer\s+\S+', 'Bearer [REDACTED]', text, flags=re.IGNORECASE)
        text = re.sub(r'token\s*=\s*\S+', 'token=[REDACTED]', text, flags=re.IGNORECASE)
        text = re.sub(r'api[-_]key\s*=\s*\S+', 'api_key=[REDACTED]', text, flags=re.IGNORECASE)
        text = re.sub(r'flag\{[^}]*\}', 'flag=[REDACTED]', text, flags=re.IGNORECASE)
        text = re.sub(r'ctf\{[^}]*\}', 'flag=[REDACTED]', text, flags=re.IGNORECASE)
        return text

    @staticmethod
    def collect(evidence_type: str, source_module: str, resource_type: str, resource_id: str, summary: str, org_id: int) -> EvidenceRecord:
        """Collect compliance metadata and calculate stable hash."""
        redacted = EvidenceService.redact_secrets(summary)
        h = EvidenceService.calculate_integrity_hash(source_module, resource_type, resource_id, redacted)
        rec = EvidenceRecord(
            evidence_type=evidence_type,
            source_module=source_module,
            resource_type=resource_type,
            resource_id=str(resource_id),
            summary=redacted,
            integrity_hash=h,
            collected_at=datetime.datetime.utcnow(),
            status='valid',
            organization_id=org_id
        )
        db.session.add(rec)
        db.session.commit()
        return rec

    @staticmethod
    def verify_integrity(evidence_id: int, org_id: int) -> bool:
        """Verify hash validity to verify file has not been tampered with."""
        rec = db.session.get(EvidenceRecord, evidence_id)
        if not rec or rec.organization_id != org_id:
            return False
        expected = EvidenceService.calculate_integrity_hash(
            rec.source_module, rec.resource_type, rec.resource_id, rec.summary
        )
        return rec.integrity_hash == expected

    @staticmethod
    def search(org_id: int, source_module: str = None) -> list:
        """Search evidence records."""
        query = EvidenceRecord.query.filter_by(organization_id=org_id)
        if source_module:
            query = query.filter_by(source_module=source_module)
        return query.all()

    @staticmethod
    def export_manifest(org_id: int) -> dict:
        """Export full catalog summary manifest of compliance hashes."""
        records = EvidenceRecord.query.filter_by(organization_id=org_id).all()
        manifest_items = []
        for r in records:
            manifest_items.append({
                'id': r.id,
                'type': r.evidence_type,
                'source': r.source_module,
                'hash': r.integrity_hash,
                'integrity': 'valid' if EvidenceService.verify_integrity(r.id, org_id) else 'compromised'
            })
        return {
            'exported_at': datetime.datetime.utcnow().isoformat(),
            'total_items': len(manifest_items),
            'manifest': manifest_items
        }
