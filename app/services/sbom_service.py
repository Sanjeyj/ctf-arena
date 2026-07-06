"""
SBOMService - Phase 32 Cyber Trust, Assurance & Verification Fabric.
Stores simulated software bill-of-materials and parses component/dependency properties offline.
"""
from app.extensions import db
from app.models.sbom_record import SBOMRecord
import json


class SBOMService:
    @staticmethod
    def register(artifact_name: str, artifact_version: str, format_type: str, document_hash: str, org_id: int, metadata: dict = None) -> SBOMRecord:
        """Register software bill of materials document entry."""
        meta_str = json.dumps(metadata) if metadata else None
        components = len(metadata.get('components', [])) if (metadata and 'components' in metadata) else 0
        deps = len(metadata.get('dependencies', [])) if (metadata and 'dependencies' in metadata) else 0
        risks = metadata.get('risk_count', 0) if metadata else 0

        sbom = SBOMRecord(
            artifact_name=artifact_name,
            artifact_version=artifact_version,
            format_type=format_type,
            component_count=components,
            dependency_count=deps,
            known_risk_count=risks,
            document_hash=document_hash,
            metadata_json=meta_str,
            organization_id=org_id
        )
        db.session.add(sbom)
        db.session.commit()
        return sbom

    @staticmethod
    def validate_metadata(sbom_id: int, org_id: int) -> bool:
        """Validate document parameters and format key tags offline."""
        sbom = db.session.get(SBOMRecord, sbom_id)
        if not sbom or sbom.organization_id != org_id:
            return False
        
        # Check standard layout
        if sbom.format_type not in ['SPDX', 'CycloneDX', 'internal']:
            return False
        if not sbom.metadata_json:
            return False
        return True

    @staticmethod
    def calculate_risk_summary(sbom_id: int, org_id: int) -> dict:
        """Evaluate static supply chain vulnerabilities index."""
        sbom = db.session.get(SBOMRecord, sbom_id)
        if not sbom or sbom.organization_id != org_id:
            return {}
        
        risk_level = 'low'
        if sbom.known_risk_count > 5:
            risk_level = 'critical'
        elif sbom.known_risk_count > 2:
            risk_level = 'high'
        elif sbom.known_risk_count > 0:
            risk_level = 'medium'

        return {
            'known_risks': sbom.known_risk_count,
            'risk_level': risk_level,
            'criticality_score': round(sbom.known_risk_count * 15.0, 2)
        }

    @staticmethod
    def compare_versions(artifact_name: str, org_id: int) -> list:
        """List registered versions of a specific software package."""
        records = SBOMRecord.query.filter_by(artifact_name=artifact_name, organization_id=org_id).order_by(SBOMRecord.artifact_version.desc()).all()
        return [r.to_dict() for r in records]

    @staticmethod
    def export_summary(sbom_id: int, org_id: int) -> dict:
        """Export static JSON SBOM summaries."""
        sbom = db.session.get(SBOMRecord, sbom_id)
        if not sbom or sbom.organization_id != org_id:
            return {}
        return {
            'artifact': sbom.artifact_name,
            'version': sbom.artifact_version,
            'components': sbom.component_count,
            'dependencies': sbom.dependency_count,
            'risk_level': sbom.known_risk_count
        }
